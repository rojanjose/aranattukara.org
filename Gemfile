source "https://rubygems.org"

# Same Jekyll + plugin versions GitHub Pages uses in production (Jekyll 3.10).
gem "github-pages", group: :jekyll_plugins

# Needed for `jekyll serve` on Ruby 3+, and for older gems on Ruby 3.4+/4.x,
# where these left the default standard library. Harmless on GitHub's Ruby 3.3.
gem "webrick"
gem "csv"
gem "base64"
gem "bigdecimal"
gem "logger"
gem "ostruct"

# Ruby 3.2+ removed Object#tainted?, which Liquid 4.0.3 still calls. Local preview only.
require_relative "tools/ruby4-compat" if RUBY_VERSION >= "3.2"
