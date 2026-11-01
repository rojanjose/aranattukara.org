// Small site behaviours: mobile menu, remembered language, copy-link, then/now slider, chip filters.
(function () {
  "use strict";

  // Mobile menu
  var btn = document.querySelector("[data-menu-toggle]");
  var nav = document.getElementById("main-nav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) { nav.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); btn.focus(); }
    });
  }

  // Remember the reader's language choice (read by the root redirect)
  document.querySelectorAll(".lang-switch a[data-lang]").forEach(function (a) {
    a.addEventListener("click", function () {
      try { localStorage.setItem("ak-lang", a.getAttribute("data-lang")); } catch (e) {}
    });
  });
  try { localStorage.setItem("ak-lang", (window.AK && AK.lang) || "en"); } catch (e) {}

  // Copy link
  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var url = b.getAttribute("data-copy"), label = b.textContent;
      function done() { b.textContent = b.getAttribute("data-copied"); setTimeout(function () { b.textContent = label; }, 1800); }
      if (navigator.share && /Mobi/.test(navigator.userAgent)) { navigator.share({ url: url, title: document.title }).catch(function () {}); return; }
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () {});
    });
  });

  // Then & now comparison slider
  document.querySelectorAll("[data-compare]").forEach(function (c) {
    var r = c.querySelector(".compare-range");
    if (!r) return;
    function set() { c.style.setProperty("--pos", r.value + "%"); }
    r.addEventListener("input", set); set();
  });

  // Chip filters: <ul class="chips" data-filter="target-selector"> with buttons data-value;
  // items carry data-cat. "all" shows everything.
  document.querySelectorAll("[data-filter]").forEach(function (group) {
    var items = document.querySelectorAll(group.getAttribute("data-filter"));
    group.addEventListener("click", function (e) {
      var chip = e.target.closest("button[data-value]");
      if (!chip) return;
      group.querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-pressed", b === chip ? "true" : "false"); });
      var v = chip.getAttribute("data-value");
      items.forEach(function (it) { it.hidden = v !== "all" && (it.getAttribute("data-cat") || "").split(" ").indexOf(v) === -1; });
      document.dispatchEvent(new CustomEvent("ak:filter", { detail: { value: v } }));
    });
  });
})();
