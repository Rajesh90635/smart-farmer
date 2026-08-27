"""fix no-space-abbreviation casing on 246 village names

Revision ID: f089b96621c7
Revises: aacc6f6427d4
Create Date: 2026-08-27 02:00:00.000000

Cosmetic corrective follow-up to 3d61e7bd3ba9, requested directly by the
user after it was disclosed alongside the aacc6f6427d4 follow-up. That
migration's title-caser only treated whitespace/"("/")"/"-" as word
boundaries, so a no-space abbreviation like the source's own
"R.T.PURAM" or "Y.S.R.Puram" got title-cased as a single token -
capitalizing just the first letter and lowercasing the rest - producing
"R.t.puram" / "Y.s.r.puram" instead of the correct "R.T.Puram" /
"Y.S.R.Puram". aacc6f6427d4 already fixed the title-caser itself (splits
on "." too) for its own 5 new mandals; this migration applies the same
corrected casing retroactively to the 246 already-committed village
names (out of 3d61e7bd3ba9's 15,886) that the old title-caser mis-cased.

This is a pure display-casing correction, not a data-correctness fix -
every affected village already existed under its (differently-cased)
name; no rows are added, removed, or reassigned between mandals. Found
by regenerating each affected name from the same cached source data
already fetched for 3d61e7bd3ba9 (villages_raw.json, not re-fetched from
the API) and diffing the old vs. corrected title-casing function;
confirmed zero within-mandal name collisions before writing this
migration (i.e. no corrected name coincides with another village
already present in the same mandal, which would violate
uq_village_mandal_name).

Idempotent by construction: each UPDATE only touches rows still holding
the old (mis-cased) name, so a re-run matches zero rows and is a no-op -
matching this project's standing idempotent-seeding convention, applied
here to an UPDATE rather than an INSERT.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f089b96621c7'
down_revision: Union[str, None] = 'aacc6f6427d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (district, mandal, old_name, new_name)
_CASING_FIXES = [
    # Alluri Sitharama Raju
    ("Alluri Sitharama Raju", "Ananthagiri", "R.t.puram", "R.T.Puram"),
    ("Alluri Sitharama Raju", "Ananthagiri", "Y.s.r.puram", "Y.S.R.Puram"),
    ("Alluri Sitharama Raju", "Ganagaraju Madugula", "A.bandaveedhi", "A.Bandaveedhi"),
    ("Alluri Sitharama Raju", "Ganagaraju Madugula", "G.m.kothuru", "G.M.Kothuru"),
    ("Alluri Sitharama Raju", "Ganagaraju Madugula", "G.nittaputtu", "G.Nittaputtu"),
    ("Alluri Sitharama Raju", "Ganagaraju Madugula", "K.bandaveedhi", "K.Bandaveedhi"),
    ("Alluri Sitharama Raju", "Ganagaraju Madugula", "K.g.madugula", "K.G.Madugula"),
    ("Alluri Sitharama Raju", "Ganagaraju Madugula", "M.nittaputtu", "M.Nittaputtu"),
    ("Alluri Sitharama Raju", "Ganagaraju Madugula", "P.g.madugula", "P.G.Madugula"),
    ("Alluri Sitharama Raju", "Ganagaraju Madugula", "S.kothuru", "S.Kothuru"),
    ("Alluri Sitharama Raju", "Gangavaram", "B.sivaramapatnam", "B.Sivaramapatnam"),
    ("Alluri Sitharama Raju", "Hukumpeta", "D.chintalaveedhi", "D.Chintalaveedhi"),
    ("Alluri Sitharama Raju", "Koyyuru", "U.cheedipalem", "U.Cheedipalem"),
    ("Alluri Sitharama Raju", "Kunavaram", "S.kothagudem", "S.Kothagudem"),
    ("Alluri Sitharama Raju", "Rampachodavaram", "B.ramannapalem", "B.Ramannapalem"),
    ("Alluri Sitharama Raju", "Rampachodavaram", "K.yerrampalem", "K.Yerrampalem"),
    ("Alluri Sitharama Raju", "Rampachodavaram", "T.burugubanda", "T.Burugubanda"),
    ("Alluri Sitharama Raju", "Y. Ramavaram", "G.vattigedda", "G.Vattigedda"),
    # Anakapalli
    ("Anakapalli", "Butchayyapeta", "R Bheemavaram", "R. Bheemavaram"),
    ("Anakapalli", "Butchayyapeta", "R.sivaramapuram", "R.Sivaramapuram"),
    ("Anakapalli", "K. Kotapadu", "Kavi.kondala Agrahar", "Kavi.Kondala Agrahar"),
    ("Anakapalli", "Kotauratla", "G.sanyasirajupalem", "G.Sanyasirajupalem"),
    ("Anakapalli", "Madugula", "P.sivaram Puram", "P.Sivaram Puram"),
    ("Anakapalli", "Nakkapalli", "G.jagannadhapuram", "G.Jagannadhapuram"),
    # Anantapur
    ("Anantapur", "Bommanahal", "D.honnur", "D.Honnur"),
    ("Anantapur", "D.Hirehal", "D.hirehal", "D.Hirehal"),
    ("Anantapur", "D.Hirehal", "H.hossahalli", "H.Hossahalli"),
    ("Anantapur", "D.Hirehal", "H.siddapuram", "H.Siddapuram"),
    ("Anantapur", "Gummagatta", "S.hosahalli", "S.Hosahalli"),
    ("Anantapur", "Kanekal", "N.hanumapuram", "N.Hanumapuram"),
    ("Anantapur", "Kundurpi", "S.mallapuram", "S.Mallapuram"),
    ("Anantapur", "Narpala", "B.pappuru", "B.Pappuru"),
    ("Anantapur", "Rayadurgam", "D.kondapuram", "D.Kondapuram"),
    ("Anantapur", "Uravakonda", "Y.rampuram", "Y.Rampuram"),
    ("Anantapur", "Vidapanakal", "N.thimmapuram", "N.Thimmapuram"),
    ("Anantapur", "Yellanur", "Y.chintakayamanda", "Y.Chintakayamanda"),
    # Annamayya
    ("Annamayya", "Koduru", "K.buduguntapalle", "K.Buduguntapalle"),
    ("Annamayya", "Mulakalacheruvu", "T.sowdasamudram", "T.Sowdasamudram"),
    ("Annamayya", "Peddathippasamudram", "T.sadum", "T.Sadum"),
    ("Annamayya", "Rajampeta", "R.buduguntapalle", "R.Buduguntapalle"),
    ("Annamayya", "Ramasamudram", "R.nadimpalle", "R.Nadimpalle"),
    ("Annamayya", "Sambepalli", "Sho.somavaram", "Sho.Somavaram"),
    ("Annamayya", "T. Sundupalle", "T.sundupalle", "T.Sundupalle"),
    # Chittoor
    ("Chittoor", "Gangadhara Nellore", "B.c.khandriga", "B.C.Khandriga"),
    ("Chittoor", "Gudipala", "190.ramapuram", "190.Ramapuram"),
    ("Chittoor", "Gudipala", "197.ramapuram", "197.Ramapuram"),
    ("Chittoor", "Gudipala", "5.lakshmambapuram", "5.Lakshmambapuram"),
    ("Chittoor", "Kuppam", "T.sadumur", "T.Sadumur"),
    ("Chittoor", "Palasamudram", "Narasimhapuram @ A.khandriga", "Narasimhapuram @ A.Khandriga"),
    ("Chittoor", "Pulicherla", "E.ramireddygaripalle", "E.Ramireddygaripalle"),
    ("Chittoor", "Srirangarajapuram", "D.b.r.bylu", "D.B.R.Bylu"),
    ("Chittoor", "Venkatagirikota", "S.bandapalle", "S.Bandapalle"),
    ("Chittoor", "Yadamari", "184.gollapalle", "184.Gollapalle"),
    # East Godavari
    ("East Godavari", "Nidadavolu", "D.muppavaram", "D.Muppavaram"),
    ("East Godavari", "Nidadavolu", "J.khandrika", "J.Khandrika"),
    # Eluru
    ("Eluru", "Dwaraka Tirumala", "G.kothapalle", "G.Kothapalle"),
    ("Eluru", "Dwaraka Tirumala", "I.s.jagannadhapuram", "I.S.Jagannadhapuram"),
    ("Eluru", "Dwaraka Tirumala", "I.s.raghavapuram", "I.S.Raghavapuram"),
    ("Eluru", "Dwaraka Tirumala", "Kommara(North)", "Kommara (North)"),
    ("Eluru", "Dwaraka Tirumala", "Kommara(South)", "Kommara (South)"),
    ("Eluru", "Dwaraka Tirumala", "M.nagulapalli", "M.Nagulapalli"),
    ("Eluru", "Dwaraka Tirumala", "P.kannapuram", "P.Kannapuram"),
    ("Eluru", "Jeelugu Milli", "P.ankam Palem", "P.Ankam Palem"),
    ("Eluru", "Pedavegi", "K.kannapuram", "K.Kannapuram"),
    ("Eluru", "T. Narasapuram", "T.narasapuram", "T.Narasapuram"),
    # Guntur
    ("Guntur", "Tenali", "Tenali(U)", "Tenali (U)"),
    # Kakinada
    ("Kakinada", "Gandepalle", "P.nayakampalle", "P.Nayakampalle"),
    ("Kakinada", "Kotananduru", "T.jagannadha Nagaram", "T.Jagannadha Nagaram"),
    ("Kakinada", "Prathipadu", "U Jagannadhapuram", "U. Jagannadhapuram"),
    ("Kakinada", "Rowthulapudi", "D.jagannadhapuram", "D.Jagannadhapuram"),
    ("Kakinada", "Rowthulapudi", "D.pydipala", "D.Pydipala"),
    ("Kakinada", "Rowthulapudi", "M.kothuru", "M.Kothuru"),
    ("Kakinada", "Rowthulapudi", "R.venkatapuram", "R.Venkatapuram"),
    ("Kakinada", "Rowthulapudi", "S.agraharam", "S.Agraharam"),
    ("Kakinada", "Thondangi", "A.v.nagaram", "A.V.Nagaram"),
    ("Kakinada", "Thondangi", "P.e.chinnayapalem", "P.E.Chinnayapalem"),
    ("Kakinada", "Yeleswaram", "C.rayavaram", "C.Rayavaram"),
    # Krishna
    ("Krishna", "Ghantasala", "V.rudravaram", "V.Rudravaram"),
    ("Krishna", "Nagayalanka", "T.kothapalem", "T.Kothapalem"),
    # Kurnool
    ("Kurnool", "Alur", "A.gonehal", "A.Gonehal"),
    ("Kurnool", "C. Belagal", "C.belagal", "C.Belagal"),
    ("Kurnool", "Devanakonda", "P.kotakonda", "P.Kotakonda"),
    ("Kurnool", "Devanakonda", "S.thimmapuram", "S.Thimmapuram"),
    ("Kurnool", "Halaharvi", "J.hosahalli", "J.Hosahalli"),
    ("Kurnool", "Kallur", "A.gokulapadu", "A.Gokulapadu"),
    ("Kurnool", "Kallur", "K.markapuram", "K.Markapuram"),
    ("Kurnool", "Orvakal", "N.konthalapadu", "N.Konthalapadu"),
    ("Kurnool", "Veldurthi", "Sho.boyanapalle", "Sho.Boyanapalle"),
    ("Kurnool", "Veldurthi", "Sho.peremula", "Sho.Peremula"),
    ("Kurnool", "Yemmiganur", "K.thimmapuram", "K.Thimmapuram"),
    # Nandyal
    ("Nandyal", "Allagadda", "G.jambuladinne", "G.Jambuladinne"),
    ("Nandyal", "Allagadda", "R.krishnapuram", "R.Krishnapuram"),
    ("Nandyal", "Allagadda", "S.lingamdinne", "S.Lingamdinne"),
    ("Nandyal", "Dornipadu", "W.govindinne", "W.Govindinne"),
    ("Nandyal", "Gospadu", "M.chintakunta", "M.Chintakunta"),
    ("Nandyal", "Gospadu", "M.krishnapuram", "M.Krishnapuram"),
    ("Nandyal", "Gospadu", "S.kuluru", "S.Kuluru"),
    ("Nandyal", "Gospadu", "S.nagulavaram", "S.Nagulavaram"),
    ("Nandyal", "Kothapalle", "P.gummadapuram", "P.Gummadapuram"),
    ("Nandyal", "Pagidyala", "Prathakota(East)", "Prathakota (East)"),
    ("Nandyal", "Pagidyala", "Prathakota(West)", "Prathakota (West)"),
    ("Nandyal", "Rudravaram", "R.nagulavaram", "R.Nagulavaram"),
    ("Nandyal", "Rudravaram", "T.lingamdinne", "T.Lingamdinne"),
    ("Nandyal", "Uyyalawada", "R Jambuladinne", "R. Jambuladinne"),
    ("Nandyal", "Uyyalawada", "R.papampalle", "R.Papampalle"),
    ("Nandyal", "Uyyalawada", "S.kothapalle", "S.Kothapalle"),
    # NTR
    ("NTR", "Ibrahimpatnam", "N.pothavaram", "N.Pothavaram"),
    ("NTR", "Ibrahimpatnam", "Z.nave Pothavaram", "Z.Nave Pothavaram"),
    ("NTR", "Mylavaram", "T.gannavaram", "T.Gannavaram"),
    ("NTR", "Nandigama", "Nandigama (U)(P)", "Nandigama (U) (P)"),
    # Palnadu
    ("Palnadu", "Narasaraopet", "Potavarappadu(U.I)", "Potavarappadu (U.I)"),
    ("Palnadu", "Nuzendla", "T.annavaram", "T.Annavaram"),
    ("Palnadu", "Nuzendla", "V.appapuram", "V.Appapuram"),
    ("Palnadu", "Rajupalem", "Kubadpuram(Anupalem)", "Kubadpuram (Anupalem)"),
    ("Palnadu", "Sattenapalli", "Sattenapalli(U)", "Sattenapalli (U)"),
    # Parvathipuram Manyam
    ("Parvathipuram Manyam", "Balijipeta", "Badevalasa At Lt.vala", "Badevalasa At LT.Vala"),
    ("Parvathipuram Manyam", "Garugubilli", "Gadabavalasa G.r.pur", "Gadabavalasa G.R.Pur"),
    ("Parvathipuram Manyam", "Komarada", "Sitamambapuram(Near Gumada)", "Sitamambapuram (Near Gumada)"),
    ("Parvathipuram Manyam", "Komarada", "Sitamambapuram(Near Komarada)", "Sitamambapuram (Near Komarada)"),
    ("Parvathipuram Manyam", "Makkuva", "N.r.c. Rarajupuram", "N.R.C. Rarajupuram"),
    ("Parvathipuram Manyam", "Palakonda", "N.k.rajapuram", "N.K.Rajapuram"),
    ("Parvathipuram Manyam", "Palakonda", "P.ramabhadrarajupeta", "P.Ramabhadrarajupeta"),
    ("Parvathipuram Manyam", "Palakonda", "T.d.parapurram", "T.D.Parapurram"),
    ("Parvathipuram Manyam", "Palakonda", "T.k.rajapuram", "T.K.Rajapuram"),
    ("Parvathipuram Manyam", "Seethanagaram", "R.venkampeta", "R.Venkampeta"),
    ("Parvathipuram Manyam", "Seethanagaram", "Seetharampuram(N)Sub", "Seetharampuram (N)Sub"),
    ("Parvathipuram Manyam", "Veeraghattam", "U.venkampeta", "U.Venkampeta"),
    # Prakasam
    ("Prakasam", "Chandrasekharapuram", "A.kotha Palli", "A.Kotha Palli"),
    ("Prakasam", "Kanigiri", "P.p.kandrika", "P.P.Kandrika"),
    ("Prakasam", "Kondapi", "C.a.b.kandrika", "C.A.B.Kandrika"),
    ("Prakasam", "Kondapi", "C.m.kandrika", "C.M.Kandrika"),
    ("Prakasam", "Kondapi", "G.d.kandrika", "G.D.Kandrika"),
    ("Prakasam", "Kondapi", "K.g.kandrika", "K.G.Kandrika"),
    ("Prakasam", "Kondapi", "K.uppalapadu", "K.Uppalapadu"),
    ("Prakasam", "Kondapi", "P.k.kandrika", "P.K.Kandrika"),
    ("Prakasam", "Kondapi", "P.m.kandrika", "P.M.Kandrika"),
    ("Prakasam", "Naguluppalapadu", "H.nidamanur", "H.Nidamanur"),
    ("Prakasam", "Pedda Araveedu", "S.kotha Palli", "S.Kotha Palli"),
    ("Prakasam", "Podili", "T.salluru", "T.Salluru"),
    ("Prakasam", "Ponnaluru", "P.balagopala Puram", "P.Balagopala Puram"),
    ("Prakasam", "Ponnaluru", "P.g.kandrika", "P.G.Kandrika"),
    ("Prakasam", "Ponnaluru", "V.k.kandrika", "V.K.Kandrika"),
    ("Prakasam", "Tanguturu", "M.nidamalur", "M.Nidamalur"),
    ("Prakasam", "Ulavapadu", "K.s.r.kandrika", "K.S.R.Kandrika"),
    ("Prakasam", "Veligandla", "K.k.khandrika", "K.K.Khandrika"),
    ("Prakasam", "Zarugumalli", "I.m.khndrika", "I.M.Khndrika"),
    ("Prakasam", "Zarugumalli", "J.g.kandrika", "J.G.Kandrika"),
    ("Prakasam", "Zarugumalli", "K.bitragunta", "K.Bitragunta"),
    ("Prakasam", "Zarugumalli", "N.m.v.kandrika", "N.M.V.Kandrika"),
    ("Prakasam", "Zarugumalli", "N.n.kandrika", "N.N.Kandrika"),
    ("Prakasam", "Zarugumalli", "N.v.v.kandrika", "N.V.V.Kandrika"),
    ("Prakasam", "Zarugumalli", "P.g.kandrika", "P.G.Kandrika"),
    ("Prakasam", "Zarugumalli", "P.m.kandrika", "P.M.Kandrika"),
    ("Prakasam", "Zarugumalli", "P.m.v.kandrika", "P.M.V.Kandrika"),
    # SPSR Nellore
    ("SPSR Nellore", "Thotapalli Gudur", "T.p.gudur - I", "T.P.Gudur - I"),
    ("SPSR Nellore", "Thotapalli Gudur", "T.p.gudur - II", "T.P.Gudur - II"),
    # Sri Sathya Sai
    ("Sri Sathya Sai", "Agali", "P.byadigera", "P.Byadigera"),
    ("Sri Sathya Sai", "Amadagur", "S.kuruvapalle", "S.Kuruvapalle"),
    ("Sri Sathya Sai", "Bathalapalle", "D.cherlopalle", "D.Cherlopalle"),
    ("Sri Sathya Sai", "Kothacheruvu", "K.locharla", "K.Locharla"),
    ("Sri Sathya Sai", "Madakasira", "C.kodigepalle", "C.Kodigepalle"),
    ("Sri Sathya Sai", "Mudigubba", "S.bandlapalle", "S.Bandlapalle"),
    ("Sri Sathya Sai", "Nallacheruvu", "S.mulakalapalle", "S.Mulakalapalle"),
    ("Sri Sathya Sai", "Roddam", "R Locharla", "R. Locharla"),
    ("Sri Sathya Sai", "Rolla", "M.rayapuram", "M.Rayapuram"),
    ("Sri Sathya Sai", "Tanakal", "T.sadum", "T.Sadum"),
    # Srikakulam
    ("Srikakulam", "Ganguvarisigadam", "S.p.ramachandrapuram", "S.P.Ramachandrapuram"),
    # Tirupati
    ("Tirupati", "Doravarisatram", "K.d.khandrika", "K.D.Khandrika"),
    ("Tirupati", "Doravarisatram", "P.khandrika", "P.Khandrika"),
    ("Tirupati", "Gudur", "N.sangameswaraswamy Khandrika", "N.Sangameswaraswamy Khandrika"),
    ("Tirupati", "K.V.B. Puram", "Gnanamamba Puram @ P.khandriga", "Gnanamamba Puram @ P.Khandriga"),
    ("Tirupati", "K.V.B. Puram", "Mattamanapathattu R.khandriga", "Mattamanapathattu R.Khandriga"),
    ("Tirupati", "K.V.B. Puram", "Venkatapuram @ G.khandriga", "Venkatapuram @ G.Khandriga"),
    ("Tirupati", "Naidupeta", "L.a.sagaram", "L.A.Sagaram"),
    ("Tirupati", "Ozili", "L.j.kattubadi", "L.J.Kattubadi"),
    ("Tirupati", "Pellakur", "P.c.t.khandrika", "P.C.T.Khandrika"),
    ("Tirupati", "Renigunta", "R Mallavaram", "R. Mallavaram"),
    ("Tirupati", "Sullurpeta", "K.c.narasimhunigunta", "K.C.Narasimhunigunta"),
    ("Tirupati", "Thottambedu", "Gunteligunta @ L.n.puram", "Gunteligunta @ L.N.Puram"),
    ("Tirupati", "Vadamalapeta", "K.g.khandriga", "K.G.Khandriga"),
    ("Tirupati", "Vadamalapeta", "T.c.agrajaram", "T.C.Agrajaram"),
    ("Tirupati", "Venkatagiri", "C.guntavenganna Khandrika", "C.Guntavenganna Khandrika"),
    ("Tirupati", "Venkatagiri", "J.appalacharyula Khandrika", "J.Appalacharyula Khandrika"),
    # Visakhapatnam
    ("Visakhapatnam", "Anandapuram", "N.g.r. Puram", "N.G.R. Puram"),
    ("Visakhapatnam", "Bheemunipatnam", "K.nagarapalem", "K.Nagarapalem"),
    # Vizianagaram
    ("Vizianagaram", "Badangi", "D.venkayyapeta", "D.Venkayyapeta"),
    ("Vizianagaram", "Badangi", "Gopalakrishna R.pura", "Gopalakrishna R.Pura"),
    ("Vizianagaram", "Badangi", "P.venkampeta", "P.Venkampeta"),
    ("Vizianagaram", "Bobbili", "Burjavalasanear M.va", "Burjavalasanear M.VA"),
    ("Vizianagaram", "Bobbili", "Jagannadhapuram(N)BO", "Jagannadhapuram (N)BO"),
    ("Vizianagaram", "Bobbili", "Panukuvalasa(N)M.vak", "Panukuvalasa (N)M.Vak"),
    ("Vizianagaram", "Bobbili", "Velagavalasa(N)Addun", "Velagavalasa (N)Addun"),
    ("Vizianagaram", "Cheepurupalli", "Purushothama S.v.lok", "Purushothama S.V.Lok"),
    ("Vizianagaram", "Dattirajeru", "M.lingalavalasa", "M.Lingalavalasa"),
    ("Vizianagaram", "Dattirajeru", "S.chintalavalasa", "S.Chintalavalasa"),
    ("Vizianagaram", "Denkada", "D.tallavalasa", "D.Tallavalasa"),
    ("Vizianagaram", "Gajapathinagaram", "M.kothavalasa", "M.Kothavalasa"),
    ("Vizianagaram", "Gajapathinagaram", "M.venkatapuram", "M.Venkatapuram"),
    ("Vizianagaram", "Gajapathinagaram", "T.k.seetharamapuram", "T.K.Seetharamapuram"),
    ("Vizianagaram", "Gantyada", "Yarakannamdora S.r.p", "Yarakannamdora S.R.P"),
    ("Vizianagaram", "Garividi", "Kondapalem At S.nagar", "Kondapalem At S.Nagar"),
    ("Vizianagaram", "Therlam", "Ramachendrapuram(Near Amity)", "Ramachendrapuram (Near Amity)"),
    ("Vizianagaram", "Therlam", "Seatharampuram(N)Amity", "Seatharampuram (N)Amity"),
    ("Vizianagaram", "Therlam", "Seetharampuram(N)Koratam", "Seetharampuram (N)Koratam"),
    ("Vizianagaram", "Therlam", "Venkampeta(At Kummaripeta)", "Venkampeta (At Kummaripeta)"),
    ("Vizianagaram", "Therlam", "Viziarampuram(N)Koratam", "Viziarampuram (N)Koratam"),
    ("Vizianagaram", "Vangara", "T.d.krishnaraya Puram", "T.D.Krishnaraya Puram"),
    ("Vizianagaram", "Vangara", "U.venkatapathi Raju Peta", "U.Venkatapathi Raju Peta"),
    ("Vizianagaram", "Vepada", "Srungaravapu K.s.ram", "Srungaravapu K.S.Ram"),
    # West Godavari
    ("West Godavari", "Akiveedu", "A.i.bheemavaram", "A.I.Bheemavaram"),
    ("West Godavari", "Narasapuram", "Chinamamidipalle(R)", "Chinamamidipalle (R)"),
    ("West Godavari", "Narasapuram", "Rustumbada(R)", "Rustumbada (R)"),
    ("West Godavari", "Pentapadu", "B.kondepadu", "B.Kondepadu"),
    # YSR Kadapa
    ("YSR Kadapa", "B. Kodur", "A.kothapalle", "A.Kothapalle"),
    ("YSR Kadapa", "B. Kodur", "M.narasimhapuram", "M.Narasimhapuram"),
    ("YSR Kadapa", "Badvel", "C.kothapalle", "C.Kothapalle"),
    ("YSR Kadapa", "Brahmamgari Matam", "D.lingampalle", "D.Lingampalle"),
    ("YSR Kadapa", "Brahmamgari Matam", "D.narasimhapuram", "D.Narasimhapuram"),
    ("YSR Kadapa", "Brahmamgari Matam", "G.narasimhapuram", "G.Narasimhapuram"),
    ("YSR Kadapa", "Brahmamgari Matam", "T.soudaravaripalle", "T.Soudaravaripalle"),
    ("YSR Kadapa", "Chinthakommadinne", "K.ramachandrapuram", "K.Ramachandrapuram"),
    ("YSR Kadapa", "Chinthakommadinne", "T.ramachandrapuram", "T.Ramachandrapuram"),
    ("YSR Kadapa", "Kamalapuram", "C.gopalapuram", "C.Gopalapuram"),
    ("YSR Kadapa", "Kamalapuram", "T.sadipirala", "T.Sadipirala"),
    ("YSR Kadapa", "Kondapuram", "K.bommepalli", "K.Bommepalli"),
    ("YSR Kadapa", "Kondapuram", "K.brahmanapalle", "K.Brahmanapalle"),
    ("YSR Kadapa", "Kondapuram", "K.sugumanchipalle", "K.Sugumanchipalle"),
    ("YSR Kadapa", "Kondapuram", "K.venkatapuram", "K.Venkatapuram"),
    ("YSR Kadapa", "Kondapuram", "S.timmapuram", "S.Timmapuram"),
    ("YSR Kadapa", "Muddanur", "K.thimmapuram", "K.Thimmapuram"),
    ("YSR Kadapa", "Mydukur", "N.mydukur", "N.Mydukur"),
    ("YSR Kadapa", "Mydukur", "S.mydukur", "S.Mydukur"),
    ("YSR Kadapa", "Peddamudium", "B.venkatapuram", "B.Venkatapuram"),
    ("YSR Kadapa", "Peddamudium", "J.kottalapalli", "J.Kottalapalli"),
    ("YSR Kadapa", "Peddamudium", "N.kottalapalli", "N.Kottalapalli"),
    ("YSR Kadapa", "Pendlimarri", "A.ramachandrapuram", "A.Ramachandrapuram"),
    ("YSR Kadapa", "Porumamilla", "S.lingampalle", "S.Lingampalle"),
    ("YSR Kadapa", "Porumamilla", "S.seshampalle", "S.Seshampalle"),
    ("YSR Kadapa", "Porumamilla", "S.veerlapalle", "S.Veerlapalle"),
    ("YSR Kadapa", "Porumamilla", "T.seshampalle", "T.Seshampalle"),
    ("YSR Kadapa", "Pulivendula", "K.velamavanipalle", "K.Velamavanipalle"),
    ("YSR Kadapa", "Veerapunayunipalle", "U.rajupalem", "U.Rajupalem"),
    ("YSR Kadapa", "Vempalle", "T.velamvaripalle", "T.Velamvaripalle"),
    ("YSR Kadapa", "Vemula", "V.kothapalle", "V.Kothapalle"),
    ("YSR Kadapa", "Yerraguntla", "P.gopalapuram", "P.Gopalapuram"),
    ("YSR Kadapa", "Yerraguntla", "T.sunkesala", "T.Sunkesala"),
]


def _flatten():
    district_names, mandal_names, old_names, new_names = [], [], [], []
    for district, mandal, old_name, new_name in _CASING_FIXES:
        district_names.append(district)
        mandal_names.append(mandal)
        old_names.append(old_name)
        new_names.append(new_name)
    return district_names, mandal_names, old_names, new_names


def _apply(from_col: str, to_col: str) -> None:
    # NOTE: the unnest() column aliases below are always (old_name, new_name)
    # regardless of direction - only which one is read as "from"/"to" varies.
    # Renaming the unnest aliases per-direction instead would be a bug: the
    # array bound to the 3rd unnest position is always old_names and the 4th
    # is always new_names, so relabeling them doesn't change what data a
    # column actually holds.
    district_names, mandal_names, old_names, new_names = _flatten()
    op.execute(
        sa.text(
            f"""
            UPDATE villages
            SET name = v.{to_col}
            FROM (
                SELECT m.id AS mandal_id, u.old_name, u.new_name
                FROM unnest(:district_names, :mandal_names, :old_names, :new_names)
                    AS u(district_name, mandal_name, old_name, new_name)
                JOIN districts d ON d.name = u.district_name
                JOIN mandals m ON m.district_id = d.id AND m.name = u.mandal_name
            ) AS v
            WHERE villages.mandal_id = v.mandal_id AND villages.name = v.{from_col}
            """
        ).bindparams(
            sa.bindparam("district_names", value=district_names, type_=sa.ARRAY(sa.String)),
            sa.bindparam("mandal_names", value=mandal_names, type_=sa.ARRAY(sa.String)),
            sa.bindparam("old_names", value=old_names, type_=sa.ARRAY(sa.String)),
            sa.bindparam("new_names", value=new_names, type_=sa.ARRAY(sa.String)),
        )
    )


def upgrade() -> None:
    _apply(from_col="old_name", to_col="new_name")


def downgrade() -> None:
    _apply(from_col="new_name", to_col="old_name")
