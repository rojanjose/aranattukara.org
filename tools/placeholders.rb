# Placeholder pictures + the list of photos still needed.
#
#   ruby tools/placeholders.rb
#
# 1. Finds every picture name the site uses (front matter hero/photo/photos/poster,
#    figure includes in text, home-page settings, _data/gallery.yml).
# 2. For each name with no real photo in assets/img/ (no <name>-960.jpg), writes
#    assets/img/<name>.svg: an illustration chosen by keyword + a "Photo to come" label.
#    (The img include prefers the .svg, so delete it when the real photo arrives.)
# 3. Writes ../specs/pictures/NEEDED.md: every missing photo, what to shoot (from the
#    `needs:` front matter), which pages use it, and the file name to deliver.
require "yaml"
require "date"
require "set"

SITE = File.expand_path("..", __dir__)
IMG = File.join(SITE, "assets/img")
SCENES = File.join(__dir__, "placeholder-scenes")
OUT = File.expand_path("../specs/pictures/NEEDED.md", SITE)

def front_matter(path)
  text = File.read(path)
  return [{}, text] unless text.start_with?("---")
  _, fm, body = text.split(/^---\s*$/, 3)
  [YAML.safe_load(fm, permitted_classes: [Date, Time], aliases: true) || {}, body || ""]
rescue Psych::Exception => e
  warn "YAML error in #{path}: #{e.message}"
  [{}, ""]
end

def url_for(path)
  rel = path.delete_prefix(SITE + "/")
  if (m = rel.match(%r{\A_(\w+)/(en|ml)/(.+)\.md\z}))
    coll = { "orgs" => "community" }.fetch(m[1], m[1])
    "/#{m[2]}/#{coll}/#{m[3]}/"
  else
    "/" + rel.sub(/(index)?\.(md|html)\z/, "").sub(%r{/\z}, "") + "/"
  end
end

uses = Hash.new { |h, k| h[k] = Set.new }      # name => pages
briefs = {}                                    # name => brief
titles = {}                                    # page url => title
files = Dir.glob(File.join(SITE, "{_stories,_places,_people,_orgs,_events}/{en,ml}/*.md")) +
        Dir.glob(File.join(SITE, "{en,ml}/**/*.{md,html}"))
files.each do |f|
  fm, body = front_matter(f)
  url = url_for(f)
  titles[url] = fm["title"]
  names = []
  %w[hero photo poster then_image now_image map_image].each { |k| names << fm[k] if fm[k].is_a?(String) }
  names.concat(Array(fm["photos"]))
  Array(fm["explore"]).each { |c| names << c["image"] if c.is_a?(Hash) }
  body.scan(/include\s+(?:figure|img)\.html\s+name="([^"]+)"/) { |(n)| names << n }
  names.compact.each { |n| uses[n] << url }
  Array(fm["needs"]).each { |n| briefs[n["name"]] ||= n["brief"] if n.is_a?(Hash) }
end
(YAML.load_file(File.join(SITE, "_data/gallery.yml")) || []).each { |g| uses[g["image"]] << "/en/gallery/" } if File.exist?(File.join(SITE, "_data/gallery.yml"))

real = ->(n) { File.exist?(File.join(IMG, "#{n}-960.jpg")) }
missing = uses.keys.reject { |n| real.(n) }.sort

SCENE_RULES = [
  [/portrait|people|person|fr-|bishop|saint|st-euphrasia|chavara|master|antony|mathai|tharakan-portrait|sakthan-thampuran-portrait|kattukkaran|chiramel|medlycott/, "portrait"],
  [/feast|perunnal|procession|lights|christmas|onam|festival/, "perunnal-poster"],
  [/drama|stage|theatre|arts|painting|club/, "perunnal-poster"],
  [/temple|kavu|pooja/, "lalur-temple"],
  [/church|chapel|convent|ashram|cross|nagari/, "st-thomas-church"],
  [/school|college|centre|center|class|library/, "tharakans-school"],
  [/bakery|shop|bazaar|market|factory|foundry|industry|business|mill|tile|junction|road|street/, "market-street"],
  [/canal|landing|warehouse|toll|port|kadavu|boat|water/, "port-canoes"],
  [/house|tharavadu|home|antique/, "then-now-then"],
  [/kol|wetland|field|paddy|environment|plant|egret|green/, "kol-wetland"],
  [/map/, "map-teaser"],
]
LABEL = <<~SVG
  <g transform="translate(%<x>d,%<y>d)">
    <rect width="%<w>d" height="%<h>d" rx="%<r>d" fill="#FAF7F0" fill-opacity=".92"/>
    <g transform="translate(%<pad>d,%<cy>d)" fill="none" stroke="#2F5D3A" stroke-width="%<sw>s" stroke-linejoin="round">
      <rect x="0" y="%<iy>s" width="%<iw>s" height="%<ih>s" rx="%<ir>s"/>
      <circle cx="%<icx>s" cy="0" r="%<icr>s"/>
    </g>
    <text x="%<tx>d" y="%<ty>d" font-family="Helvetica, Arial, sans-serif" font-size="%<fs>d" font-weight="700" fill="#2F5D3A">Photo to come</text>
  </g>
SVG

made = 0
missing.each do |n|
  scene = SCENE_RULES.find { |re, _| n =~ re }&.last || "hero-kol"
  svg = File.read(File.join(SCENES, "#{scene}.svg"))
  w, h = svg[/viewBox="0 0 (\d+) (\d+)"/, 1].to_i, svg[/viewBox="0 0 (\d+) (\d+)"/, 2].to_i
  s = [w, h].min / 1000.0
  fs = (44 * s).round; lh = (fs * 2.1).round; lw = (fs * 9.2).round; pad = (fs * 0.6).round
  label = format(LABEL, x: (w - lw - 30 * s).round, y: (h - lh - 30 * s).round, w: lw, h: lh, r: (lh / 2.0).round,
                 pad: pad, cy: lh / 2, sw: (3.2 * s).round(1), iy: -(fs * 0.42).round(1), iw: (fs * 1.2).round(1),
                 ih: (fs * 0.84).round(1), ir: (fs * 0.16).round(1), icx: (fs * 0.6).round(1), icr: (fs * 0.24).round(1),
                 tx: pad + (fs * 1.6).round, ty: (lh / 2 + fs * 0.36).round, fs: fs)
  File.write(File.join(IMG, "#{n}.svg"), svg.sub(%r{</svg>\s*\z}, label + "</svg>\n"))
  made += 1
end
# remove placeholders that now have a real photo, or are no longer used
Dir.glob(File.join(IMG, "*.svg")).each do |f|
  n = File.basename(f, ".svg")
  next if n == "favicon"
  File.delete(f) if real.(n) || !uses.key?(n)
end

# ---- NEEDED.md -------------------------------------------------------------------
groups = {
  "People (portraits)" => /portrait|people|fr-|bishop|saint|euphrasia|chavara|master|mathai|kattukkaran|chiramel|sakthan/,
  "Places of worship" => /church|chapel|temple|convent|ashram|kavu|nagari|feast|perunnal/,
  "Schools and institutions" => /school|college|centre|library/,
  "Then & now, landmarks and lost places" => /landing|warehouse|toll|canal|house|tharavadu|aranaat|then|now|site|bazaar|road|junction/,
}
grouped = Hash.new { |hh, k| hh[k] = [] }
missing.each { |n| grouped[groups.find { |_, re| n =~ re }&.first || "Everyday life, work and the landscape"] << n }

lines = ["# Pictures needed for aranattukara.org", "",
         "Generated by `site/tools/placeholders.rb` on #{Date.today} — run it again after adding content or photos.", "",
         "The draft site shows an illustration marked **“Photo to come”** wherever a photo below is missing.",
         "There are **#{missing.size} photos** to take or find.", "",
         "## How to deliver a photo", "",
         "1. Name the file after the **file name** column (any extension), e.g. `ph-st-marys-chapel.jpg`.",
         "2. Landscape, at least **2400 px** wide (portraits: upright, at least 1200 px), sharp, in daylight unless noted.",
         "3. Tell me who took it, and confirm you have permission to publish it (and consent from people in it).",
         "4. I run `tools/optimize-images.sh` and the placeholder disappears; the credit goes into `_data/credits.yml`.", ""]
(groups.keys + ["Everyday life, work and the landscape"]).each do |g|
  next if grouped[g].empty?
  lines += ["## #{g}", "", "| File name | What to photograph | Used on |", "|---|---|---|"]
  grouped[g].each do |n|
    pages = uses[n].select { |u| u.start_with?("/en/") }.sort.map { |u| "[#{titles[u] || u}](#{u})" }
    pages = uses[n].sort.map { |u| "[#{titles[u] || u}](#{u})" } if pages.empty?
    lines << "| `#{n}` | #{briefs[n] || n.delete_prefix('ph-').tr('-', ' ').capitalize} | #{pages.join(', ')} |"
  end
  lines << ""
end
lines += ["## Also missing", "",
          "- **Map coordinates** for places without a pin (see each place page) — a phone GPS reading at the gate is enough.",
          "- **Higher-resolution scans** of two historical maps: the British Library original of John Gould's 1816 plan of Trichur,",
          "  and the Perry–Castañeda Library scan of the 1955 US Army sheet NC 43-7.", ""]
File.write(OUT, lines.join("\n"))
puts "placeholders written: #{made} · photos needed: #{missing.size} · #{OUT.sub(File.expand_path('..', SITE) + '/', '')}"
