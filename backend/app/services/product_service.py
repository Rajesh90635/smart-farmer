"""
Product catalog: admin-curated master list, mirroring the same
create-then-approve pattern as ProfessionalProfile verification (Prompt
8) - a product always starts PENDING_REVIEW and only an explicit admin
approval action moves it to APPROVED. Dealers can only ever list an
APPROVED product (enforced in dealer_product_service).
"""
import uuid
from io import BytesIO

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.core.image_processing import process_image
from app.core.image_validation import validate_upload
from app.core.photo_storage_keys import build_leaf_filename, build_product_photo_container
from app.models.product import Product, ProductStatus
from app.repositories import product_repository
from app.schemas.product import ProductCreateRequest, ProductListResponse, ProductResponse
from app.services.audit_logger import AuditLogger
from app.services.storage.base import FileStorage

_EXT_BY_MIME = {"image/jpeg": "jpg", "image/png": "jpg", "image/webp": "jpg"}


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
        variety_id=payload.variety_id,
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


def upload_product_image(
    db: Session,
    admin_user_id: str,
    product_id: uuid.UUID,
    file_content: bytes,
    declared_mime_type: str,
    storage: FileStorage,
    settings: Settings,
) -> ProductResponse:
    """D26-02 (docs/audit/FINAL_CANONICAL_group_A.md): reuses the same
    validate_upload/process_image pipeline crop_photo_service.upload_photo
    already uses (re-encodes to JPEG, strips EXIF/GPS, enforces size
    limits) - no second image-handling implementation. Deliberately skips
    the farmer-photo-specific quality check (blur/lighting) and thumbnail
    generation - a product catalog photo isn't AI-analyzed and doesn't
    need the crop-photo module's own concerns."""
    product = product_repository.get_product(db, product_id)
    if product is None:
        raise AppError(error_codes.NOT_FOUND, "Product not found.", 404)

    validated = validate_upload(content=file_content, declared_mime_type=declared_mime_type, settings=settings)
    processed = process_image(validated.image, settings=settings)

    extension = _EXT_BY_MIME.get(declared_mime_type, "jpg")
    container = build_product_photo_container(product_id=product_id)
    storage_key = storage.save(container, build_leaf_filename(extension=extension), BytesIO(processed.content), "image/jpeg")

    product.image_storage_key = storage_key
    AuditLogger(db).log(
        "PRODUCT_IMAGE_UPLOADED", actor_id=admin_user_id, actor_role="admin", entity="product", entity_id=str(product.id)
    )
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


def get_product(db: Session, product_id: uuid.UUID) -> ProductResponse:
    product = product_repository.get_product(db, product_id)
    if product is None:
        raise AppError(error_codes.NOT_FOUND, "Product not found.", 404)
    return ProductResponse.model_validate(product)


def list_approved_products(
    db: Session,
    *,
    query: str | None = None,
    category=None,
    manufacturer: str | None = None,
    variety_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ProductListResponse:
    items, total = product_repository.list_products(
        db,
        status=ProductStatus.APPROVED,
        query=query,
        category=category,
        manufacturer=manufacturer,
        variety_id=variety_id,
        limit=limit,
        offset=offset,
    )
    return ProductListResponse(items=[ProductResponse.model_validate(p) for p in items], total=total)


def list_all_products_admin(db: Session, *, status: ProductStatus | None = None, query: str | None = None, limit: int = 50, offset: int = 0) -> ProductListResponse:
    items, total = product_repository.list_products(db, status=status, query=query, limit=limit, offset=offset)
    return ProductListResponse(items=[ProductResponse.model_validate(p) for p in items], total=total)
