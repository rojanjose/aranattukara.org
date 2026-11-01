# Local-preview shim only (loaded from the Gemfile). Liquid 4.0.3 (pinned by the github-pages gem) calls
# Object#tainted?/taint/untaint, which Ruby 3.2+ removed. GitHub Pages builds on
# Ruby 3.3 and does not use this Gemfile, so this never runs in production.
# Delete it if you preview with Ruby 3.1 (e.g. `brew install ruby@3.1`).
class Object
  def tainted?; false; end unless method_defined?(:tainted?)
  def taint; self; end unless method_defined?(:taint)
  def untaint; self; end unless method_defined?(:untaint)
end
