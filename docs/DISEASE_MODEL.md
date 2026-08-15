# Disease Model

## Data model

`DiseaseClass` (`app/models/disease_class.py`) — Crop → DiseaseClass →
DiseaseMetadata, per Requirement 6/7.

| Field | Notes |
|---|---|
| crop_id | FK → crop_master; unique with disease_name |
| disease_name | Required |
| local_names | JSONB `{language_code: name}` |
| scientific_name | Nullable |
| description, symptoms | Free text |
| severity | Free string, not an enum — no authoritative severity taxonomy exists yet (same reasoning as `Plot.soil_type`) |
| is_active | |
| disease_metadata | JSONB, unused this phase — extensibility hook |

**Deliberately excluded:** treatment/medicine fields. That's a separate
future module referencing `disease_id`, never a column here (Requirement 7's
explicit instruction).

## Seed data — illustrative, not authoritative

| Crop | Diseases seeded |
|---|---|
| Tomato | Healthy, Early Blight, Late Blight, Leaf Mold |
| Rice | Healthy, Bacterial Leaf Blight |

**These rows exist so the schema/API can be exercised end-to-end. They are
NOT tied to any working model** — no model in this project can currently
recognize any of them (see docs/AI_ARCHITECTURE.md: no model is
configured). Do not present these as "supported diseases" to a real
farmer until a real model's actual class list is verified and mapped here.

## Supported crops / supported diseases (as of this phase)

**Actual answer: none.** `NotConfiguredModelProvider.supported_crop_names()`
returns `[]`. The seed data above describes what the *schema* can
represent, not what any model can *recognize*. When a real model is
integrated, its `ModelProvider.supported_crop_names()` and the classes it
can actually output must be reconciled against this table — expanding
`disease_classes` to match exactly what the model supports, never claiming
support for a class the model wasn't trained on (Requirement 6's explicit
rule).

## Local names

Only a handful of Hindi names were seeded as examples
(`local_names: {"hi": "..."}`). Malayalam/Tamil/Telugu/Kannada/Marathi
names are not populated — same open item as the Farm/Plot/Crop phase's
crop-master seed data.

## Licensing

No disease taxonomy or symptom description was copied from a proprietary
source — the seeded descriptions are generic, widely-known agricultural
facts (e.g. "dark concentric-ring spots" is standard early-blight
terminology, not sourced from a specific copyrighted text). If a future
model's class list or metadata comes from a specific dataset (e.g.
PlantVillage), that dataset's license terms govern reproducing its
descriptions/symptom text verbatim — verify before copying, per
docs/AI_ARCHITECTURE.md's evaluation table.
