from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.location import District, Mandal, State, Village


def list_states(db: Session) -> list[State]:
    return list(db.execute(select(State).order_by(State.name)).scalars().all())


def get_state(db: Session, state_id: int) -> State | None:
    return db.execute(select(State).where(State.id == state_id)).scalar_one_or_none()


def list_districts_for_state(db: Session, state_id: int) -> list[District]:
    return list(
        db.execute(select(District).where(District.state_id == state_id).order_by(District.name)).scalars().all()
    )


def get_district(db: Session, district_id: int) -> District | None:
    return db.execute(select(District).where(District.id == district_id)).scalar_one_or_none()


def list_mandals_for_district(db: Session, district_id: int) -> list[Mandal]:
    return list(
        db.execute(select(Mandal).where(Mandal.district_id == district_id).order_by(Mandal.name)).scalars().all()
    )


def get_mandal(db: Session, mandal_id: int) -> Mandal | None:
    return db.execute(select(Mandal).where(Mandal.id == mandal_id)).scalar_one_or_none()


def list_villages_for_mandal(db: Session, mandal_id: int) -> list[Village]:
    return list(
        db.execute(select(Village).where(Village.mandal_id == mandal_id).order_by(Village.name)).scalars().all()
    )


def get_village(db: Session, village_id: int) -> Village | None:
    return db.execute(select(Village).where(Village.id == village_id)).scalar_one_or_none()
