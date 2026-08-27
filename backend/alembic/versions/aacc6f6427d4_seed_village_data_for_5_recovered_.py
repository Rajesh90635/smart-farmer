"""seed village data for 5 mandals recovered by fixing the matcher

Revision ID: aacc6f6427d4
Revises: 3d61e7bd3ba9
Create Date: 2026-08-27 01:00:00.000000

Small follow-up to 3d61e7bd3ba9. While explaining that migration's 54
disclosed village-less mandals to the user, re-checking each one surfaced
a real bug in the *mandal*-name matcher (not the village-name cleaner,
which already handled this correctly): it stripped ALL parenthetical
text when normalizing a mandal name for fuzzy matching, including
meaningful ASCII qualifiers - not just the Telugu-script parenthetical it
was meant to remove. That silently turned official "Kakinada (Rural)"
and "Kakinada ( Urban )" into indistinguishable "Kakinada", so neither
could match this table's real "Kakinada Rural"/"Kakinada Urban" rows,
which were then wrongly bucketed with the genuine Rural/Urban-split gaps
that the official source actually can't resolve.

Re-running the fuzzy match with the bug fixed (ASCII qualifier groups
preserved, only non-ASCII/Telugu groups stripped, mirroring the village-
name cleaner) against all 54 previously-unmatched mandals recovered
exactly 5 real matches - the rest remain genuinely unmatched for the
reasons already disclosed in 3d61e7bd3ba9 (structural Rural/Urban/East/
West splits the official source doesn't have, stale Visakhapatnam data,
names too different to safely auto-match). One near-miss - official
"Machilipatnam" fuzzy-matching BOTH this table's "Machilipatnam North"
and "Machilipatnam South" - was deliberately excluded even though it
scored under the distance threshold: that's the same unresolvable
structural-split problem as Guntur East/West, not a real recovery, and
was caught by manual review rather than trusted from the distance score
alone.

    Kakinada / Kakinada Rural  <- official "Kakinada (Rural)"    (exact)
    Kakinada / Kakinada Urban  <- official "Kakinada ( Urban )"  (exact)
    Chittoor / Gudupalle       <- official "Gudi Palle"          (spelling variant)
    Nandyal  / Miduthuru       <- official "Midthur"             (spelling variant)
    Nandyal  / Sirivella       <- official "Sirvel"              (spelling variant)

102 real village rows, same source/cleaning/title-casing convention as
3d61e7bd3ba9 (revenue villages from codes.ap.gov.in's own API), with two
further small cleaning fixes applied here and disclosed rather than
silently carried over: a stray trailing comma in the source's own
"Thimmapuram," was stripped, and the title-caser now also splits on "."
so no-space abbreviations like "S.Atchutapuram" title-case each piece
correctly (previously would have produced "S.atchutapuram"). This second
fix is NOT retroactively applied to 3d61e7bd3ba9's already-committed
15,886 rows - a spot check found ~211 existing village names with the
same no-space-abbreviation pattern (e.g. "R.t.puram" instead of
"R.T.Puram") - purely cosmetic casing, not a data-correctness issue,
flagged to the user as a separate decision rather than bundled into this
migration silently.

Idempotent by design (ON CONFLICT ON CONSTRAINT uq_village_mandal_name
DO NOTHING), same pattern as every prior seeding migration in this
project.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aacc6f6427d4'
down_revision: Union[str, None] = '3d61e7bd3ba9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_VILLAGES_BY_DISTRICT_MANDAL = {
    ("Kakinada", "Kakinada Rural"): [
        "Chidiga", "Chidiga (CT)", "Ganganapalle", "Ganganapalli", "Indrapalem", "Kovvada",
        "Kovvuru", "Nemam", "Panduru", "Penumarthi", "Ramanayyapeta", "Repuru",
        "S.Atchutapuram", "Sarpavaram", "Suryaraopeta (Part)", "Thammavaram", "Thimmapuram",
        "Toorangi (R)", "Turangi", "Vakalapudi", "Vakalapudi (OG)",
    ],
    ("Kakinada", "Kakinada Urban"): [
        "Kakinada", "Medalinu", "Ramanaiahpeta", "Suryaraopeta",
    ],
    ("Chittoor", "Gudupalle"): [
        "Agaram", "Alugumanipalle", "Anagarlapalle", "Anganamalakothur", "Athinatham",
        "Avulathimmanpalle", "Beggilipalle", "Bijiganipalle", "Bisanatham", "Boyanapalle",
        "Burugulapalle", "Cheekatipalle", "Chinnagollapalle", "Chinnaparthikunta",
        "Dasimanipalle", "Dinnepalle", "Gokarlapalle", "Gudupalle", "Gundlasagaram",
        "Irisiganipalle", "Jarugukonda", "Kakinayanichigurlapa", "Kanamanapalle",
        "Kodiganipalle", "Kotachembagiri", "Kotamakanepalle", "Kotapalle", "Kuppiganipalle",
        "Lingapuram Dinne", "Malavanikothur", "Maldepalle", "Nakkanapalle", "Nalagampalle",
        "Onnapanayanikothur", "Ontipalle", "Peddagollapalle", "Peddaparthikunta",
        "Pogurupalle", "Sanganapalle", "Settipalle", "Settipalle @ K.Bandarlapalle",
        "Sirigiripalle", "Sodiganipalle", "Sonnarsanapalle", "Thalai Agraharam",
        "Thimmanayanipalle", "Vengepalle", "Yamaganipalle",
    ],
    ("Nandyal", "Miduthuru"): [
        "Alaganur", "Bannur", "Byrapuram", "Cherakucherla", "Chintalapalle", "Chowtakur",
        "Devanur", "Jalakanur", "Kadumur", "Masapeta", "Midthur", "Nagalooty", "Rollapadu",
        "Sunkesula", "Talamudipi", "Thimmapuram", "Veepanagandla",
    ],
    ("Nandyal", "Sirivella"): [
        "Boyalakuntla", "Chennur", "Gangavaram", "Govindpalle", "Gumparamandinne",
        "Jeenepalle", "Kaminenipalle", "Kotapadu", "Mahadevapuram", "Sirvel", "Vanikemdinne",
        "Yerraguntla",
    ],
}


def _flatten():
    district_names, mandal_names, village_names = [], [], []
    for (district, mandal), villages in _VILLAGES_BY_DISTRICT_MANDAL.items():
        for village in villages:
            district_names.append(district)
            mandal_names.append(mandal)
            village_names.append(village)
    return district_names, mandal_names, village_names


def upgrade() -> None:
    district_names, mandal_names, village_names = _flatten()
    op.execute(
        sa.text(
            """
            INSERT INTO villages (mandal_id, name)
            SELECT m.id, v.village_name
            FROM unnest(:district_names, :mandal_names, :village_names)
                AS v(district_name, mandal_name, village_name)
            JOIN districts d ON d.name = v.district_name
            JOIN mandals m ON m.district_id = d.id AND m.name = v.mandal_name
            ON CONFLICT ON CONSTRAINT uq_village_mandal_name DO NOTHING
            """
        ).bindparams(
            sa.bindparam("district_names", value=district_names, type_=sa.ARRAY(sa.String)),
            sa.bindparam("mandal_names", value=mandal_names, type_=sa.ARRAY(sa.String)),
            sa.bindparam("village_names", value=village_names, type_=sa.ARRAY(sa.String)),
        )
    )


def downgrade() -> None:
    district_names, mandal_names, village_names = _flatten()
    op.execute(
        sa.text(
            """
            DELETE FROM villages
            WHERE (mandal_id, name) IN (
                SELECT m.id, v.village_name
                FROM unnest(:district_names, :mandal_names, :village_names)
                    AS v(district_name, mandal_name, village_name)
                JOIN districts d ON d.name = v.district_name
                JOIN mandals m ON m.district_id = d.id AND m.name = v.mandal_name
            )
            """
        ).bindparams(
            sa.bindparam("district_names", value=district_names, type_=sa.ARRAY(sa.String)),
            sa.bindparam("mandal_names", value=mandal_names, type_=sa.ARRAY(sa.String)),
            sa.bindparam("village_names", value=village_names, type_=sa.ARRAY(sa.String)),
        )
    )
