// Client-side search over the Liquid-generated /search-<lang>.json index.
// Plain substring matching, case- and accent-insensitive: works for Malayalam,
// where English word-stemming search libraries do poorly (technical-spec §8.3).
(function () {
  "use strict";
  var dialog = document.getElementById("search");
  var input = document.getElementById("search-input");
  var list = document.getElementById("search-results");
  if (!dialog || !input || !list) return;
  var index = null, lastFocus = null;

  function norm(s) { return (s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, ""); }

  function load() {
    if (index) return Promise.resolve(index);
    return fetch(input.getAttribute("data-index")).then(function (r) { return r.json(); }).then(function (d) {
      index = d.map(function (x) { x._t = norm(x.title); x._all = norm([x.title, x.summary, x.keywords].join(" ")); return x; });
      return index;
    });
  }

  function render(q) {
    q = norm(q.trim());
    list.innerHTML = "";
    if (!q) return;
    var words = q.split(/\s+/);
    var hits = index.filter(function (x) { return words.every(function (w) { return x._all.indexOf(w) !== -1; }); })
      .sort(function (a, b) { return (b._t.indexOf(q) !== -1) - (a._t.indexOf(q) !== -1); })
      .slice(0, 12);
    if (!hits.length) { list.innerHTML = '<li class="none">' + input.getAttribute("data-none") + "</li>"; return; }
    hits.forEach(function (x) {
      var li = document.createElement("li"), a = document.createElement("a");
      a.href = x.url;
      a.innerHTML = '<span class="r-kind"></span><span class="r-title"></span><span class="r-sum"></span>';
      a.children[0].textContent = x.kind || "";
      a.children[1].textContent = x.title;
      a.children[2].textContent = x.summary || "";
      li.appendChild(a); list.appendChild(li);
    });
  }

  function open() {
    lastFocus = document.activeElement;
    dialog.hidden = false; document.body.style.overflow = "hidden";
    input.focus();
    load().then(function () { render(input.value); }).catch(function () {});
  }
  function close() {
    dialog.hidden = true; document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }

  document.querySelectorAll("[data-search-open]").forEach(function (b) { b.addEventListener("click", open); });
  dialog.querySelector("[data-search-close]").addEventListener("click", close);
  dialog.addEventListener("click", function (e) { if (e.target === dialog) close(); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !dialog.hidden) close();
    if (e.key === "/" && dialog.hidden && !/input|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); open(); }
  });
  input.addEventListener("input", function () { if (index) render(input.value); });
  if (location.hash === "#search") open();
})();
