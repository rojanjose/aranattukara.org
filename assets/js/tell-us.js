/* The site's "Tell us" form: fills in the page the reader came from, checks the
   answers, posts them into a hidden frame and shows a thank-you message. */
(function () {
  var form = document.querySelector("[data-tell-us]");
  if (!form) return;
  var thanks = document.querySelector("[data-tell-us-thanks]");
  var sink = document.querySelector("iframe[name=tell-us-sink]");
  var page = form.querySelector("#tu-page");
  var sent = false;
  var timer;

  // ?page=<url> from a "Tell us" button fills in which page this is about.
  try {
    var p = new URLSearchParams(location.search).get("page");
    if (p && page && !page.value) page.value = p;
  } catch (e) { /* old browser: leave it empty */ }

  function show(name, on) {
    var el = form.querySelector('[data-error="' + name + '"]');
    if (el) el.hidden = !on;
  }

  form.addEventListener("change", function (e) {
    if (e.target.closest(".tu-kind")) show("kind", false);
  });

  form.addEventListener("submit", function (e) {
    var kinds = form.querySelectorAll('.tu-kind input[type=checkbox]:checked');
    if (!kinds.length) {
      e.preventDefault();
      show("kind", true);
      form.querySelector(".tu-kind input").focus();
      return;
    }
    show("send", false);
    sent = true;
    form.querySelector("button[type=submit]").disabled = true;
    // If the frame never loads (offline, blocked), say so after a while.
    timer = setTimeout(function () {
      if (!sent) return;
      sent = false;
      form.querySelector("button[type=submit]").disabled = false;
      show("send", true);
    }, 20000);
  });

  sink.addEventListener("load", function () {
    if (!sent) return;
    sent = false;
    clearTimeout(timer);
    form.reset();
    form.querySelector("button[type=submit]").disabled = false;
    form.hidden = true;
    thanks.hidden = false;
    thanks.focus();
  });

  var again = document.querySelector("[data-tell-us-again]");
  if (again) again.addEventListener("click", function () {
    thanks.hidden = true;
    form.hidden = false;
    form.querySelector("input").focus();
  });
})();
