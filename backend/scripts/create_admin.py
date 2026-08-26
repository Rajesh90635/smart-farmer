"""
Creates an ADMIN-role user directly in the database.

There is deliberately no public /auth/register path to admin - registration
always creates a farmer (see auth_service.register). Admin accounts are
provisioned out-of-band, by whoever has direct database/server access, which
is exactly what running this script implies.

An admin User has no FarmerProfile (that table is farmer-only data) and
logs in through the same POST /api/v1/auth/login endpoint as any other
role - auth_service now resolves the JWT's role claim from the user's
actual assigned role instead of assuming farmer, so the token this admin
receives will correctly carry role=admin.

Usage (from backend/):
    python scripts/create_admin.py <phone_number> <password>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.phone_utils import normalize_phone_number
from app.core.roles import Role as RoleCode
from app.core.security_passwords import hash_password, is_strong_password
from app.db.session import SessionLocal
from app.models.user import AccountStatus, User
from app.repositories import user_repository


def create_admin(phone_number: str, password: str) -> None:
    canonical_phone = normalize_phone_number(phone_number)
    if not is_strong_password(password):
        raise SystemExit("Password must be at least 8 characters and contain a letter and a digit.")

    db = SessionLocal()
    try:
        if user_repository.get_by_phone(db, canonical_phone) is not None:
            raise SystemExit(f"An account with phone number {canonical_phone} already exists.")

        admin_role = user_repository.get_role_by_code(db, RoleCode.ADMIN.value)
        if admin_role is None:
            raise SystemExit("The 'admin' role is not seeded in this environment's database.")

        user = User(
            phone_number=canonical_phone,
            password_hash=hash_password(password),
            status=AccountStatus.ACTIVE,
        )
        db.add(user)
        db.flush()

        user_repository.assign_role(db, user.id, admin_role.id)
        db.commit()

        print(f"Admin account created: {canonical_phone} (user id {user.id})")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/create_admin.py <phone_number> <password>")
    create_admin(sys.argv[1], sys.argv[2])
