// Leaflet + OpenStreetMap (technical-spec D10). Two uses:
//  - [data-map-mini]: one marker on a place page
//  - #map-full[data-places]: all places from /places.json, filter chips, heritage-walk route
(function () {
  "use strict";
  if (!window.L) return;
  var TILES = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  var ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
  var COLORS = { church: "#B5532E", chapel: "#B5532E", convent: "#B5532E", temple: "#C99A2E", school: "#3D6A84", landmark: "#2F5D3A", "lost-place": "#6E695F" };
  L.Icon.Default.imagePath = (window.AK ? AK.root : "/") + "assets/vendor/leaflet/images/";

  function pin(type) {
    var c = COLORS[type] || "#2F5D3A";
    return L.divIcon({
      className: "ak-pin", iconSize: [28, 38], iconAnchor: [14, 37], popupAnchor: [0, -32],
      html: '<svg viewBox="0 0 28 38" width="28" height="38"><path d="M14 37C5 25 1 19 1 13a13 13 0 0 1 26 0c0 6-4 12-13 24Z" fill="' + c + '" stroke="#fff" stroke-width="2"/><circle cx="14" cy="13" r="5" fill="#fff"/></svg>'
    });
  }

  document.querySelectorAll("[data-map-mini]").forEach(function (el) {
    var lat = +el.getAttribute("data-lat"), lng = +el.getAttribute("data-lng");
    el.innerHTML = "";
    var m = L.map(el, { scrollWheelZoom: false, attributionControl: true }).setView([lat, lng], 16);
    L.tileLayer(TILES, { maxZoom: 19, attribution: ATTR }).addTo(m);
    L.marker([lat, lng], { icon: pin("landmark") }).addTo(m).bindTooltip(el.getAttribute("data-title"));
  });

  // Ward boundaries (assets/data/wards.geojson, from OpenStreetMap).
  // role "core" = the wards Aranattukara spans; "neighbour" = the wards around them.
  var WARD_STYLE = {
    "51": { color: "#2F5D3A", weight: 3, fillColor: "#5E8C5A", fillOpacity: .28 },
    "50": { color: "#B5532E", weight: 3, fillColor: "#C99A2E", fillOpacity: .24 },
    neighbour: { color: "#6E695F", weight: 1.5, dashArray: "5 6", fillOpacity: 0 }
  };
  function wardLayer(geo, opts) {
    var lang = window.AK ? AK.lang : "en";
    return L.geoJSON(geo, {
      filter: function (f) { return !opts.coreOnly || f.properties.role === "core"; },
      style: function (f) {
        var s = WARD_STYLE[f.properties.role === "core" ? String(f.properties.ward) : "neighbour"];
        return opts.faint ? { color: s.color, weight: 2, dashArray: "4 6", fillOpacity: .05, fillColor: s.fillColor || s.color } : s;
      },
      onEachFeature: function (f, layer) {
        var p = f.properties, name = lang === "ml" ? p.name_ml : p.name;
        // Names only: ward numbers changed in 2025, so the key and the page text carry them.
        if (opts.labels) layer.bindTooltip(name, { permanent: true, direction: "center", className: "ward-label ward-label-" + p.role });
        else layer.bindTooltip(name, { sticky: true });
      }
    });
  }

  document.querySelectorAll("[data-map-wards]").forEach(function (el) {
    var m = L.map(el, { scrollWheelZoom: false, zoomSnap: 0.25 }).setView([10.513, 76.197], 14);
    L.tileLayer(TILES, { maxZoom: 19, attribution: ATTR + " · Ward boundaries: OSM (ODbL)" }).addTo(m);
    fetch(el.getAttribute("data-map-wards")).then(function (r) { return r.json(); }).then(function (geo) {
      var all = wardLayer(geo, { labels: true }).addTo(m);
      all.eachLayer(function (l) { if (l.feature.properties.role === "core") l.bringToFront(); });
      m.invalidateSize();
      m.fitBounds(all.getBounds(), { padding: [4, 4] });
    }).catch(function () {});
  });

  var full = document.getElementById("map-full");
  if (!full) return;
  var map = L.map(full, { scrollWheelZoom: true }).setView([10.512, 76.199], 15);
  L.tileLayer(TILES, { maxZoom: 19, attribution: ATTR }).addTo(map);
  if (full.getAttribute("data-wards")) {
    fetch(full.getAttribute("data-wards")).then(function (r) { return r.json(); }).then(function (geo) {
      wardLayer(geo, { coreOnly: true, faint: true }).addTo(map).bringToBack();
    }).catch(function () {});
  }
  var layers = [], walk = null;

  fetch(full.getAttribute("data-places")).then(function (r) { return r.json(); }).then(function (places) {
    var lang = window.AK ? AK.lang : "en", stops = [];
    places.forEach(function (p) {
      if (!p.coords) return;
      var title = (lang === "ml" && p.title_ml) ? p.title_ml : p.title;
      var url = (lang === "ml" && p.url_ml) ? p.url_ml : p.url;
      var mk = L.marker(p.coords, { icon: pin(p.type) }).bindPopup('<div class="map-popup"><strong></strong><a></a></div>');
      mk.on("popupopen", function (e) {
        var n = e.popup.getElement(); n.querySelector("strong").textContent = title;
        var a = n.querySelector("a"); a.href = url; a.textContent = (lang === "ml" ? "കൂടുതൽ" : "Read more") + " →";
      });
      mk._type = p.type; mk._walk = !!p.walk_stop;
      mk.addTo(map); layers.push(mk);
      if (p.walk_stop) stops.push([p.walk_stop, p.coords]);
    });
    stops.sort(function (a, b) { return a[0] - b[0]; });
    if (stops.length > 1) walk = L.polyline(stops.map(function (s) { return s[1]; }), { color: "#B5532E", weight: 4, dashArray: "8 10" }).addTo(map);
    if (layers.length) map.fitBounds(L.featureGroup(layers).getBounds().pad(0.3), { maxZoom: 16 });
  }).catch(function () {});

  document.addEventListener("ak:filter", function (e) {
    var v = e.detail.value;
    layers.forEach(function (mk) {
      var show = v === "all" || mk._type === v || (v === "walk" && mk._walk);
      if (show) mk.addTo(map); else map.removeLayer(mk);
    });
    if (walk) { if (v === "all" || v === "walk") walk.addTo(map); else map.removeLayer(walk); }
  });
})();
