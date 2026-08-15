"""
Authorized tools: each function takes ONLY the authenticated farmer_id
(never any id parsed from the farmer's free-text message) and returns a
small structured dict - never a raw ORM object, never a full database
row. There is no farmer_id/order_id/crop_id "sent by the model" at all in
this architecture (the deterministic router never extracts entity ids
from text) - every tool call operates on "the calling farmer's own
most-relevant record," resolved entirely server-side from the
authenticated session.

Every tool is a thin wrapper reusing an EXISTING repository/service from
a prior phase - no new business logic, no new database writes.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.ai_analysis import AIAnalysis
from app.models.crop_cycle import CropCycle, CultivationStatus
from app.models.crop_health_case import CropHealthCase
from app.models.crop_master import CropMaster
from app.models.farm import Farm
from app.models.harvest_record import HarvestRecord
from app.models.plot import Plot
from app.repositories import case_repository, harvest_repository, order_repository, product_repository, sale_order_repository
from app.services.ai.confidence import classify_confidence
from app.services.weather.weather_provider import WeatherProvider

_ACTIVE_STATUSES = tuple(s for s in CultivationStatus if s not in (CultivationStatus.HARVESTED, CultivationStatus.CANCELLED))


def get_crop_status(db: Session, farmer_id: str) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    row = db.execute(
        select(CropCycle, CropMaster.name, Farm.farm_name)
        .join(CropMaster, CropCycle.crop_id == CropMaster.id)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .join(Farm, Plot.farm_id == Farm.id)
        .where(Farm.farmer_id == farmer_uuid, CropCycle.cultivation_status.in_(_ACTIVE_STATUSES))
        .order_by(CropCycle.updated_at.desc())
        .limit(1)
    ).first()

    if row is None:
        return {"available": False, "source": "Farmer crop record"}

    cycle, crop_name, farm_name = row
    return {
        "available": True,
        "source": "Farmer crop record",
        "crop_name": crop_name,
        "farm_name": farm_name,
        "stage": cycle.cultivation_status.value,
        "sowing_date": cycle.sowing_date.isoformat() if cycle.sowing_date else None,
        "expected_harvest_date": cycle.expected_harvest_date.isoformat() if cycle.expected_harvest_date else None,
    }


def get_disease_status(db: Session, farmer_id: str, settings: Settings) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    analysis = db.execute(
        select(AIAnalysis).where(AIAnalysis.farmer_id == farmer_uuid).order_by(AIAnalysis.created_at.desc()).limit(1)
    ).scalar_one_or_none()

    if analysis is None:
        return {"available": False, "source": "AI disease detection"}

    confidence_level = classify_confidence(analysis.confidence, settings).value if analysis.confidence is not None else None
    return {
        "available": True,
        "source": "AI disease detection (Prompt 6)",
        "result_status": analysis.result_status.value,
        "predicted_class": analysis.predicted_class,
        "confidence_level": confidence_level,
        "requires_review": analysis.requires_review,
        "model_name": analysis.model_name,
        "model_version": analysis.model_version,
    }


def get_weather_status(db: Session, farmer_id: str, provider: WeatherProvider, settings: Settings) -> dict:
    from app.services import weather_service

    farmer_uuid = uuid.UUID(farmer_id)
    farm = db.execute(
        select(Farm).where(Farm.farmer_id == farmer_uuid, Farm.latitude.is_not(None)).order_by(Farm.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    if farm is None:
        return {"available": False, "source": "Weather service"}

    result = weather_service.get_farm_weather(db, farmer_id, farm.id, provider, settings)
    return {
        "available": result.available,
        "source": "Weather service (Prompt 7)",
        "is_stale": result.is_stale,
        "current_temperature_c": result.current.temperature_c if result.current else None,
        "rain_probability_today_percent": result.forecast[0].reading.rain_probability_percent if result.forecast else None,
        "unavailable_reason": result.unavailable_reason,
    }


def get_harvest_status(db: Session, farmer_id: str) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    harvest = db.execute(
        select(HarvestRecord).where(HarvestRecord.farmer_id == farmer_uuid).order_by(HarvestRecord.updated_at.desc()).limit(1)
    ).scalar_one_or_none()
    if harvest is None:
        return {"available": False, "source": "Harvest record"}
    return {
        "available": True,
        "source": "Harvest record (Prompt 10)",
        "status": harvest.status.value,
        "expected_harvest_date": harvest.expected_harvest_date.isoformat() if harvest.expected_harvest_date else None,
        "estimated_quantity": str(harvest.estimated_quantity) if harvest.estimated_quantity else None,
        "unit": harvest.unit,
    }


def get_buyer_offers(db: Session, farmer_id: str) -> dict:
    from app.repositories import buyer_offer_repository

    farmer_uuid = uuid.UUID(farmer_id)
    listings, _ = harvest_repository.list_listings_for_farmer(db, farmer_uuid, limit=1, offset=0)
    if not listings:
        return {"available": False, "source": "Marketplace offers"}

    offers = buyer_offer_repository.list_active_offers_for_listing(db, listings[0].id)
    return {
        "available": True,
        "source": "Marketplace offers (Prompt 10)",
        "listing_crop_quantity": str(listings[0].quantity_available),
        "listing_unit": listings[0].unit,
        "offer_count": len(offers),
        "offers": [{"price_per_unit": str(o.price_per_unit), "quantity": str(o.quantity)} for o in offers[:5]],
    }


def get_my_sales(db: Session, farmer_id: str) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    sales, total = sale_order_repository.list_sales_for_farmer(db, farmer_uuid, limit=5, offset=0)
    return {
        "available": total > 0,
        "source": "Sale records (Prompt 10)",
        "total_sales": total,
        "recent_sales": [{"status": s.status.value, "quantity": str(s.quantity), "unit": s.unit, "net_value": str(s.net_value)} for s in sales],
    }


def get_my_orders(db: Session, farmer_id: str) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    orders, total = order_repository.list_orders_for_farmer(db, farmer_uuid, limit=1, offset=0)
    if not orders:
        return {"available": False, "source": "Order records"}
    order = orders[0]
    return {
        "available": True,
        "source": "Order records (Prompt 9)",
        "status": order.status.value,
        "final_amount": str(order.final_amount) if order.final_amount else None,
    }


def get_delivery_status(db: Session, farmer_id: str) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    orders, total = order_repository.list_orders_for_farmer(db, farmer_uuid, limit=1, offset=0)
    if not orders:
        return {"available": False, "source": "Delivery records"}
    delivery = order_repository.get_delivery_for_order(db, orders[0].id)
    if delivery is None:
        return {"available": False, "source": "Delivery records"}
    return {
        "available": True,
        "source": "Delivery records (Prompt 9)",
        "status": delivery.status.value,
        "estimated_delivery_date": delivery.estimated_delivery_date.isoformat() if delivery.estimated_delivery_date else None,
    }


def get_expert_case_status(db: Session, farmer_id: str) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    case = db.execute(
        select(CropHealthCase).where(CropHealthCase.farmer_id == farmer_uuid).order_by(CropHealthCase.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    if case is None:
        return {"available": False, "source": "Expert case record"}

    reviews = case_repository.list_reviews_for_case(db, case.id)
    latest_review = reviews[-1] if reviews else None
    return {
        "available": True,
        "source": "Expert case record (Prompt 8)",
        "status": case.status.value,
        "final_verified_class": case.final_verified_class,
        "review_outcome": latest_review.outcome if latest_review else None,
        "review_notes": latest_review.notes if latest_review else None,
    }


def get_seed_products(db: Session, *, query: str | None = None) -> dict:
    from app.models.product import ProductCategory, ProductStatus

    items, total = product_repository.list_products(db, status=ProductStatus.APPROVED, query=query, category=ProductCategory.SEED, limit=5, offset=0)
    return {
        "available": len(items) > 0,
        "source": "Product catalog (Prompt 9)",
        "products": [{"name": p.name, "pack_size": f"{p.pack_size_value}{p.pack_size_unit}"} for p in items],
    }
