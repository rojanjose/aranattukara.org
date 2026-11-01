# Translation check (technical-spec §6.6).
#   ruby tools/check-pairs.rb
# Lists English pages without a Malayalam version (and the reverse), and pairs whose
# language-independent front matter disagrees (dates, coordinates, photos, tags…).
require "yaml"
require "date"

ROOT = File.expand_path("..", __dir__)
SHARED = %w[date end_date coords type walk_stop photos photo hero poster places people themes era series order kind festivals place years].freeze

def front_matter(path)
  text = File.read(path)
  return {} unless text.start_with?("---")
  YAML.safe_load(text.split(/^---\s*$/, 3)[1], permitted_classes: [Date, Time], aliases: true) || {}
rescue Psych::Exception => e
  warn "YAML error in #{path}: #{e.message}"
  {}
end

# language folders: collections (_x/en, _x/ml) and plain pages (en/, ml/)
roots = Dir.glob(File.join(ROOT, "_*/en")).reject { |d| d.include?("/_site/") }.map { |d| [d, d.sub(%r{/en\z}, "/ml")] }
roots << [File.join(ROOT, "en"), File.join(ROOT, "ml")]

missing_ml, missing_en, mismatched = [], [], []
roots.each do |en_dir, ml_dir|
  en = Dir.glob("**/*.{md,html}", base: en_dir).sort
  ml = Dir.glob("**/*.{md,html}", base: ml_dir).sort
  rel = ->(dir, f) { File.join(dir, f).delete_prefix(ROOT + "/") }
  (en - ml).each { |f| missing_ml << rel.(en_dir, f) }
  (ml - en).each { |f| missing_en << rel.(ml_dir, f) }
  (en & ml).each do |f|
    a = front_matter(File.join(en_dir, f))
    b = front_matter(File.join(ml_dir, f))
    diffs = SHARED.select { |k| (a.key?(k) || b.key?(k)) && a[k] != b[k] }
    mismatched << "#{rel.(en_dir, f)}  ↔  ml  (#{diffs.join(', ')})" unless diffs.empty?
  end
end

def report(title, list)
  puts "#{title}: #{list.empty? ? 'none' : list.size}"
  list.each { |l| puts "  - #{l}" }
end

report("Missing Malayalam version", missing_ml)
report("Missing English version", missing_en)
report("Shared fields that differ", mismatched)
exit(mismatched.empty? ? 0 : 1)
