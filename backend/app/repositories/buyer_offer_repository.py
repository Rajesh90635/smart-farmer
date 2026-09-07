import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.buyer_business_profile import BuyerBusinessProfile
from app.models.buyer_offer import BuyerOffer, CounterOffer, OfferStatus


def create_buyer_business_profile(db: Session, profile: BuyerBusinessProfile) -> BuyerBusinessProfile:
    db.add(profile)
    return profile


def get_buyer_business_profile(db: Session, professional_id: uuid.UUID) -> BuyerBusinessProfile | None:
    return db.execute(select(BuyerBusinessProfile).where(BuyerBusinessProfile.professional_id == professional_id)).scalar_one_or_none()


def create_offer(db: Session, offer: BuyerOffer) -> BuyerOffer:
    db.add(offer)
    return offer


def get_offer_by_id(db: Session, offer_id: uuid.UUID) -> BuyerOffer | None:
    return db.get(BuyerOffer, offer_id)


def list_offers_for_listing(db: Session, listing_id: uuid.UUID) -> list[BuyerOffer]:
    return list(db.execute(select(BuyerOffer).where(BuyerOffer.harvest_listing_id == listing_id).order_by(BuyerOffer.created_at.desc())).scalars().all())


def list_offers_for_buyer(db: Session, buyer_id: uuid.UUID) -> list[BuyerOffer]:
    return list(db.execute(select(BuyerOffer).where(BuyerOffer.buyer_id == buyer_id).order_by(BuyerOffer.created_at.desc())).scalars().all())


def list_active_offers_for_listing(db: Session, listing_id: uuid.UUID) -> list[BuyerOffer]:
    return list(
        db.execute(select(BuyerOffer).where(BuyerOffer.harvest_listing_id == listing_id, BuyerOffer.status == OfferStatus.ACTIVE)).scalars().all()
    )


def create_counter_offer(db: Session, counter: CounterOffer) -> CounterOffer:
    db.add(counter)
    return counter


def list_counter_offers(db: Session, buyer_offer_id: uuid.UUID) -> list[CounterOffer]:
    # `sequence` (a real, monotonically-increasing IDENTITY column) is the
    # deterministic tiebreaker for two counters inserted within the same
    # created_at timestamp tick - see get_latest_counter_offer.
    return list(
        db.execute(
            select(CounterOffer).where(CounterOffer.buyer_offer_id == buyer_offer_id).order_by(CounterOffer.created_at.asc(), CounterOffer.sequence.asc())
        ).scalars().all()
    )


def get_latest_counter_offer(db: Session, buyer_offer_id: uuid.UUID) -> CounterOffer | None:
    # Ordering by created_at alone is not reliable - two counters can be inserted
    # within the same timestamp tick, and Postgres does not guarantee insertion
    # order for ties. `sequence` is a real, monotonically-increasing IDENTITY
    # column (unlike `id`, a random UUID4), so it is the deterministic tiebreaker.
    return db.execute(
        select(CounterOffer)
        .where(CounterOffer.buyer_offer_id == buyer_offer_id)
        .order_by(CounterOffer.created_at.desc(), CounterOffer.sequence.desc())
        .limit(1)
    ).scalar_one_or_none()
