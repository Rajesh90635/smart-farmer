"""seed village data for 26 more mandals recovered via cross-district search

Revision ID: 0106c9d5f59f
Revises: f089b96621c7
Create Date: 2026-08-27 03:00:00.000000

Second recovery pass, requested directly by the user ("try to recover
more of the 49 unmatched mandals"). The first pass (`aacc6f6427d4`) only
searched each official mandal against candidates within the SAME
district AP CODES filed it under. Before attempting any further name-
distance tuning, two other avenues were checked first and are worth
recording:

1. **Tried and rejected**: whether the single official mandal behind
   each Rural/Urban/East/West/North/South structural split (Anantapur,
   Chittoor, Guntur, Kurnool, Nandyal, Ongole, Vizianagaram, Adoni,
   Machilipatnam) tags its own villages with a (Rural)/(Urban)/(R)/(U)
   qualifier that could be used to split them correctly between this
   table's two rows. Checked by fetching each one's real village list:
   the tags exist but are applied to only a handful of villages each
   (e.g. Anantapur's 21 villages: 3 tagged "(RURAL)", 1 "(Ct)", 17
   untagged) - nowhere near a clean, source-backed split of ALL
   villages. Assigning the untagged majority to either half would be a
   guess, not a fact - correctly left alone, unchanged from
   `3d61e7bd3ba9`'s original disclosed limitation for this category.

2. **Tried and it worked**: searching EVERY official mandal across ALL
   26 districts (not just its own) for a name-exact-or-near match to
   each of this table's remaining unmatched mandals. This surfaced a
   real, previously-undiscovered pattern: several of this table's
   mandals are filed by AP CODES under a DIFFERENT (usually adjacent)
   district than the one Wikipedia assigned them to in `c1a2b3d4e5f6`
   - e.g. this table's Annamayya/Chowdepalle is an exact-name match
   (distance 0) to AP CODES' own Chittoor/Chowdepalle record; East
   Godavari/Kapileswarapuram matches Konaseema's own record; nine of
   Prakasam's mandals (Addanki, Gudluru, Kandukur, Korisapadu,
   Lingasamudram, Santhamaguluru, Voletivaripalem, plus near-exact
   Ballikurava) match records AP CODES files under Bapatla or SPSR
   Nellore instead; four of Tirupati's match records filed under
   Annamayya. This is a genuine cross-source disagreement about which
   CURRENT district a handful of mandals belong to (unsurprising, given
   AP's district map has been redrawn multiple times since 2022) - NOT
   a reason to change this table's own `mandals.district_id` for any of
   them (that would be a separate, larger decision, out of scope here,
   and this table's existing district assignment for these mandals is
   left exactly as-is). The real-world village list under a given named
   mandal doesn't depend on which district bucket either source happens
   to file it under, so it was used as-is, with the source district
   disclosed per mandal in this file's own data comments below.

Beyond the cross-district search, four more were resolved by direct,
individually-verified pairing rather than blind distance-based fuzzy
matching (each confirmed via the matching Telugu name, not guessed):
YSR Kadapa/Siddavatam = official "Sidhout" (శిద్దవటం matches exactly);
YSR Kadapa/Sri Avadhutha Kasinayana = official "S.A.K.N. MANDAL" (an
acronym - శ్రీ అవధూత కాశినాయన is the same Telugu name spelled out);
Annamayya/Beerangi Kothakota = official "B Kothakota" ("B." abbreviates
"Beerangi", verified against the earlier known-uncertain source
disclosure in `c1a2b3d4e5f6`'s own docstring); East
Godavari/Rajamahendravaram Rural+Urban = official "Rajahmundry
Rural"/"Rajahmundry Urban" (Rajahmundry is Rajamahendravaram's old
English name, same real place); YSR Kadapa/Kadapa = official "Cuddapah"
(Cuddapah was renamed Kadapa in 2005, same real place). One same-district
recovery was also picked up that the first pass's threshold had missed:
Eluru/Kukunuru = official "Kukunoor" (distance 2, genuinely under the
threshold - not clear why the first pass missed it; re-verified directly
rather than assumed).

One more, SPSR Nellore/Nellore rural, is the counterpart to this table's
already-matched "Nellore urban": AP CODES' own list has a bare "Nellore"
(the rural remainder) plus a separately-named "Nellore Urban" - the
bare name was too different from "Nellore rural" for the automated
matcher to accept, so paired here directly once noticed.

**Two source-data quality artifacts found and disclosed, not silently
fixed**: (1) AP CODES' own Prakasam-search "Kandukur"/"Voletivaripalem"
share an ambiguous duplicate mandal code (5148) in the source's own
mandal list - resolved by fetching both 5147 and 5148 directly and
confirming they return two genuinely different, non-overlapping village
lists; 5148 used for Kandukur (its own unambiguous exact-name match),
5147 for Voletivaripalem. (2) Rajamahendravaram Urban's one village is
literally named "Rajajmundry Urban" in the source (a typo for
"Rajahmundry Urban") - preserved verbatim rather than silently
corrected, consistent with this project's practice of not rewriting
source data.

450 real village rows added (15,988 -> 16,438), same cleaning/title-
casing convention as every prior village migration. Idempotent by
design (`ON CONFLICT ON CONSTRAINT uq_village_mandal_name DO NOTHING`).

**Not done, correctly**: 23 mandals remain village-less - the genuine
Rural/Urban/East/West/North/South structural splits (see point 1 above,
now spanning Anantapur/Chittoor/Guntur/Kurnool/Nandyal/Ongole/
Vizianagaram/Adoni/Machilipatnam/Visakhapatnam-Urban-gap - 22 mandals),
plus Alluri Sitharama Raju's Etapaka/Gurthedu and Annamayya's Vayalpad,
whose nearest official candidates (distance 3-4) were manually reviewed
and rejected as genuinely different real places, not this table's mandal
under a different name.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0106c9d5f59f'
down_revision: Union[str, None] = 'f089b96621c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_VILLAGES_BY_DISTRICT_MANDAL = {
    # cross-district: filed under Chittoor in official data
    ("Annamayya", "Chowdepalle"): [
        "29 A. Chintamakulapa", "A. Kothakota", "Charala", "Chowdepalle", "Diguvapalle",
        "Durgasamudram", "Gaddamvaripalle", "Katiperi", "Kogathi", "Kondamarri", "Laddigam",
        "Pandillapalle", "Peddayallakuntla", "Pudipatla", "Settipeta",
    ],
    # cross-district: filed under Chittoor
    ("Annamayya", "Sodam"): [
        "Ammagaripalle", "Booragamanda", "Cherukuvaripalle", "Chintamakulapalle",
        "Errathivaripalle", "Gongivaripalle", "Khambhamvaripalle", "Nadigadda", "Palamanda",
        "Sodam", "Thatiguntapalem", "Thimmanayanipalle", "Vootupalle",
    ],
    # cross-district: filed under Chittoor
    ("Annamayya", "Somala"): [
        "Avulapalle", "Irikipenta", "Kamireddivaripalle", "Kanduru", "Mittapalle",
        "Nanjampeta At Chadamb", "Nellimanda", "Peddaupparapalle", "S. Nadimpalle", "Somala",
        "Thamminayanipalle", "Upparapalle", "Valligatla",
    ],
    # cross-district: filed under Konaseema
    ("East Godavari", "Kapileswarapuram"): [
        "Addankivari Lanka", "Angara", "Atchutapuram", "Kaleru", "Kapileswarapuram",
        "Kedara Lanka", "Korumilli", "Machara", "Nagula Cheruvu", "Nalluru", "Nelaturu",
        "Nidasanametta", "Padamati Khandrika", "Teki", "Thatapudi", "Vadlamuru", "Vakatippa",
        "Valluru", "Vedurumudi", "West Khandrika",
    ],
    # cross-district: filed under Konaseema
    ("East Godavari", "Mandapeta"): [
        "Arthamuru", "Chinadevarapudi", "Dwarapudi", "Ippanapadu", "Kesavaram", "Mandapeta",
        "Maredubaka", "Meruipadu", "Palathodu", "Tapeswaram", "Velagathodu",
        "Vemulapalle At Seetay", "Yeditha", "Z.Medapadu",
    ],
    # cross-district: filed under Eluru
    ("West Godavari", "Ganapavaram"): [
        "Agraharagopavaram", "Ardhavaram", "Cherukuganuma Agraha", "Chinaramachandrapura",
        "Dasulakumudavalli", "Ganapavaram", "Jagannadhapuram", "Jallikakinada", "Kasipadu",
        "Kesavaram", "Komarru", "Kommara", "Kothapalli", "Moyyeru", "Muggulla",
        "Mupparthipadu", "Pippara", "Saripalle", "Seethalamkondepadu", "Vakapalli", "Valluru",
        "Varadarajapuram", "Veereswarapuram", "Velagapalli", "Venkatrajapuram",
    ],
    # cross-district: filed under Bapatla
    ("Prakasam", "Addanki"): [
        "Addanki (North) (U)", "Addanki (South) (R)", "Bommanampadu", "Chakraya Palem",
        "Chinakotha Palli", "Dharmavaram", "Dhenuva Konda", "Gopalapuram", "Kalavakuru",
        "Kotikalapudi", "Kunkupadu", "Mani Keswaram", "Modepalli", "Mylavaram", "Nannurupadu",
        "Narasimha Puram", "Ramayapalem", "Uppalapadu", "Vemparala",
    ],
    # cross-district: filed under SPSR Nellore
    ("Prakasam", "Gudluru"): [
        "Ammavari Palem", "Basireddy Palem", "Chevuru", "Chinala Trapi", "Dappalampadu",
        "Darakani Padu", "Gudlur", "Gundla Palem", "Kotha Peta", "Mocharla", "Nayudu Palem",
        "Parakonda Padu", "Parakonda Paduagraharam", "Potluru", "Pureti Palli", "Ravur",
        "Swarnajipuram", "Venkam Peta",
    ],
    # cross-district: filed under SPSR Nellore; code 5148 ambiguous in source (also mislabeled Voletivaripalem) - verified unambiguous by exact-name search
    ("Prakasam", "Kandukur"): [
        "Anandapuram", "Anantha Sagaram", "Donda Padu", "G.Meka Padu", "Jillellamudi",
        "Kancharagunta", "Kandukur", "Kondamudusu Palem", "Kondikandukur", "Kovur",
        "M.Kesaramvarikandrik", "Machavaram", "Madanagopala Puram", "Mahadevapuram", "Mopadu",
        "Nekunam Puram K.Kandrika", "Ogur", "Palukur", "Palur", "Pandala Padu",
        "Vikkirala Peta",
    ],
    # cross-district: filed under Bapatla
    ("Prakasam", "Korisapadu"): [
        "Anamanamur", "Bodduvari Palem", "Dyvalaravuru", "Korisa Padu", "Pamidi Padu",
        "Pichikalagudipadu", "Prasangula Padu", "Rachapudi", "Ravinuthala", "Somavarap Padu",
    ],
    # cross-district: filed under SPSR Nellore
    ("Prakasam", "Lingasamudram"): [
        "Anneboina Palli", "Cheemala Penta", "China Pavani", "Ganga Palem",
        "Janamreddi Kandrika", "Lingasamudram", "Mala Konda Rayuni PA", "Mogili Charla",
        "Mukteswaram", "Mutyalapadu", "Narasimha Puram", "Pentrala", "Racheruvu Raju Palem",
        "Ralla Padu", "Thimmareddy Palem", "Thunugunta", "Thurpu Raju Palem",
        "Veera Raghavuni Kota", "Vengala Puram", "Viswanadhapuram",
    ],
    # cross-district: filed under Bapatla
    ("Prakasam", "Santhamaguluru"): [
        "Elchur", "Gopa Puram", "Gurije Palli", "Kame Palli", "Kommala Padu", "Kopparam",
        "Kunduru (East)", "Kunduru (West)", "Santhamagulur", "Tangedu Malli",
        "Vellala Cheruvu",
    ],
    # cross-district: filed under SPSR Nellore; source lists this name twice (5147/5148) - used 5147, since 5148 verified as Kandukur
    ("Prakasam", "Voletivaripalem"): [
        "Ayyavari Palli", "Chundi", "East Polineni Palem", "Kakutur", "Kalavalla",
        "Kalidasu Vari Kandri", "Konda Samudram", "Kondareddi Palem", "Naladalapur",
        "Nawab Palem", "Nekunam Puramaliaspo", "Nukavaram", "Polineni Cheruvu",
        "Ramachandra Puram", "Ramalinga Puram", "Sakhavaram", "Sameera Palem",
        "Singamaeni Palle", "Veeranna Palem", "Voletivari Palem", "Z.Uppala Padu",
    ],
    # cross-district: filed under Annamayya
    ("Tirupati", "Chitvel"): [
        "Bhakrapuram", "Cherlopalle", "Chintalachelika", "Chitvel", "Devamachupalle",
        "K.S.Agraharam", "K.V.R.R. Puram", "Kalvavarikhandrika", "Kampasamudram",
        "Maharajapuram @siddareddipalle", "Malemarpuram", "Mallemadugu", "Mylapalle",
        "Nagaripadu", "Nagavaram", "Nethivaripalle", "Rajukunta", "Thimmayapalem",
        "Thumma Konda",
    ],
    # cross-district: filed under Annamayya
    ("Tirupati", "Obulavaripalle"): [
        "Bommavaram", "Botimeedapalle", "Chinnaorampadu", "Gadela", "Gobburuvaripalle",
        "Govindampalle", "Jillelamadaka", "Korlakunta", "Mangampeta", "Mukkavaripalle",
        "Nukanapalle", "Peddarampadu", "Rallacheruvupalle", "Venkatesapuram",
        "Yerraguntakota",
    ],
    # cross-district: filed under Annamayya
    ("Tirupati", "Pullampeta"): [
        "A.Channamambapuram", "Anantaiahgaripalle", "Ananthasamudram", "Apparajupeta",
        "Dalavaipalle", "Dandlopalle", "Devasamudram", "Garalamadugu", "Immanur",
        "Ketharajupalle", "Kommanavaripalle", "Kothapalle Agraharam", "Perigavaram",
        "Pullampeta", "Puthanavaripalle", "Ramasamudram", "Rangampalle", "Reddipalle",
        "Sreerangarajupalem", "Thippayapalle", "Thiru Vengalanatharajapuram",
        "Utukuruchalivendala", "Utukuruvenkatampalle", "Vallurupalle", "Vathalur",
    ],
    # cross-district + spelling variant: official 'Ballikuruva' under Bapatla
    ("Prakasam", "Ballikurava"): [
        "Ballikurava", "Chennupalli", "Gorre Padu", "Guntu Palli", "Konidena", "Koppera Padu",
        "Koppera Palem", "Kukatla Palli", "Mukteswaram", "Sankaralingam Gudipadu",
        "Uppumagulur", "Vaidana", "Valla Palle", "Vemavaram",
    ],
    # cross-district + spelling variant: official 'Penagaluru' (also appears under YSR Kadapa, same code)
    ("Tirupati", "Penagalur"): [
        "Damancherla", "Girijamambaouram", "Indlur", "Itimarpuram", "Jattivaripalle",
        "Kambalakunta", "Komantharajupuram", "Kondur", "Konduruchinrayasamud",
        "Nallapureddipalle", "Narasingarajupuram", "Narayana Nellore", "Obili", "Penagalur",
        "Penagalur Agraharam", "Pondalur", "Pondaluru Venkatampa", "Siddavaram",
        "Singanamala", "Singanamala Chennarayasamudram", "Singanamala Vengamambapuram",
        "Singareddipalle", "Siriavaram", "Thimmamambapuram", "Thirumalarajupeta",
        "Thirunampalle", "Velagacherla", "Yelagacherla Mangamambapuram",
    ],
    # same-district spelling variant: official 'Kukunoor', missed by the distance threshold originally
    ("Eluru", "Kukunuru"): [
        "Amaravaram", "Arvaipalle", "Cheeravalli", "Dacharam", "Damaracharla", "Ganapavaram",
        "Gommugudem", "Gommuru", "Gumpanapalle", "Ibrahimpeta", "Kivvaka", "Komatlagudem",
        "Kondapalle", "Kowndinyamukthi", "Kukunoor", "Madhavaram", "Maredubaka", "Pocharam",
        "Polaram", "Ramachandrapuram", "Ravigudem (Big)", "Seetharama Nagar", "Sridhara",
        "Thondipaka", "Upperu", "Vinjaram",
    ],
    # abbreviation expansion: official 'B Kothakota' (B. = Beerangi)
    ("Annamayya", "Beerangi Kothakota"): [
        "B.Kothakota", "Badikayalapalle", "Beerangi", "Boyyappagaripalle", "Gattu",
        "Gollapalle", "Gummasamudram", "Kotavooru", "Thummanamgutta",
    ],
    # historical name: official 'Sidhout' - confirmed same place via matching Telugu name
    ("YSR Kadapa", "Siddavatam"): [
        "Gundlamoola", "Jangalapalle", "Jyothi", "Kadapayapalle", "Kanumalapalle",
        "Lingampalle", "Machupalle", "Mandapalle", "Mulapalle", "Nekanapuram", "Peddapalle",
        "Ponnavolu", "S.Rajampeta", "Shakarajupalle", "Sithout At Siddavatta", "Tokkolu",
        "Velugupalle", "Vontithatipalle",
    ],
    # acronym expansion: official 'S.A.K.N. MANDAL' - confirmed via matching Telugu name
    ("YSR Kadapa", "Sri Avadhutha Kasinayana"): [
        "Akkamgundla", "Akkampeta", "Balayapalli", "Ganganapalli", "Gontivaripalli",
        "Itugullapadu", "Katheragandla", "Moolapalli", "Narasapuram", "Nayunipalli",
        "Obulapuram", "Pagadalapalli", "Pittigunta", "Rampadu", "Savisettipalli", "Uppalur",
        "Vankamarri", "Varikunta", "Vasudevapuram", "Vengalampalli",
    ],
    # historical name: official 'Rajahmundry Rural'
    ("East Godavari", "Rajamahendravaram Rural"): [
        "Bommuru (U)", "Dowleswaram (U)", "Hukumpeta (U)", "Katheru (U)", "Kolamuru",
        "Morampudi", "Pidimgoyyi", "Rajahmundry Nma (OG)", "Rajavolu", "Satelite City",
        "Torredu",
    ],
    # historical name: official 'Rajahmundry Urban'
    ("East Godavari", "Rajamahendravaram Urban"): [
        "Rajajmundry Urban",
    ],
    # historical name: official 'Cuddapah' (renamed Kadapa in 2005)
    ("YSR Kadapa", "Kadapa"): [
        "Akkayapalle (U)", "Chemmumiapet (U)", "Chinnachowk (U)", "Gudur", "Kadapa Urban",
        "Nagarajupet", "Palempalle", "Patha Kadapa", "Putlampalli", "Ramaraju Palle",
        "Ukkayapalle",
    ],
    # official 'Nellore' (bare) is the Rural counterpart - 'Nellore Urban' already matched separately
    ("SPSR Nellore", "Nellore rural"): [
        "Akkacheruvupadu", "Allipuram", "Amamcherla", "Ambapuram", "Buja Buja Nellore",
        "Chintareddipalem", "Devarapalem", "Donthali", "Golla Kandukur", "Gudipallipadu",
        "Gundlapalem", "Kakupalle-I", "Kakupalle-II", "Kallurpalle (OG)", "Kandamuru",
        "Kanuparthipadu", "Kondayapalem", "Mannavarappadu", "Mattempadu", "Mogallapalem",
        "Mulumudi", "Nellore-I (R)", "Ogurupadu", "Padarupalle", "Pedda Cherukur",
        "Penubarthi", "Pottepalem", "Sajjapuram", "South Mopur", "Upputuru", "Vedayapalem",
        "Vellanti", "Visavavilettipadu",
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
