
const API_BASE = window.FOREST_API_BASE || "http://127.0.0.1:8000";

// const API_BASE = window.FOREST_API_BASE ||
//     (window.location.protocol === "http:" || window.location.protocol === "https:"
//         ? window.location.origin
//         : "http://127.0.0.1:8000");
const DEFAULT_CENTER = [10.7, 78.4];
const DEFAULT_ZOOM = 7;

const state = {
    map: null,
    layers: {},
    basemaps: {},
    active: {
        forestBase: false,
        heat: true,
        grid: false,
        prediction: true
    },
    recent: { type: "FeatureCollection", features: [] },
    predictions: [],
    summary: null,
    districts: null
};

const $ = (id) => document.getElementById(id);

function certaintyLabel(value) {
    const normalized = String(value || "").trim().toLowerCase();
    if (normalized === "h") return "high certainty";
    if (normalized === "n") return "medium certainty";
    if (normalized === "l") return "lower certainty";
    return "certainty not available";
}

function initMap() {
    state.map = L.map("map", { zoomControl: false }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.control.zoom({ position: "bottomleft" }).addTo(state.map);

    state.basemaps.light = L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap & CartoDB"
    }).addTo(state.map);

    state.basemaps.forest = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
        maxZoom: 19,
        attribution: "Tiles &copy; Esri"
    });

    state.basemaps.forestLabels = L.tileLayer("https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
        pane: "overlayPane",
        attribution: "&copy; OpenStreetMap & CartoDB"
    });

    state.layers.heat = null;
    state.layers.districts = L.layerGroup().addTo(state.map);
    state.layers.grid = L.layerGroup().addTo(state.map);
    state.layers.prediction = L.layerGroup().addTo(state.map);
}

function syncBasemap() {
    const usingForest = state.active.forestBase;

    if (usingForest) {
        if (state.map.hasLayer(state.basemaps.light)) state.map.removeLayer(state.basemaps.light);
        if (!state.map.hasLayer(state.basemaps.forest)) state.basemaps.forest.addTo(state.map);
        if (!state.map.hasLayer(state.basemaps.forestLabels)) state.basemaps.forestLabels.addTo(state.map);
    } else {
        if (state.map.hasLayer(state.basemaps.forest)) state.map.removeLayer(state.basemaps.forest);
        if (state.map.hasLayer(state.basemaps.forestLabels)) state.map.removeLayer(state.basemaps.forestLabels);
        if (!state.map.hasLayer(state.basemaps.light)) state.basemaps.light.addTo(state.map);
    }
}

async function fetchJson(path, fallback = null) {
    try {
        const response = await fetch(`${API_BASE}${path}`);
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.warn(`Failed to load ${path}`, error);
        return fallback;
    }
}

function setApiStatus(online) {
    const dot = $("apiDot");
    const label = $("apiLabel");
    if (!dot || !label) return;
    dot.classList.toggle("online", online);
    dot.classList.toggle("offline", !online);
    label.textContent = online ? "API connected" : "API unavailable";
}

function riskBand(value) {
    if (value >= 0.7) return "high";
    if (value >= 0.4) return "medium";
    return "low";
}

function riskColor(value) {
    const band = riskBand(value);
    if (band === "high") return "#cf3f22";
    if (band === "medium") return "#d7961f";
    return "#17633f";
}

function formatPercent(value) {
    return `${Math.round(value * 100)}%`;
}

function setText(id, value) {
    const el = $(id);
    if (el) el.textContent = value;
}

function syncLayerVisibility(key) {
    const layer = state.layers[key];
    if (!layer) return;
    if (state.active[key] && !state.map.hasLayer(layer)) layer.addTo(state.map);
    if (!state.active[key] && state.map.hasLayer(layer)) state.map.removeLayer(layer);
}

async function loadDistrictBorders() {
    if (state.districts) return state.districts;
    state.districts = await fetchJson("/assets/tamil_nadu_districts.geojson", null);
    return state.districts;
}

function renderDistrictBorders() {
    state.layers.districts.clearLayers();
    if (!state.districts || !state.districts.features) return;

    const districtLayer = L.geoJSON(state.districts, {
        style: () => ({
            color: "#6f5a50",
            weight: 1,
            opacity: 0.7,
            fillOpacity: 0
        })
    });

    districtLayer.addTo(state.layers.districts);
    districtLayer.bringToFront();
}

function renderHeatmap() {
    if (state.layers.heat && state.map.hasLayer(state.layers.heat)) {
        state.map.removeLayer(state.layers.heat);
    }

    const points = (state.recent.features || []).map((feature) => {
        const [lon, lat] = feature.geometry.coordinates;
        const intensity = Math.min(Number(feature.properties.risk || 0), 1);
        return [lat, lon, Math.max(0.2, intensity)];
    });

    state.layers.heat = L.heatLayer(points, {
        radius: 24,
        blur: 20,
        maxZoom: 11,
        gradient: {
            0.2: "#f7c948",
            0.5: "#e88f24",
            0.75: "#cf3f22",
            1: "#71150f"
        }
    });

    syncLayerVisibility("heat");
}

function renderPredictionGrid() {
    state.layers.grid.clearLayers();
    state.predictions.forEach((cell) => {
        const bounds = [
            [Number(cell.lat) - 0.125, Number(cell.lon) - 0.125],
            [Number(cell.lat) + 0.125, Number(cell.lon) + 0.125]
        ];
        const color = riskColor(Number(cell.predicted_risk || 0));
        L.rectangle(bounds, {
            color,
            weight: 1,
            fillColor: color,
            fillOpacity: 0.12
        })
            .bindPopup(
                `<strong>Predicted risk area</strong><br>` +
                `Chance of fire: ${formatPercent(Number(cell.predicted_risk || 0))}<br>` +
                `For date: ${String(cell.forecast_date).slice(0, 10)}`
            )
            .addTo(state.layers.grid);
    });
    syncLayerVisibility("grid");
}

function renderPredictionMarkers() {
    state.layers.prediction.clearLayers();
    state.predictions
        .filter((cell) => Number(cell.predicted_risk || 0) >= 0.55)
        .forEach((cell) => {
            const risk = Number(cell.predicted_risk || 0);
            const color = riskColor(risk);
            L.circleMarker([cell.lat, cell.lon], {
                radius: risk >= 0.8 ? 5 : 3.5,
                color: "#ffffff",
                weight: 1.5,
                fillColor: color,
                fillOpacity: 0.92
            })
                .bindPopup(
                    `<strong>Predicted fire point</strong><br>` +
                    `Chance of fire: ${formatPercent(risk)}<br>` +
                    `For date: ${String(cell.forecast_date).slice(0, 10)}<br>` +
                    `Recent fire influence: ${formatPercent(Number(cell.recent_fire_score || 0))}`
                )
                .addTo(state.layers.prediction);
        });
    syncLayerVisibility("prediction");
}

function renderMetrics() {
    const recentFeatures = state.recent.features || [];
    const avgRisk = state.predictions.length
        ? state.predictions.reduce((sum, row) => sum + Number(row.predicted_risk || 0), 0) / state.predictions.length
        : 0;
    const highRisk = state.predictions.filter((row) => Number(row.predicted_risk || 0) >= 0.7).length;
    const latestDate = recentFeatures.length
        ? recentFeatures
            .map((feature) => feature.properties.date)
            .sort()
            .at(-1)
        : "-";

    setText("metricFire", recentFeatures.length);
    setText("metricGrid", formatPercent(avgRisk));
    setText("metricPredictions", highRisk);
    setText("metricLatest", latestDate);
}

const locationCache = {};

// async function getLocationName(lat, lon) {
//     try {
//         const res = await fetch(
//             `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`
//         );
//         const data = await res.json();

//         return (
//             data.address?.city ||
//             data.address?.town ||
//             data.address?.village ||
//             data.address?.county ||
//             data.address?.state ||
//             "Unknown location"
//         );
//     } catch (err) {
//         console.warn("Location fetch failed", err);
//         return "Unknown location";
//     }
// }
async function getLocationName(lat, lon) {
    const key = `${lat},${lon}`;
    if (locationCache[key]) return locationCache[key];

    try {
        const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`,
            {
                headers: {
                    "Accept": "application/json"
                }
            }
        );

        const data = await res.json();

        console.log("Location API response:", data); // 🔍 DEBUG

        const location =
            data.address?.city ||
            data.address?.town ||
            data.address?.village ||
            data.address?.county ||
            data.address?.state ||
            "Unknown location";

        locationCache[key] = location;

        return location;
    } catch (err) {
        console.error("Location fetch failed", err);
        return "Unknown location";
    }
}
// function renderRiskList() {
//     const list = $("riskList");
//     if (!list) return;

//     const topZones = state.predictions
//         .slice()
//         .sort((a, b) => Number(b.predicted_risk || 0) - Number(a.predicted_risk || 0))
//         .slice(0, 5);

//     if (!topZones.length) {
//         list.innerHTML = `<div class="empty-state">No prediction data available.</div>`;
//         return;
//     }

//     list.innerHTML = topZones.map((row, index) => {
//         const risk = Number(row.predicted_risk || 0);
//         const band = riskBand(risk);
//         return `
//             <article class="risk-row ${band}">
//                 <div class="row-head">
//                     <span>Area ${index + 1}</span>
//                     <span>${formatPercent(risk)}</span>
//                 </div>
//                 <div class="progress"><span class="${band}" style="width:${risk * 100}%"></span></div>
//                 <p class="metric-note">${Number(row.lat).toFixed(2)}, ${Number(row.lon).toFixed(2)},${Number(row.recent_fire_score || 0).toFixed(2)} for ${String(row.forecast_date).slice(0, 10)}. This area may need closer watch.</p>
//             </article>
//         `;
//     }).join("");
// }

async function renderRiskList() {
    const list = $("riskList");
    if (!list) return;

    const topZones = state.predictions
        .slice()
        .sort((a, b) => Number(b.predicted_risk || 0) - Number(a.predicted_risk || 0))
        .slice(0, 5);

    if (!topZones.length) {
        list.innerHTML = `<div class="empty-state">No prediction data available.</div>`;
        return;
    }

    // 🔹 Step 1: Render immediately (without location)
    list.innerHTML = topZones.map((row, index) => {
        const risk = Number(row.predicted_risk || 0);
        const band = riskBand(risk);

        return `
            <article class="risk-row ${band}" id="risk-${index}">
                <div class="row-head">
                    <span>Area ${index + 1}</span>
                    <span>${formatPercent(risk)}</span>
                </div>

                <div class="progress">
                    <span class="${band}" style="width:${risk * 100}%"></span>
                </div>

                <p class="metric-note" id="loc-${index}">
                    📍 Loading location...
                    (${Number(row.lat).toFixed(2)}, ${Number(row.lon).toFixed(2)})
                </p>
            </article>
        `;
    }).join("");

    // 🔹 Step 2: Update location async
    topZones.forEach(async (row, index) => {
        const location = await getLocationName(row.lat, row.lon);

        const el = document.getElementById(`loc-${index}`);
        if (el) {
            el.innerHTML = `
                📍 ${location} 
                (${Number(row.lat).toFixed(2)}, ${Number(row.lon).toFixed(2)}) <br>
                🔥 Risk Score: ${Number(row.recent_fire_score || 0).toFixed(2)} <br>
                📅 ${String(row.forecast_date).slice(0, 10)}
            `;
        }
    });
}
function renderRecentList() {
    const list = $("recentList");
    if (!list) return;

    const recent = (state.recent.features || [])
        .slice()
        .sort((a, b) => Number(b.properties.frp || 0) - Number(a.properties.frp || 0))
        .slice(0, 4);

    if (!recent.length) {
        list.innerHTML = `<div class="empty-state">No recent fires found in the current dataset.</div>`;
        return;
    }

    list.innerHTML = recent.map((feature) => `
        <article class="risk-row high">
            <div class="row-head">
                <span>${feature.properties.date}</span>
                <span>FRP ${Number(feature.properties.frp || 0).toFixed(1)}</span>
            </div>
            <p class="metric-note">${Number(feature.geometry.coordinates[1]).toFixed(2)}, ${Number(feature.geometry.coordinates[0]).toFixed(2)} with ${certaintyLabel(feature.properties.confidence)} that this is a real fire signal.</p>
        </article>
    `).join("");
}

function fitToData() {
    const layers = [
        ...state.layers.grid.getLayers(),
        ...state.layers.prediction.getLayers()
    ];
    const group = L.featureGroup(layers);
    if (group.getLayers().length) {
        state.map.fitBounds(group.getBounds(), { padding: [28, 28], maxZoom: 8 });
        return;
    }

    const points = (state.recent.features || []).map((feature) => {
        const [lon, lat] = feature.geometry.coordinates;
        return L.marker([lat, lon]);
    });
    const fallback = L.featureGroup(points);
    if (fallback.getLayers().length) {
        state.map.fitBounds(fallback.getBounds(), { padding: [28, 28], maxZoom: 8 });
    }
}

function bindControls() {
    document.querySelectorAll("[data-layer]").forEach((input) => {
        const key = input.dataset.layer;
        state.active[key] = input.checked;
        input.addEventListener("change", () => {
            state.active[key] = input.checked;
            if (key === "forestBase") {
                syncBasemap();
                return;
            }
            syncLayerVisibility(key);
        });
    });

    const daySlider = $("daySlider");
    if (daySlider) {
        daySlider.addEventListener("input", () => {
            setText("dayLabel", `Day ${daySlider.value}`);
            loadPredictions(daySlider.value);
        });
    }

    const refreshBtn = $("refreshBtn");
    if (refreshBtn) refreshBtn.addEventListener("click", loadAll);

    const fitBtn = $("fitBtn");
    if (fitBtn) fitBtn.addEventListener("click", fitToData);
}

async function loadPredictions(day = 1) {
    const [grid, summary] = await Promise.all([
        fetchJson(`/prediction/grid?day=${day}`, []),
        fetchJson(`/prediction/summary?day=${day}`, null)
    ]);

    state.predictions = Array.isArray(grid) ? grid : [];
    state.summary = summary;

    renderPredictionGrid();
    renderPredictionMarkers();
    renderMetrics();
    renderRiskList();
}

async function loadAll() {
    const day = $("daySlider")?.value || 1;
    const [health, recent] = await Promise.all([
        fetchJson("/api", null),
        fetchJson("/risk/recent", { type: "FeatureCollection", features: [] })
    ]);

    setApiStatus(Boolean(health));
    state.recent = recent || { type: "FeatureCollection", features: [] };
    await loadDistrictBorders();

    renderDistrictBorders();
    renderHeatmap();
    renderRecentList();
    await loadPredictions(day);
    fitToData();
}

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    syncBasemap();
    bindControls();
    loadAll();
});
