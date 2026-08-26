"""
Product catalog + dealer listing + price comparison/Scam Shield endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.models.product import ProductStatus
from app.schemas.price import PriceComparisonResponse, ReferencePriceCreateRequest, ReferencePriceResponse, ScamShieldStatusResponse
from app.schemas.product import (
    DealerProductCreateRequest,
    DealerProductListResponse,
    DealerProductResponse,
    DealerProductUpdateRequest,
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
)
from app.services import dealer_product_service, price_query_service, product_service

router = APIRouter(tags=["products"])


@router.get("/products", response_model=ProductListResponse)
def list_products(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    """Only APPROVED products are ever returned here - see product_service."""
    return product_service.list_approved_products(db, query=q, limit=limit, offset=offset)


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    payload: ProductCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProductResponse:
    return product_service.create_product(db, current_user.user_id, payload)


@router.get("/products/admin", response_model=ProductListResponse)
def list_products_admin(
    status_filter: ProductStatus | None = Query(default=ProductStatus.PENDING_REVIEW, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    """Wires up product_service.list_all_products_admin (already existed,
    just never had a route) - defaults to PENDING_REVIEW so an admin
    lands on 'what needs my attention' first; any other real status
    ('approved', 'rejected', 'suspended', 'recalled') can be requested
    explicitly via ?status=. Declared before /products/{product_id} so
    'admin' is never swallowed by that path param route."""
    return product_service.list_all_products_admin(db, status=status_filter, limit=limit, offset=offset)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value, Role.ADMIN.value, Role.DEALER.value, Role.TRADER.value)),
    db: Session = Depends(get_db),
) -> ProductResponse:
    return product_service.get_product(db, product_id)


@router.post("/products/{product_id}/approve", response_model=ProductResponse)
def approve_product(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProductResponse:
    return product_service.approve_product(db, current_user.user_id, product_id)


@router.post("/products/{product_id}/reject", response_model=ProductResponse)
def reject_product(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProductResponse:
    return product_service.reject_product(db, current_user.user_id, product_id)


@router.post("/products/{product_id}/suspend", response_model=ProductResponse)
def suspend_product(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProductResponse:
    return product_service.suspend_product(db, current_user.user_id, product_id)


@router.get("/products/{product_id}/prices", response_model=ReferencePriceResponse)
def get_latest_reference_price(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
):
    from app.core import error_codes
    from app.core.errors import AppError
    from app.repositories import product_repository

    ref = product_repository.get_latest_reference_price(db, product_id)
    if ref is None:
        raise AppError(error_codes.NOT_FOUND, "Reference price unavailable.", 404)
    return ReferencePriceResponse.model_validate(ref)


@router.get("/products/{product_id}/price-history")
def get_reference_price_history(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> list[ReferencePriceResponse]:
    from app.repositories import product_repository

    history = product_repository.list_reference_price_history(db, product_id)
    return [ReferencePriceResponse.model_validate(r) for r in history]


@router.post("/products/{product_id}/reference-prices", response_model=ReferencePriceResponse, status_code=201)
def add_reference_price(
    product_id: uuid.UUID,
    payload: ReferencePriceCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
):
    from app.models.reference_price import ReferencePrice
    from app.repositories import product_repository

    ref = ReferencePrice(
        product_id=product_id, price=payload.price, source_type=payload.source_type,
        source_name=payload.source_name, region=payload.region, effective_date=payload.effective_date,
    )
    product_repository.create_reference_price(db, ref)
    db.commit()
    db.refresh(ref)
    return ReferencePriceResponse.model_validate(ref)


@router.get("/products/{product_id}/compare", response_model=PriceComparisonResponse)
def compare_product_prices(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PriceComparisonResponse:
    return price_query_service.compare_offers_for_product(db, product_id, settings)


@router.get("/dealer-products/{dealer_product_id}/scam-shield", response_model=ScamShieldStatusResponse)
def get_scam_shield_status(
    dealer_product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ScamShieldStatusResponse:
    return price_query_service.get_scam_shield_status(db, dealer_product_id, settings)


@router.post("/dealer-products", response_model=DealerProductResponse, status_code=201)
def create_dealer_listing(
    payload: DealerProductCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.DEALER.value, Role.TRADER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DealerProductResponse:
    return dealer_product_service.create_listing(db, current_user.user_id, payload, settings)


@router.put("/dealer-products/{listing_id}", response_model=DealerProductResponse)
def update_dealer_listing(
    listing_id: uuid.UUID,
    payload: DealerProductUpdateRequest,
    current_user: CurrentUser = Depends(require_role(Role.DEALER.value, Role.TRADER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DealerProductResponse:
    return dealer_product_service.update_listing(db, current_user.user_id, listing_id, payload, settings)


@router.get("/dealer-products/me", response_model=DealerProductListResponse)
def list_my_dealer_listings(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.DEALER.value, Role.TRADER.value)),
    db: Session = Depends(get_db),
) -> DealerProductListResponse:
    return dealer_product_service.list_my_listings(db, current_user.user_id, limit=limit, offset=offset)


@router.get("/seeds", response_model=ProductListResponse)
def list_seeds(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    """Seeds are just Products with category=SEED - reuses the entire
    existing product catalog/approval system (Prompt 9), no duplicate
    seed-specific catalog. Only APPROVED seed products are ever returned,
    same as any other product category."""
    from app.models.product import ProductCategory

    return product_service.list_approved_products(db, query=q, category=ProductCategory.SEED, limit=limit, offset=offset)


@router.get("/seeds/{product_id}", response_model=ProductResponse)
def get_seed(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> ProductResponse:
    from app.core import error_codes
    from app.core.errors import AppError
    from app.models.product import ProductCategory

    product = product_service.get_product(db, product_id)
    if product.category != ProductCategory.SEED:
        raise AppError(error_codes.NOT_FOUND, "Seed product not found.", 404)
    return product
