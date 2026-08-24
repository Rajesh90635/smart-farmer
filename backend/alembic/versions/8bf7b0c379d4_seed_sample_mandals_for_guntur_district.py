"""seed sample mandals for guntur district

Revision ID: 8bf7b0c379d4
Revises: 90c85f85e7f8
Create Date: 2026-08-23 20:24:26.938842

SAMPLE DATA ONLY - explicitly requested by the user to exercise the
Mandal dropdown end-to-end before the real, complete mandal/village
dataset is supplied (see app/models/location.py's own docstring: Mandal
had zero rows anywhere in this project before this migration). These
nine names are recalled from general/training knowledge of mandals
immediately around Guntur city that are commonly understood to remain in
the post-2022 Andhra Pradesh district-reorganization "Guntur" district
(as opposed to the newly-carved Bapatla/Palnadu districts) - this was
NOT independently verified against a live authoritative source in this
sandbox (same disclosed-uncertainty convention already used elsewhere in
this project, e.g. package license checks). Treat as a working sample,
not confirmed reference data, until replaced/confirmed by the real
dataset.

Idempotent by design (ON CONFLICT DO NOTHING against the table's own
uq_mandal_district_name constraint) per explicit user instruction: safe
to re-run, and safe to layer the real dataset on top of later without
creating duplicates or erroring on rows that already exist.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bf7b0c379d4'
down_revision: Union[str, None] = '90c85f85e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SAMPLE_GUNTUR_MANDALS = [
    "Guntur East",
    "Guntur West",
    "Pedakakani",
    "Mangalagiri",
    "Tadepalle",
    "Tadikonda",
    "Chebrolu",
    "Duggirala",
    "Prathipadu",
]


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO mandals (district_id, name)
            SELECT d.id, m.name
            FROM (SELECT id FROM districts WHERE name = 'Guntur') AS d
            CROSS JOIN unnest(:names) AS m(name)
            ON CONFLICT ON CONSTRAINT uq_mandal_district_name DO NOTHING
            """
        ).bindparams(sa.bindparam("names", value=_SAMPLE_GUNTUR_MANDALS, type_=sa.ARRAY(sa.String)))
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM mandals
            WHERE district_id = (SELECT id FROM districts WHERE name = 'Guntur')
              AND name = ANY(:names)
            """
        ).bindparams(sa.bindparam("names", value=_SAMPLE_GUNTUR_MANDALS, type_=sa.ARRAY(sa.String)))
    )
