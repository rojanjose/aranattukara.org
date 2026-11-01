"""Turn the researched pictures in ../specs/pictures into site images + credits.

    python3 tools/build-images.py            (run from site/; needs Pillow for crops)

For every entry below: optionally crop, then run tools/optimize-images.sh to write
assets/img/<name>-{480,960,1600}.webp + -960.jpg, and record the credit in
_data/credits.yml (shown under pictures and on the Picture credits page).
Add an entry here when a new researched picture should go on the site. Photos the
owner supplies later are added the same way (source = their file, licence = theirs).
"""
import json, os, re, subprocess, sys, urllib.parse
from PIL import Image, ImageOps

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(SITE, "..", "specs", "pictures")
H, N = os.path.join(P, "history"), os.path.join(P, "now")
TMP = os.path.join(SITE, ".image-tmp")
os.makedirs(TMP, exist_ok=True)

LIC = {
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "Public domain": "https://creativecommons.org/publicdomain/mark/1.0/",
    "GODL-India": "https://www.data.gov.in/Godl",
}
meta = {}
for folder in (H, N):
    for m in json.load(open(os.path.join(folder, "commons-meta.json"))):
        meta[os.path.join(folder, m["file"])] = m

# Photos taken for the site (aranattukara.org, 31 Oct 2026). Folder → (source file, site name, title).
OWN = dict(author="aranattukara.org", date="2026-10-31", license="All rights reserved")
PL = f"{N}/places"
OWN_PHOTOS = [
    ("st-thomas-church/Front-View.jpg",              "st-thomas-church-front",       "St. Thomas Church, Aranattukara, from the church square"),
    ("st-thomas-church/front-with-gate.jpg",         "st-thomas-church-gate",        "St. Thomas Church from the gate, with the churchyard cross"),
    ("st-thomas-church/side-view.jpg",               "st-thomas-church-side",        "St. Thomas Church from the side"),
    ("st-thomas-church/side-with-coconut-trees.jpg", "st-thomas-church-palms",       "The spires of St. Thomas Church among coconut palms"),
    ("st-thomas-church/inside-view2.jpg",            "st-thomas-church-interior",    "Inside St. Thomas Church, looking towards the altar"),
    ("st-thomas-church/bell-tower.jpg",              "st-thomas-church-bell-tower",  "The bell tower of St. Thomas Church"),
    ("st-thomas-church/flag-post.jpg",               "st-thomas-church-flagpole",    "The flagpole in the church square, where the feast flag is raised"),
    ("st-thomas-church/mother-mary.jpg",             "st-thomas-church-grotto",      "The Marian grotto at St. Thomas Church"),
    ("st-thomas-church/parish-hall.jpg",             "st-thomas-church-parish-hall", "St. Thomas Church parish hall"),
    ("tharakans-high-school/road-side-view.jpg",     "tharakans-school-front",       "Tharakan's High School from the road"),
    ("tharakans-high-school/roardview2.jpg",         "tharakans-school-road",        "Tharakan's High School: the gate and name board"),
    ("tharakans-high-school/assembly-ground.jpg",    "tharakans-school-building",    "Tharakan's High School: the main building and assembly ground"),
    ("tharakans-high-school/courtyard.jpg",          "tharakans-school-courtyard",   "The big tree in the courtyard of Tharakan's High School"),
    ("tharakans-high-school/School-ground.jpg",      "tharakans-school-ground",      "The playground of Tharakan's High School"),
    ("tharakans-high-school/school-kindergarten.jpg", "tharakans-school-kindergarten", "The kindergarten and lower primary block, Tharakan's School"),
    ("john-mathai-center/main-building.jpg",         "john-matthai-centre",          "Dr John Matthai Centre, Lalur: the main building among the trees"),
    ("john-mathai-center/gate.jpg",                  "john-matthai-centre-gate",     "The gate of the Dr John Matthai Centre"),
    ("john-mathai-center/school-of-drama-fine-arts.jpg", "school-of-drama",          "The School of Drama and Fine Arts at the John Matthai Centre"),
    ("john-mathai-center/john-mathai-bust.jpg",      "john-mathai-bust",             "The bust of Dr John Mathai at the centre named after him"),
    ("john-mathai-center/events.jpg",                "school-of-drama-noticeboard",  "Play posters on the noticeboard of the School of Drama"),
    ("kol-padam/canal.jpg",                          "kol-padam-canal",              "A canal and footpath through the kol fields near Aranattukara"),
    ("kol-padam/pond.jpg",                           "kol-padam-pond",               "A pond at the edge of the kol fields near Aranattukara"),
    ("kol-padam/water-pump.jpg",                     "kol-padam-pump",               "A pump moving water in the kol fields near Aranattukara"),
    ("chiramel-tharakan-family/house-front.jpg",     "tharakan-house",               "The Chiramel Tharakan family house, Aranattukara"),
]

IA = "https://archive.org/details/keralalegislativeassembly.proceedings."
COUNCIL = dict(author="Cochin Legislative Council (Kerala Legislative Assembly archive)", license="Public domain")

# name: (source file, crop box or None, extra credit fields)
ITEMS = {
    "kol-wetland-sunset":        (f"{N}/kol-wetlands/thrissur-kole-wetland-1.jpg", None, {}),
    "kol-wetland-bund":          (f"{N}/kol-wetlands/thrissur-kole-wetland-3.jpg", None, {}),
    "kol-wetland-path":          (f"{N}/kol-wetlands/thrissur-kole-wetland-8.jpg", None, {}),
    "gould-plan-1816":           (f"{H}/upscaled/1816-plan-of-trichur-temple-and-environs-john-gould-x4.jpg", None,
                                  {"meta_from": f"{H}/maps/1816-plan-of-trichur-temple-and-environs-john-gould.jpg", "author": "John Gould (British Library)", "date": "1816"}),
    "gould-plan-1816-aranaat":   (f"{H}/upscaled/1816-gould-plan-detail-aranaat-warehouses-x4.jpg", None,
                                  {"meta_from": f"{H}/maps/1816-plan-of-trichur-temple-and-environs-john-gould.jpg", "author": "John Gould (British Library)", "date": "1816", "note": "Detail."}),
    "map-travancore-cochin-1862": (f"{H}/maps/1862-map-of-travancore-and-cochin-church-missionary-atlas.jpg", None, {"author": "Church Missionary Society", "date": "1862"}),
    "map-cochin-state-1941":     (f"{H}/maps/1941-map-of-cochin-state-census.jpg", None, {}),
    "ams-map-1955-aranattukara": (f"{H}/maps/1955-us-army-map-detail-aranattukara-and-kol-wetlands.jpg", None,
                                  {"meta_from": f"{H}/maps/1955-us-army-map-service-nc43-7-coimbatore-sheet.jpg", "note": "Detail of sheet NC 43-7."}),
    "st-thomas-church-feast-2025": (f"{H}/places/st-thomas-church-aranattukara-feast-2025.jpg", None, {}),
    "sakthan-thampuran-palace":  (f"{H}/places/sakthan-thampuran-palace-built-1795-photo-2018.jpg", None, {}),
    "sakthan-thampuran-tomb":    (f"{H}/places/tomb-of-sakthan-thampuran-photo-2018.jpg", None, {}),
    "adolph-medlycott-1890":     (f"{H}/upscaled/1890-adolph-medlycott-vicar-apostolic-of-trichur-x4.jpg", None,
                                  {"meta_from": f"{H}/people/1890-adolph-medlycott-vicar-apostolic-of-trichur.jpg"}),
    "john-mathai-1949":          (f"{H}/people/1949-john-mathai-budget-day.jpg", (160, 0, 1600, 1800), {"note": "Cropped from the budget-day photograph."}),
    "john-mathai-budget-1949":   (f"{H}/people/1949-john-mathai-budget-day.jpg", None, {}),
    "first-cabinet-1950":        (f"{H}/upscaled/1950-first-cabinet-of-india-with-john-mathai-x3.jpg", None,
                                  {"meta_from": f"{H}/people/1950-first-cabinet-of-india-with-john-mathai.jpg"}),
    "jose-kattukkaran-2011":     (f"{H}/people/2011-jose-kattukkaran-mayor-speaks-chess-tournament.jpg", (600, 180, 1240, 980), {"note": "Cropped."}),
    "fr-antony-thachuparambil-mural": (f"{H}/people/2014-fr-antony-thachuparambil-mural-kottat-church.jpg", (120, 250, 1720, 2250), {"note": "Cropped."}),
    "chavara-stamp-1987":        (f"{H}/people/1987-kuriakose-elias-chavara-stamp-of-india.jpg", None, {}),
    # Downloaded from other websites, used at the owner's (site owner's) decision of 1 Nov 2026; permission not yet given.
    "bishop-neelankavil-portrait": (f"{H}/people/mar-joseph-pastor-neelankavil-cmi-1690800077.jpeg", (52, 0, 448, 495),
                                  {"title": "Bishop Joseph Pastor Neelankavil CMI", "author": "Syro-Malabar Church", "date": "",
                                   "license": "All rights reserved", "page": "https://www.syromalabarchurch.in/", "note": "Cropped."}),
    "bishop-chirayath-portrait": (f"{H}/people/Mar-Antony-Chirayath.jpeg", (20, 0, 180, 200),
                                  {"title": "Mar Antony Chirayath", "author": "Owner unknown", "date": "",
                                   "license": "All rights reserved", "note": "Cropped. Credit to be confirmed."}),
    "st-euphrasia-portrait":     (f"{H}/people/St-Euphrasia-Eluvathingal.webp", (20, 18, 216, 298),
                                  {"title": "St. Euphrasia Eluvathingal", "author": "Artist unknown", "date": "",
                                   "license": "All rights reserved", "page": "https://saintscatholic.blogspot.com/", "note": "Devotional painting; frame cropped. Credit to be confirmed."}),
    "mathrubhumi-study-circle-logo": (f"{H}/communites/mathrubhumi-study-circle.jpeg", None,
                                  {"title": "Mathrubhumi Study Circle logo", "author": "Mathrubhumi", "date": "",
                                   "license": "Trademark of Mathrubhumi", "pad": (1200, 600, "white")}),
    "vincent-de-paul-portrait":  (f"{H}/communites/1650-vincent-de-paul-portrait-simon-francois-de-tours.jpg", (0, 220, 1395, 1120),
                                  {"note": "Cropped."}),
    "aranattukara-logo":       (f"{P}/logo/aka-logo.jpeg", (178, 18, 1038, 878),
                                  dict(OWN, title="The aranattukara.org logo", date="2026-11-01")),
    "st-aloysius-college":       (f"{N}/places/st-aloysius-college/st-aloysius-college-elthuruth-2019.jpg", None, {}),
    "lalur-trenching-ground-2010": (f"{N}/lalur/2010-lalur-trenching-ground-through-broken-wall.jpg", None, {}),
    "lalur-waste-dump-2012":     (f"{N}/lalur/2012-lalur-waste-dump.jpg", None, {}),
    "lalur-waste-truck-2009":    (f"{N}/lalur/2009-lalur-waste-truck-on-the-way-to-the-dump.jpg", None, {}),
    "lalur-road-to-dump-2012":   (f"{N}/lalur/2012-lalur-road-to-dumping-yard-1.jpg", None, {}),
    "lalur-strike-2010":         (f"{N}/lalur/2010-lalur-war-against-waste-1.jpg", None, {}),
    "lalur-hunger-strike-2012":  (f"{N}/lalur/2012-lalur-k-venu-hunger-strike.jpg", None, {}),
    "lalur-sukumar-azhikode-2009": (f"{N}/lalur/2009-lalur-sukumar-azhikode-speaks.jpg", None, {}),
    "lalur-support-march-2012":  (f"{N}/lalur/2012-lalur-support-march-thrissur-round.jpg", None, {}),
    "council-1930-teacher":      (f"{H}/documents/1930-12-04-cochin-legislative-council-teacher-aranattukara-school-p1.jpg", None,
                                  dict(COUNCIL, title="Cochin Legislative Council proceedings, 4 Dec 1930", date="1930-12-04", page=IA + "1226187")),
    "council-1932-colony":       (f"{H}/documents/1932-12-01-cochin-legislative-council-aranattukara-depressed-class-colony.jpg", None,
                                  dict(COUNCIL, title="Cochin Legislative Council proceedings, 1 Dec 1932", date="1932-12-01", page=IA + "1250424")),
    "council-1935-trenching-ground": (f"{H}/documents/1935-12-11-cochin-legislative-council-trenching-ground-laloor-p1.jpg", None,
                                  dict(COUNCIL, title="Cochin Legislative Council proceedings, 11 Dec 1935", date="1935-12-11", page=IA + "1275372")),
    "council-1939-bazaar-road":  (f"{H}/documents/1939-03-30-cochin-legislative-council-road-toll-gate-to-aranattukara-bazaar-p1.jpg", None,
                                  dict(COUNCIL, title="Cochin Legislative Council proceedings, 30 Mar 1939", date="1939-03-30", page=IA + "1300464")),
    "council-1942-lalur-dump":   (f"{H}/documents/1942-05-26-cochin-legislative-council-dumping-ground-at-lalur-p1.jpg", None,
                                  dict(COUNCIL, title="Cochin Legislative Council proceedings, 26 May 1942", date="1942-05-26", page=IA + "1303071")),
    "council-1943-tharakans-school": (f"{H}/documents/1943-08-02-cochin-legislative-council-tharakans-lower-secondary-school-aranattukara.jpg", None,
                                  dict(COUNCIL, title="Cochin Legislative Council proceedings, 2 Aug 1943", date="1943-08-02", page=IA + "1303372")),
}
for _f, _name, _title in OWN_PHOTOS:
    ITEMS[_name] = (f"{PL}/{_f}", None, dict(OWN, title=_title))


LABELS = {  # short, readable titles for the credits page
    "kol-wetland-sunset": "Kol wetland near Thrissur at sunset",
    "kol-wetland-bund": "Kol wetland: bund path and channel",
    "kol-wetland-path": "Kol wetland: path through the paddy",
    "gould-plan-1816": "Plan of Trichur and its environs, 1816",
    "gould-plan-1816-aranaat": "Plan of Trichur, 1816 — detail of “Aranaat”",
    "map-travancore-cochin-1862": "Map of Travancore and Cochin, Church Missionary Atlas, 1862",
    "map-cochin-state-1941": "Map of Cochin State, Census of India 1941",
    "ams-map-1955-aranattukara": "US Army Map Service, sheet NC 43-7, 1955 — Trichur and Aranattukara",
    "st-thomas-church-feast-2025": "St. Thomas Church, Aranattukara, at the feast",
    "sakthan-thampuran-palace": "Sakthan Thampuran Palace, Thrissur",
    "sakthan-thampuran-tomb": "Tomb of Sakthan Thampuran, Thrissur",
    "adolph-medlycott-1890": "Bishop Adolph Medlycott, Vicar Apostolic of Trichur",
    "john-mathai-1949": "John Mathai (portrait crop)",
    "john-mathai-budget-1949": "John Mathai before his budget speech, 1949",
    "first-cabinet-1950": "India's first cabinet with President Rajendra Prasad, 1950",
    "jose-kattukkaran-2011": "Mayor Jose Kattukkaran speaking in Thrissur, 2011",
    "fr-antony-thachuparambil-mural": "Mural of Fr. Antony Thachuparambil, Kottat Church, Chalakudy",
    "chavara-stamp-1987": "St. Kuriakose Elias Chavara on a 1987 Indian stamp",
    "vincent-de-paul-portrait": "St. Vincent de Paul, portrait by Simon François de Tours",
    "st-aloysius-college": "St. Aloysius College, Elthuruth",
    "lalur-trenching-ground-2010": "Lalur trenching ground",
    "lalur-waste-dump-2012": "Waste beside houses at Lalur",
    "lalur-waste-truck-2009": "Waste on its way to Lalur",
    "lalur-road-to-dump-2012": "The road to the Lalur dumping yard",
    "lalur-strike-2010": "The Lalur strike",
    "lalur-hunger-strike-2012": "Hunger strike in support of the Lalur agitation",
    "lalur-sukumar-azhikode-2009": "Sukumar Azhikode at the Lalur strike",
    "lalur-support-march-2012": "March in support of the Lalur struggle, Thrissur Round",
}


def yq(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


only = set(sys.argv[1:])
lines = ["# Picture credits — generated by tools/build-images.py. Do not edit by hand;",
         "# change ITEMS in that script and run it again.", ""]
for name, (src, box, extra) in ITEMS.items():
    m = meta.get(extra.get("meta_from", src), {})
    if not only or name in only:
        work = src
        im = Image.open(src)
        if box or extra.get("pad") or im.getexif().get(274, 1) != 1:
            work = os.path.join(TMP, name + ".jpg")
            im = ImageOps.exif_transpose(im).convert("RGB")
            im = im.crop(box) if box else im
            if extra.get("pad"):        # (width, height, colour): centre a logo on a wide canvas
                w, h, colour = extra["pad"]
                im.thumbnail((w, int(h * .85)))
                canvas = Image.new("RGB", (w, h), colour)
                canvas.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
                im = canvas
            im.save(work, quality=95)
        subprocess.run([os.path.join(SITE, "tools", "optimize-images.sh"), work, name], check=True)
    lic = extra.get("license") or m.get("license", "")
    page = extra.get("page") or m.get("page", "")
    title = extra.get("title") or m.get("title", "").removeprefix("File:").rsplit(".", 1)[0] \
        or urllib.parse.unquote(page.rsplit("File:", 1)[-1]).replace("_", " ").rsplit(".", 1)[0]
    date = re.sub(r"\s*\(.*?\)", "", extra.get("date") or m.get("date", "")).strip()
    if re.match(r"(?i)prior|unknown|before", date):
        date = ""
    date = re.sub(r"^(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}(:\d{2})?$", r"\1", date)
    if name in LABELS:
        title = LABELS[name]
    author = (extra.get("author") or m.get("author") or "Unknown").strip()
    half = len(author) // 2
    if len(author) % 2 == 0 and author[:half] == author[half:]:
        author = author[:half]          # Commons sometimes repeats the creator text
    lines += [f"{name}:",
              f"  title: {yq(title)}",
              f"  author: {yq(author)}",
              f"  date: {yq(date)}",
              f"  license: {yq(lic)}",
              f"  license_url: {yq(LIC.get(lic, m.get('license_url', '')))}",
              f"  source: {yq(extra.get('page') or m.get('page', ''))}",
              f"  note: {yq(extra.get('note', ''))}", ""]
open(os.path.join(SITE, "_data", "credits.yml"), "w").write("\n".join(lines))
print("wrote _data/credits.yml with", len(ITEMS), "entries")
