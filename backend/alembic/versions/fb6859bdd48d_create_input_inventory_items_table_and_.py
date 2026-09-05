"""create input inventory items table and stock alert category

Revision ID: fb6859bdd48d
Revises: 0106c9d5f59f
Create Date: 2026-09-05 08:21:21.684817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb6859bdd48d'
down_revision: Union[str, None] = '0106c9d5f59f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # `category` is a plain string, not a shared native enum with
    # `products.category` - avoids touching that existing enum type.
    op.create_table(
        'input_inventory_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farmer_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('custom_name', sa.String(length=200), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('low_stock_threshold', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('low_stock_alerted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiry_alerted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['farmer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_input_inventory_items_farmer_id'), 'input_inventory_items', ['farmer_id'], unique=False)
    op.create_index(op.f('ix_input_inventory_items_category'), 'input_inventory_items', ['category'], unique=False)
    op.create_index(op.f('ix_input_inventory_items_expiry_date'), 'input_inventory_items', ['expiry_date'], unique=False)

    # Postgres requires ADD VALUE to run outside the value's own usage
    # transaction, but allows it inside its own migration transaction on
    # PG 12+ (this project runs PG 18) as long as the new value isn't
    # referenced in the SAME transaction - it isn't, here.
    op.execute("ALTER TYPE notification_category ADD VALUE IF NOT EXISTS 'stock_alert'")


def downgrade() -> None:
    op.drop_index(op.f('ix_input_inventory_items_expiry_date'), table_name='input_inventory_items')
    op.drop_index(op.f('ix_input_inventory_items_category'), table_name='input_inventory_items')
    op.drop_index(op.f('ix_input_inventory_items_farmer_id'), table_name='input_inventory_items')
    op.drop_table('input_inventory_items')
    # Postgres cannot drop a single enum value - downgrading leaves
    # 'stock_alert' in the notification_category type (harmless: an enum
    # value with no rows referencing it), consistent with this project's
    # existing note that "Enum types are not dropped by autogenerate."
