"""Make the site's logo files from the master in ../specs/pictures/logo/aka-logo.jpeg.

    python3 tools/build-logo.py            (run from site/; needs Pillow)

Writes to assets/img/:
  logo-mark-{128,256}.png   the whole emblem cut round, for the header
  logo-{180,192,512}.png    the whole emblem on its paper background (home-screen icons)
  logo-{480,960}.webp       the whole emblem cut round (transparent corners), for pages
  logo-share.jpg            1200 × 630 card for link previews (og:image)
"""
import os
from PIL import Image, ImageDraw

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(SITE, "..", "specs", "pictures", "logo", "aka-logo.jpeg")
OUT = os.path.join(SITE, "assets", "img")
PAPER = (247, 241, 222)                      # the logo's own background colour

src = Image.open(SRC).convert("RGB")
emblem = src.crop((178, 18, 1038, 878))      # the whole round emblem, square


def round_mask(im):
    big = im.resize((im.width * 4, im.height * 4), Image.LANCZOS)
    m = Image.new("L", big.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, big.width - 1, big.height - 1), fill=255)
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    out.paste(big, (0, 0), m)
    return out


for s in (180, 192, 512):
    emblem.resize((s, s), Image.LANCZOS).quantize(256).save(os.path.join(OUT, f"logo-{s}.png"), optimize=True)
emblem_round = round_mask(emblem)
for s in (128, 256):
    emblem_round.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, f"logo-mark-{s}.png"), optimize=True)
for s in (480, 960):
    emblem_round.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, f"logo-{s}.webp"), quality=82)

card = Image.new("RGB", (1200, 630), PAPER)
e = emblem.resize((580, 580), Image.LANCZOS)
card.paste(e, ((1200 - 580) // 2, 25))
card.save(os.path.join(OUT, "logo-share.jpg"), quality=85, optimize=True)

for f in sorted(os.listdir(OUT)):
    if f.startswith("logo-"):
        print(f"{f:22} {os.path.getsize(os.path.join(OUT, f)) // 1024} KB")
