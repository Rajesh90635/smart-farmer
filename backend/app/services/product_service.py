"""
Product catalog: admin-curated master list, mirroring the same
create-then-approve pattern as ProfessionalProfile verification (Prompt
8) - a product always starts PENDING_REVIEW and only an explicit admin
approval action moves it to APPROVED. Dealers can only ever list an
APPROVED product (enforced in dealer_product_service).
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.product import Product, ProductStatus
from app.repositories import product_repository
from app.schemas.product import ProductCreateRequest, ProductListResponse, ProductResponse
from app.services.audit_logger import AuditLogger


def create_product(db: Session, admin_user_id: str, payload: ProductCreateRequest) -> ProductResponse:
    product = Product(
        name=payload.name,
        category=payload.category,
        manufacturer=payload.manufacturer,
        active_ingredients=payload.active_ingredients,
        pack_size_value=payload.pack_size_value,
        pack_size_unit=payload.pack_size_unit,
        description=payload.description,
        usage_information=payload.usage_information,
        regulatory_info=payload.regulatory_info,
        status=ProductStatus.PENDING_REVIEW,
    )
    product_repository.create_product(db, product)
    db.flush()

    AuditLogger(db).log("PRODUCT_CREATED", actor_id=admin_user_id, actor_role="admin", entity="product", entity_id=str(product.id))
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


def approve_product(db: Session, admin_user_id: str, product_id: uuid.UUID) -> ProductResponse:
    product = product_repository.get_product(db, product_id)
    if product is None:
        raise AppError(error_codes.NOT_FOUND, "Product not found.", 404)

    product.status = ProductStatus.APPROVED
    AuditLogger(db).log("PRODUCT_APPROVED", actor_id=admin_user_id, actor_role="admin", entity="product", entity_id=str(product.id))
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


def reject_product(db: Session, admin_user_id: str, product_id: uuid.UUID) -> ProductResponse:
    product = product_repository.get_product(db, product_id)
    if product is None:
        raise AppError(error_codes.NOT_FOUND, "Product not found.", 404)

    product.status = ProductStatus.REJECTED
    AuditLogger(db).log("PRODUCT_REJECTED", actor_id=admin_user_id, actor_role="admin", entity="product", entity_id=str(product.id))
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


def suspend_product(db: Session, admin_user_id: str, product_id: uuid.UUID) -> ProductResponse:
    product = product_repository.get_product(db, product_id)
    if product is None:
        raise AppError(error_codes.NOT_FOUND, "Product not found.", 404)

    product.status = ProductStatus.SUSPENDED
    AuditLogger(db).log("PRODUCT_SUSPENDED", actor_id=admin_user_id, actor_role="admin", entity="product", entity_id=str(product.id))
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


def get_product(db: Session, product_id: uuid.UUID) -> ProductResponse:
    product = product_repository.get_product(db, product_id)
    if product is None:
        raise AppError(error_codes.NOT_FOUND, "Product not found.", 404)
    return ProductResponse.model_validate(product)


def list_approved_products(db: Session, *, query: str | None = None, category=None, limit: int = 50, offset: int = 0) -> ProductListResponse:
    items, total = product_repository.list_products(db, status=ProductStatus.APPROVED, query=query, category=category, limit=limit, offset=offset)
    return ProductListResponse(items=[ProductResponse.model_validate(p) for p in items], total=total)


def list_all_products_admin(db: Session, *, status: ProductStatus | None = None, query: str | None = None, limit: int = 50, offset: int = 0) -> ProductListResponse:
    items, total = product_repository.list_products(db, status=status, query=query, limit=limit, offset=offset)
    return ProductListResponse(items=[ProductResponse.model_validate(p) for p in items], total=total)
