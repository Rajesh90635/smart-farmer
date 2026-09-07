"""Missing Backlog Batch 8 (group 5): crop_photos.damage_record_id

Revision ID: cd0584254c03
Revises: 39a9e48c0858
Create Date: 2026-09-08 15:00:00.000000

D74-03: optional link from a CropPhoto to the CropDamageRecord (D74-02,
already VERIFIED) it is evidence for. Reuses the existing photo-capture
pipeline entirely - no second upload mechanism for insurance. Additive,
nullable, ON DELETE SET NULL (a deleted damage record never cascades
into deleting the photo evidence itself).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd0584254c03'
down_revision: Union[str, None] = '39a9e48c0858'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('crop_photos', sa.Column('damage_record_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_crop_photos_damage_record_id', 'crop_photos', 'crop_damage_records', ['damage_record_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index(op.f('ix_crop_photos_damage_record_id'), 'crop_photos', ['damage_record_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_crop_photos_damage_record_id'), table_name='crop_photos')
    op.drop_constraint('fk_crop_photos_damage_record_id', 'crop_photos', type_='foreignkey')
    op.drop_column('crop_photos', 'damage_record_id')
