// [HEDI] ContrailWatch interface.
// Flow: ask the API for a Snapshot -> draw one dot per plane -> click a dot -> details panel.

const COLORS = { grey: "#9aa0a6", orange: "#f29d38", green: "#2e9e6b", purple: "#7b5cd6" };

// 1. The map, centred on the BBOX (Gulf of St. Lawrence, Newfoundland, Labrador).
const map = L.map("map").setView([50, -64], 5);
// OpenStreetMap tiles (the CARTO dark tiles are blocked on the venue network).
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "© OpenStreetMap contributors",
}).addTo(map);
const planeLayer = L.layerGroup().addTo(map);

// 2. The colour of a plane, from the physics result and Jev's decision.
function planeColor(assessment, decision) {
  if (!assessment || !assessment.flagged) return COLORS.grey;   // no persistent contrail
  if (!decision) return COLORS.orange;                          // flagged, no decision yet
  return decision.route === "auto" ? COLORS.green : COLORS.purple;
}

// 3. Ask the API for data, then redraw everything.
async function refresh() {
  const threshold = document.getElementById("threshold").value;
  const res = await fetch(`/api/snapshot?mode=replay&threshold=${threshold}`);
  const snap = await res.json();

  // Index the lists by plane id (icao24) to join them easily.
  const byId = (list) => Object.fromEntries(list.map((x) => [x.icao24, x]));
  const assessments = byId(snap.assessments);
  const decisions = byId(snap.decisions);
  const advisories = byId(snap.advisories);

  document.getElementById("mode").textContent = `mode: ${snap.mode} · ${snap.source || ""}`;
  planeLayer.clearLayers();
  for (const plane of snap.aircraft) {
    const a = assessments[plane.icao24], d = decisions[plane.icao24];
    L.circleMarker([plane.lat, plane.lon], {
      radius: 9, color: "#fff", weight: 1, fillColor: planeColor(a, d), fillOpacity: 0.95,
    })
      .bindTooltip(`${plane.callsign} · FL${plane.flight_level}`)
      .on("click", () => showPanel(plane, a, d, advisories[plane.icao24]))
      .addTo(planeLayer);
  }
  showReceipt(snap.receipt);
}

// 4. Details of one flight.
function showPanel(plane, a, d, adv) {
  const row = (label, lvl) => lvl
    ? `<tr><td>${label}</td><td>FL${lvl.flight_level}</td><td>${lvl.rh_ice_pct}%</td><td>${lvl.persistent ? "yes" : "no"}</td></tr>`
    : "";
  let html = `<h2>${plane.callsign}</h2>
    <p>FL${plane.flight_level} · heading ${plane.heading_deg}° · ${plane.speed_kt} kt</p>`;
  if (a) {
    html += `<table><tr><th>Option</th><th>Level</th><th>RHi</th><th>Contrail</th></tr>
      ${row("now", a.current)}${row("climb", a.climb)}${row("descend", a.descend)}</table>`;
    for (const opt of ["climb", "descend"]) {
      if (opt in a.net_benefit_co2e_kg) {
        html += `<p>${opt}: +${a.fuel_penalty_kg[opt]} kg fuel → net benefit <b>${a.net_benefit_co2e_kg[opt]} kg CO₂e</b></p>`;
      }
    }
  }
  if (d) {
    const by = { jev: "Jev", rule: "fallback rule (Jev unavailable)", physics: "physics: no beneficial option, no Jev call" };
    html += `<p class="decision">Decision: <b>${d.action}</b> · confidence ${d.confidence}
      → ${d.route === "auto" ? "sent automatically" : "Sophie reviews"}<br><small>decided by: ${by[d.decided_by] || d.decided_by}</small></p>`;
  }
  if (adv) html += `<blockquote>${adv.text}<br><small>written by: ${adv.written_by}</small></blockquote>`;
  document.getElementById("panel").innerHTML = html;
}

// 5. The compute receipt.
function showReceipt(r) {
  document.getElementById("receipt").textContent =
    `Compute receipt · ${r.aircraft_scanned} planes scanned · ${r.flagged_by_physics} flagged by physics · ` +
    `${r.physics_ms} ms physics · ${r.weather_calls} weather call(s), ${r.weather_cache_hits} cache hit(s) · ${r.jev_calls} Jev call(s) · ` +
    `${r.latency_ms} ms total · ` +
    `${r.local_llm_calls} Granite · ${r.llm_calls} Claude · ${(r.llm_energy_wh + r.local_llm_energy_wh).toFixed(2)} Wh · $${r.cost_usd}`;
}

// 6. The slider: show the value and reload the data.
document.getElementById("threshold").addEventListener("input", (e) => {
  document.getElementById("threshold-value").textContent = Number(e.target.value).toFixed(2);
  refresh();
});

refresh();
