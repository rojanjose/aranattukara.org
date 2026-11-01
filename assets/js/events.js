// Time-dependent content, decided in the browser at view time (technical-spec D11):
// a static build only knows the date it was built, so lists would go stale.
//  - [data-event][data-end="YYYY-MM-DD"]: hidden once the end date has passed
//    (on an event's own page, the "this event has passed" note is shown instead)
//  - [data-upcoming][data-limit]: shows the first N upcoming items, or the empty note
//  - [data-on-this-day]: highlights timeline entries whose month/day is today
(function () {
  "use strict";
  var now = new Date();
  var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  function ended(el) {
    var d = (el.getAttribute("data-end") || "").split("-");
    if (d.length !== 3) return false;
    return new Date(+d[0], +d[1] - 1, +d[2]) < today;
  }

  document.querySelectorAll("[data-event]").forEach(function (el) {
    if (!ended(el)) return;
    if (el.classList.contains("event-page")) {
      var note = el.querySelector(".event-past-note"); if (note) note.hidden = false;
    } else {
      el.hidden = true; el.setAttribute("data-past", "");
    }
  });

  document.querySelectorAll("[data-upcoming]").forEach(function (box) {
    var limit = +(box.getAttribute("data-limit") || 0);
    var shown = 0;
    box.querySelectorAll("[data-event]:not([data-past])").forEach(function (el) {
      shown += 1;
      if (limit && shown > limit) el.hidden = true;
    });
    var empty = box.querySelector("[data-empty]");
    if (empty) empty.hidden = shown > 0;
  });

  document.querySelectorAll("[data-on-this-day] [data-md]").forEach(function (li) {
    var md = (now.getMonth() + 1) + "-" + now.getDate();
    if (li.getAttribute("data-md") === md) li.classList.add("today");
  });
})();
