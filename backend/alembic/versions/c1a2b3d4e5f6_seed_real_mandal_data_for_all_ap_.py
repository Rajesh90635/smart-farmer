"""seed real mandal data for all AP districts

Revision ID: c1a2b3d4e5f6
Revises: 8bf7b0c379d4
Create Date: 2026-08-24 00:00:00.000000

REAL DATA, sourced live from each Andhra Pradesh district's own dedicated
Wikipedia article (infobox mandal count cross-checked against the listed
mandals for each), not from training-data recall - explicitly replacing
the prior migration's disclosed "unverified sample" for Guntur, and
filling in the remaining 25 districts that previously had zero mandal
rows. This does NOT touch villages - no authoritative village-level
dataset was available or attempted, per the same no-fabrication rule.

IMPORTANT - a real district-boundary complication, disclosed rather than
silently resolved:

Andhra Pradesh's district boundaries changed again on 2025-12-31 (a real,
dated event independently confirmed across multiple districts' own
Wikipedia articles - not a scraping artifact): two new districts were
carved out (Polavaram, from Alluri Sitharama Raju's Rampachodavaram
division; Markapuram, from Prakasam), and Punganur/Koduru/the Rajampeta
mandals/Gudur-Kota-Chillakur were reassigned between
Chittoor/Annamayya/Tirupati/YSR Kadapa/SPSR Nellore. This project's own
`districts` table (migration 8813e01a2a4a) only has the 26 districts from
the original April-2022 reorganization, predating that Dec-2025 change.

Per explicit user decision, this migration seeds mandals against the
EXISTING 26-district structure using PRE-Dec-2025 boundaries - i.e.
Markapuram's 21 mandals are filed under "Prakasam", Polavaram's 12 under
"Alluri Sitharama Raju", and the five reshuffled mandals/divisions are
filed under their pre-2025 parent district - rather than adding
Markapuram/Polavaram as new district rows. This avoids touching the
already-shipped, already-tested Phase 41 State/District dropdown and
Farm.district_id data. If the districts table is ever updated to the
current 28-district structure, these specific mandals will need to move
with it.

Two further, smaller disclosed uncertainties (each source's own infobox
count disagreed with its own listed-mandal count by exactly one, and the
source didn't say which name was extra/missing - all listed names are
included rather than arbitrarily dropping one):
- Prakasam: infobox said 27, 28 names listed.
- Nandyal: infobox said 29, 30 names listed.
- Anantapur: infobox said 31, 32 names listed.

And one geographic inference, not confirmed by a direct source citation:
Markapuram's own Wikipedia article names Prakasam only as an adjacent
district, not explicitly as its carve-out parent - treated as Prakasam's
child per near-certain geography (every Markapuram mandal - Giddalur,
Kanigiri, Podili, Cumbum, Yerragondapalem, etc. - is historically and
unambiguously part of Prakasam), consistent with this project's existing
disclosed-inference convention (e.g. the OCR confidence thresholds, the
Nominatim GPS-matching heuristic).

Idempotent by design (ON CONFLICT ON CONSTRAINT uq_mandal_district_name
DO NOTHING), matching the exact pattern already established by
8bf7b0c379d4 - safe to re-run, and safe to layer real village data on top
of later without creating duplicates.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, None] = '8bf7b0c379d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_MANDALS_BY_DISTRICT = {
    "Srikakulam": [
        "Ichchapuram", "Kaviti", "Sompeta", "Kanchili", "Palasa", "Mandasa",
        "Vajrapukotturu", "Srikakulam", "Gara", "Amadalavalasa", "Ponduru",
        "Sarubujjili", "Burja", "Narasannapeta", "Polaki", "Etcherla",
        "Laveru", "Ranastalam", "Ganguvarisigadam", "Jalumuru", "Tekkali",
        "Santha Bommali", "Kotabommali", "Pathapatnam", "Meliaputti",
        "Nandigama", "Saravakota", "Kothuru", "Hiramandalam",
        "Lakshminarasupeta",
    ],
    "Parvathipuram Manyam": [
        "Jiyyammavalasa", "Gummalakshmipuram", "Kurupam", "Palakonda",
        "Seethampeta", "Bhamini", "Veeraghattam", "Parvathipuram",
        "Seethanagaram", "Balijipeta", "Salur", "Pachipenta", "Makkuva",
        "Komarada", "Garugubilli",
    ],
    "Vizianagaram": [
        "Bobbili", "Ramabhadrapuram", "Badangi", "Therlam",
        "Gajapathinagaram", "Dattirajeru", "Mentada", "Cheepurupalli",
        "Garividi", "Gurla", "Merakamudidam", "Vangara",
        "Regidi Amadalavalasa", "Santhakavati", "Rajam",
        "Vizianagaram Urban", "Gantyada", "Poosapatirega", "Denkada",
        "Bhogapuram", "Srungavarapukota", "Jami", "Vepada",
        "Lakkavarapukota", "Kothavalasa", "Bondapalli", "Nellimarla",
        "Vizianagaram Rural",
    ],
    "Visakhapatnam": [
        "Bheemunipatnam", "Anandapuram", "Padmanabham",
        "Visakhapatnam Rural", "Seethammadhara", "Gajuwaka",
        "Pedagantyada", "Gopalapatnam", "Mulagada", "Maharanipeta",
        "Pendurthi",
    ],
    "Anakapalli": [
        "Atchutapuram", "Elamanchili", "Kotauratla", "Nakkapalli",
        "Payakaraopeta", "Rambilli", "S. Rayavaram", "Anakapalli",
        "Butchayyapeta", "Cheedikada", "Chodavaram", "Devarapalli",
        "K. Kotapadu", "Kasimkota", "Munagapaka", "Paravada", "Sabbavaram",
        "Golugonda", "Madugula", "Makavarapalem", "Narsipatnam",
        "Nathavaram", "Ravikamatham", "Rolugunta",
    ],
    # 11 Paderu-division mandals (current ASR) + 12 Rampachodavaram-division
    # mandals (spun off as "Polavaram district" on 2025-12-31; filed here
    # under their pre-split parent per the explicit scope decision above).
    "Alluri Sitharama Raju": [
        "Ananthagiri", "Araku Valley", "Chinthapalli", "Dumbriguda",
        "Ganagaraju Madugula", "Gudem Kotha Veedhi", "Hukumpeta", "Koyyuru",
        "Munchingiputtu", "Paderu", "Pedabayalu",
        "Chintur", "Kunavaram", "Etapaka", "Vararamachandrapuram",
        "Maredumilli", "Rampachodavaram", "Devipatnam", "Y. Ramavaram",
        "Gangavaram", "Addateegala", "Rajavommangi", "Gurthedu",
    ],
    "Kakinada": [
        "Gollaprolu", "Kajuluru", "Kakinada Rural", "Kakinada Urban",
        "Karapa", "Pedapudi", "Pithapuram", "Thallarevu", "Thondangi",
        "U. Kothapalli", "Gandepalle", "Jaggampeta", "Kirlampudi",
        "Kotananduru", "Peddapuram", "Prathipadu", "Rowthulapudi",
        "Samalkota", "Sankhavaram", "Tuni", "Yeleswaram",
    ],
    "East Godavari": [
        "Chagallu", "Devarapalle", "Gopalapuram", "Kovvur", "Nallajerla",
        "Nidadavolu", "Peravali", "Tallapudi", "Undrajavaram", "Anaparthi",
        "Biccavolu", "Gokavaram", "Kadiam", "Kapileswarapuram", "Korukonda",
        "Mandapeta", "Rajamahendravaram Rural", "Rajamahendravaram Urban",
        "Rajanagaram", "Rangampeta", "Rayavaram", "Seethanagaram",
    ],
    "Konaseema": [
        "Allavaram", "Amalapuram", "I. Polavaram", "Katrenikona",
        "Malikipuram", "Mamidikuduru", "Mummidivaram", "Razole",
        "Sakhinetipalle", "Uppalaguptam", "Ainavilli", "Alumuru",
        "Ambajipeta", "Atreyapuram", "Kothapeta", "P. Gannavaram",
        "Ravulapalem", "K. Gangavaram", "Ramachandrapuram",
    ],
    "West Godavari": [
        "Akiveedu", "Bhimavaram", "Ganapavaram", "Kalla", "Palakoderu",
        "Undi", "Veeravasaram", "Achanta", "Mogalthur", "Narasapuram",
        "Palakollu", "Penugonda", "Penumantra", "Poduru", "Yelamanchili",
        "Attili", "Iragavaram", "Pentapadu", "Tadepalligudem", "Tanuku",
    ],
    "Eluru": [
        "Bhimadole", "Denduluru", "Eluru", "Kaikalur", "Kalidindi",
        "Mandavalli", "Mudinepalli", "Nidamarru", "Pedapadu", "Pedavegi",
        "Unguturu", "Buttayagudem", "Dwaraka Tirumala", "Jangareddygudem",
        "Jeelugu Milli", "Kamavarapukota", "Koyyalagudem", "Kukunuru",
        "Polavaram", "T. Narasapuram", "Velairpadu", "Agiripalli",
        "Chatrai", "Chintalapudi", "Lingapalem", "Musunuru", "Nuzvid",
    ],
    "Krishna": [
        "Bapulapadu", "Gannavaram", "Gudivada", "Gudlavalleru", "Nandivada",
        "Pedaparupudi", "Unguturu", "Avanigadda", "Bantumilli",
        "Challapalli", "Ghantasala", "Guduru", "Koduru", "Kruthivennu",
        "Machilipatnam North", "Machilipatnam South", "Mopidevi",
        "Nagayalanka", "Pedana", "Kankipadu", "Movva", "Pamarru",
        "Pamidimukkala", "Penamaluru", "Thotlavalluru", "Vuyyuru",
    ],
    "NTR": [
        "Chandarlapadu", "Jaggayyapeta", "Kanchikacherla", "Nandigama",
        "Penuganchiprolu", "Vatsavai", "Veerullapadu", "A. Konduru",
        "Gampalagudem", "Reddigudem", "Tiruvuru", "Vissannapeta",
        "G. Konduru", "Ibrahimpatnam", "Mylavaram", "Vijayawada Rural",
        "Vijayawada Central", "Vijayawada North", "Vijayawada East",
        "Vijayawada West",
    ],
    "Guntur": [
        "Guntur East", "Guntur West", "Medikonduru", "Pedakakani",
        "Pedanandipadu", "Phirangipuram", "Prathipadu", "Tadikonda",
        "Thullur", "Vatticherukuru", "Chebrolu", "Duggirala", "Kakumanu",
        "Kollipara", "Mangalagiri", "Ponnur", "Tadepalle", "Tenali",
    ],
    "Palnadu": [
        "Dachepalle", "Durgi", "Gurazala", "Karempudi", "Machavaram",
        "Macherla", "Piduguralla", "Rentachintala", "Veldurthi",
        "Bollapalle", "Chilakaluripet", "Edlapadu", "Ipur", "Nadendla",
        "Narasaraopet", "Nuzendla", "Rompicherla", "Savalyapuram",
        "Vinukonda", "Amaravathi", "Atchampet", "Bellamkonda", "Krosuru",
        "Muppalla", "Nekarikallu", "Pedakurapadu", "Rajupalem",
        "Sattenapalli",
    ],
    "Bapatla": [
        "Bapatla", "Karlapalem", "Martur", "Parchur", "Pittalavanipalem",
        "Yeddanapudi", "Chinaganjam", "Chirala", "Inkollu", "Karamchedu",
        "Vetapalem", "Amruthalur", "Bhattiprolu", "Cherukupalle", "Kollur",
        "Nagaram", "Nizampatnam", "Repalle", "Tsunduru", "Vemuru",
    ],
    # Current Prakasam (28 names; infobox itself says 27, unresolved by
    # source - see module docstring) + Markapuram's 21 mandals (carved out
    # 2025-12-31; filed here under its pre-split parent).
    "Prakasam": [
        "Addanki", "Ballikurava", "Darsi", "Donakonda", "J. Panguluru",
        "Korisapadu", "Kurichedu", "Mundlamuru", "Santhamaguluru",
        "Thallur", "Gudluru", "Kandukur", "Lingasamudram", "Marripudi",
        "Ponnaluru", "Ulavapadu", "Voletivaripalem", "Chimakurthy",
        "Kondapi", "Kothapatnam", "Maddipadu", "Naguluppalapadu",
        "Ongole Rural", "Ongole Urban", "Santhanuthalapadu",
        "Singarayakonda", "Tanguturu", "Zarugumalli",
        "Chandrasekharapuram", "Hanumanthunipadu", "Kanigiri", "Pamuru",
        "Pedacherlopalle", "Veligandla", "Ardhaveedu", "Bestavaripeta",
        "Cumbum", "Dornala", "Giddalur", "Komarolu", "Konakanamitla",
        "Markapuram", "Pedda Araveedu", "Podili", "Pullalacheruvu",
        "Racherla", "Tarlupadu", "Tripuranthakam", "Yerragondapalem",
    ],
    # Current list minus Gudur/Kota/Chillakur, which belonged to Tirupati
    # pre-2025 (moved to Nellore on 2025-12-31 - filed under Tirupati here).
    "SPSR Nellore": [
        "Ananthasagaram", "Anumasamudrampeta", "Atmakur", "Chejerla",
        "Kaluvoya", "Marripadu", "Sangam", "Seetharamapuram", "Udayagiri",
        "Allur", "Bogole", "Dagadarthi", "Duttalur", "Jaladanki",
        "Kaligiri", "Kavali", "Kodavalur", "Kondapuram", "Varikuntapadu",
        "Vidavalur", "Vinjamur", "Buchireddypalem", "Indukurpet", "Kovur",
        "Manubolu", "Muthukur", "Nellore rural", "Nellore urban",
        "Podalakur", "Rapur", "Sydapuram", "Thotapalli Gudur",
        "Venkatachalam",
    ],
    "Kurnool": [
        "Adoni Urban", "Adoni Rural", "Gonegandla", "Holagunda", "Kosigi",
        "Kowthalam", "Mantralayam", "Nandavaram", "Pedda kadabur",
        "Yemmiganur", "C. Belagal", "Gudur", "Kallur", "Kodumur",
        "Kurnool Rural", "Kurnool Urban", "Orvakal", "Veldurthi", "Alur",
        "Aspari", "Chippagiri", "Devanakonda", "Halaharvi", "Krishnagiri",
        "Maddikera East", "Pattikonda", "Tuggali",
    ],
    # Infobox says 29, 30 names listed on the district's own page -
    # unresolved by source, all 30 included (see module docstring).
    "Nandyal": [
        "Atmakur", "Bandi Atmakur", "Jupadu Bunglow", "Kothapalle",
        "Miduthuru", "Nandikotkur", "Pagidyala", "Pamulapadu", "Srisailam",
        "Velugodu", "Banaganapalli", "Kolimigundla", "Koilkuntla", "Owk",
        "Sanjamala", "Bethamcherla", "Dhone", "Peapully", "Allagadda",
        "Chagalamarri", "Dornipadu", "Gadivemula", "Gospadu", "Mahanandi",
        "Nandyal Urban", "Nandyal Rural", "Panyam", "Rudravaram",
        "Sirivella", "Uyyalawada",
    ],
    # Infobox says 31, 32 names listed on the district's own page -
    # unresolved by source, all 32 included (see module docstring).
    "Anantapur": [
        "Anantapur Urban", "Anantapur Rural", "Atmakur",
        "Bukkaraya Samudram", "Garladinne", "Kudair", "Narpala",
        "Peddapappur", "Putlur", "Raptadu", "Singanamala", "Tadipatri",
        "Yellanur", "Gooty", "Guntakal", "Pamidi", "Peddavadugur",
        "Uravakonda", "Vajrakarur", "Vidapanakal", "Yadiki", "Beluguppa",
        "Bommanahal", "Brahmasamudram", "D.Hirehal", "Gummagatta",
        "Kalyandurg", "Kambadur", "Kanekal", "Kundurpi", "Rayadurgam",
        "Settur",
    ],
    "Sri Sathya Sai": [
        "Bathalapalle", "Chennekothapalle", "Dharmavaram", "Kanaganapalle",
        "Mudigubba", "Ramagiri", "Tadimarri", "Gandlapenta", "Kadiri",
        "Nallacheruvu", "Nambulapulakunta", "Talupula", "Tanakal", "Agali",
        "Amarapuram", "Gudibanda", "Madakasira", "Rolla", "Chilamathur",
        "Gorantla", "Hindupur", "Lepakshi", "Parigi", "Penukonda", "Roddam",
        "Somandepalle", "Amadagur", "Bukkapatnam", "Kothacheruvu",
        "Nallamada", "Obuladevaracheruvu", "Puttaparthi",
    ],
    # Current list minus the Rajampeta division, which belonged to
    # Annamayya pre-2025 (merged back into Kadapa on 2025-12-31 - filed
    # under Annamayya here).
    "YSR Kadapa": [
        "Atlur", "B. Kodur", "Badvel", "Brahmamgari Matam", "Chapadu",
        "Duvvur", "Gopavaram", "Kalasapadu", "Khajipeta", "Mydukur",
        "Porumamilla", "Sri Avadhutha Kasinayana", "Jammalamadugu",
        "Kondapuram", "Muddanur", "Mylavaram", "Peddamudium", "Proddatur",
        "Rajupalem", "Chennur", "Chinthakommadinne", "Kadapa",
        "Kamalapuram", "Pendlimarri", "Siddavatam", "Vallur", "Vontimitta",
        "Yerraguntla", "Chakarayapet", "Lingala", "Pulivendula",
        "Simhadripuram", "Thondur", "Veerapunayunipalle", "Vempalle",
        "Vemula",
    ],
    # Current list minus Punganur (belonged to Chittoor pre-2025), plus
    # Koduru and the Rajampeta division (both belonged to Annamayya
    # pre-2025; Koduru moved to Tirupati and Rajampeta merged back into
    # YSR Kadapa on 2025-12-31).
    "Annamayya": [
        "Beerangi Kothakota", "Chowdepalle", "Kurabalakota", "Madanapalle",
        "Mulakalacheruvu", "Nimmanapalle", "Peddamandyam",
        "Peddathippasamudram", "Ramasamudram", "Thamballapalle",
        "Gurramkonda", "Kalakada", "Kalikiri", "Kambhamvaripalle",
        "Pileru", "Sodam", "Somala", "Vayalpad", "Chinnamandyam",
        "Galiveedu", "Lakkireddipalli", "Ramapuram", "Rayachoti",
        "Sambepalli", "Koduru", "Nandalur", "Rajampeta", "Veeraballi",
        "T. Sundupalle",
    ],
    # Current list plus Punganur (belonged to Chittoor pre-2025; moved to
    # Annamayya on 2025-12-31).
    "Chittoor": [
        "Bangarupalyam", "Chittoor Rural", "Chittoor Urban",
        "Gangadhara Nellore", "Gudipala", "Irala", "Penumuru",
        "Pulicherla", "Puthalapattu", "Rompicherla", "Srirangarajapuram",
        "Thavanampalle", "Vedurukuppam", "Yadamari", "Gudupalle", "Kuppam",
        "Ramakuppam", "Santhipuram", "Karvetinagar", "Nagari", "Nindra",
        "Palasamudram", "Vijayapuram", "Baireddipalle", "Gangavaram",
        "Palamaner", "Peddapanjani", "Venkatagirikota", "Punganur",
    ],
    # Current list minus Koduru (moved from Annamayya on 2025-12-31, filed
    # under Annamayya above), plus Gudur/Kota/Chillakur (belonged to
    # Tirupati pre-2025; moved to Nellore on 2025-12-31).
    "Tirupati": [
        "Balayapalli", "Dakkili", "K.V.B. Puram", "Nagalapuram",
        "Narayanavanam", "Pichatur", "Renigunta", "Srikalahasti",
        "Thottambedu", "Venkatagiri", "Yerpedu", "Buchinaidu Kandriga",
        "Chittamur", "Doravarisatram", "Naidupeta", "Ozili", "Pellakur",
        "Satyavedu", "Sullurpeta", "Tada", "Vakadu", "Varadaiahpalem",
        "Chandragiri", "Chinnagottigallu", "Chitvel", "Obulavaripalle",
        "Pakala", "Penagalur", "Pullampeta", "Puttur", "Ramachandrapuram",
        "Tirupati Rural", "Tirupati Urban", "Vadamalapeta",
        "Yerravaripalem", "Gudur", "Kota", "Chillakur",
    ],
}


# Already inserted by 8bf7b0c379d4 (a subset of this migration's own
# Guntur list, per ON CONFLICT DO NOTHING) - excluded from downgrade so
# that reverting only this migration doesn't also erase rows owned by the
# prior one.
_ALREADY_SEEDED_BY_PRIOR_MIGRATION = {
    ("Guntur", "Guntur East"), ("Guntur", "Guntur West"),
    ("Guntur", "Pedakakani"), ("Guntur", "Mangalagiri"),
    ("Guntur", "Tadepalle"), ("Guntur", "Tadikonda"),
    ("Guntur", "Chebrolu"), ("Guntur", "Duggirala"),
    ("Guntur", "Prathipadu"),
}


def _flatten(exclude_already_seeded=False):
    district_names = []
    mandal_names = []
    for district, mandals in _MANDALS_BY_DISTRICT.items():
        for mandal in mandals:
            if exclude_already_seeded and (district, mandal) in _ALREADY_SEEDED_BY_PRIOR_MIGRATION:
                continue
            district_names.append(district)
            mandal_names.append(mandal)
    return district_names, mandal_names


def upgrade() -> None:
    district_names, mandal_names = _flatten()
    op.execute(
        sa.text(
            """
            INSERT INTO mandals (district_id, name)
            SELECT d.id, v.mandal_name
            FROM unnest(:district_names, :mandal_names) AS v(district_name, mandal_name)
            JOIN districts d ON d.name = v.district_name
            ON CONFLICT ON CONSTRAINT uq_mandal_district_name DO NOTHING
            """
        ).bindparams(
            sa.bindparam("district_names", value=district_names, type_=sa.ARRAY(sa.String)),
            sa.bindparam("mandal_names", value=mandal_names, type_=sa.ARRAY(sa.String)),
        )
    )


def downgrade() -> None:
    district_names, mandal_names = _flatten(exclude_already_seeded=True)
    op.execute(
        sa.text(
            """
            DELETE FROM mandals
            WHERE (district_id, name) IN (
                SELECT d.id, v.mandal_name
                FROM unnest(:district_names, :mandal_names) AS v(district_name, mandal_name)
                JOIN districts d ON d.name = v.district_name
            )
            """
        ).bindparams(
            sa.bindparam("district_names", value=district_names, type_=sa.ARRAY(sa.String)),
            sa.bindparam("mandal_names", value=mandal_names, type_=sa.ARRAY(sa.String)),
        )
    )
