#!/bin/sh
# Make web-sized copies of a photo for the site (technical-spec §9.1).
#
#   tools/optimize-images.sh <original-photo> <base-name>
#   tools/optimize-images.sh ~/Drive/Aranattukara/originals/church-1965.jpg st-thomas-1965
#
# Writes assets/img/<base-name>-480.webp, -960.webp, -1600.webp and -960.jpg,
# then reference it in front matter as `hero: st-thomas-1965` (no path, no extension).
# Originals stay OUT of the repo. Location and camera data are removed.
# Needs: sips (built into macOS) and cwebp (`brew install webp`).
set -eu

src="${1:?usage: optimize-images.sh <original> <base-name>}"
name="${2:?usage: optimize-images.sh <original> <base-name>}"
out="$(cd "$(dirname "$0")/.." && pwd)/assets/img"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

case "$name" in *[!a-z0-9-]*) echo "base-name must be lowercase letters, digits and hyphens: $name" >&2; exit 1;; esac
command -v cwebp >/dev/null || { echo "cwebp not found — brew install webp" >&2; exit 1; }

# Normalise to an sRGB JPEG master; sips rewrites the file, dropping GPS and most EXIF.
sips -s format jpeg -s formatOptions 92 --matchTo "/System/Library/ColorSync/Profiles/sRGB Profile.icc" \
  "$src" --out "$tmp/master.jpg" >/dev/null

for w in 480 960 1600; do
  sips -Z "$w" "$tmp/master.jpg" --out "$tmp/$w.jpg" >/dev/null
  cwebp -quiet -q 78 -metadata none "$tmp/$w.jpg" -o "$out/$name-$w.webp"
done
sips -s formatOptions 80 "$tmp/960.jpg" --out "$out/$name-960.jpg" >/dev/null

total=$(du -ck "$out/$name"-*.webp "$out/$name-960.jpg" | tail -1 | cut -f1)
echo "wrote $out/$name-{480,960,1600}.webp and -960.jpg (${total} KB total)"
[ "$total" -le 350 ] || echo "note: over the 350 KB per-photo budget — consider a tighter crop" >&2
