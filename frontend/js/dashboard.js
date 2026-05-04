const API_BASE = window.FOREST_API_BASE ||
    (window.location.protocol === "http:" || window.location.protocol === "https:"
        ? window.location.origin
        : "http://127.0.0.1:8000");
const DEFAULT_CENTER = [10.7, 78.4];
const DEFAULT_ZOOM = 7;

const state = {
    map: null,
    layers: {},
    active: {
        heat: true,
        grid: true,
        prediction: true
    },
    recent: { type: "FeatureCollection", features: [] },
    predictions: [],
    summary: null
};

const locationCache = {};
let currentRenderId = 0;

async function getLocationName(lat, lon) {
    const key = `${lat.toFixed(2)},${lon.toFixed(2)}`;
    if (locationCache[key]) return locationCache[key];

    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10`);
        if (response.ok) {
            const data = await response.json();
            if (data && data.address) {
                const addr = data.address;
                const locName = addr.forest || addr.park || addr.natural || addr.hamlet || addr.village || addr.town || addr.city || addr.suburb || addr.neighbourhood || addr.road || addr.municipality;
                const district = addr.state_district || addr.county;

                let result = "";
                if (district) {
                    result = district;
                    if (locName && locName !== district) {
                        result += `, ${locName}`;
                    }
                } else if (locName) {
                    result = locName;
                } else {
                    result = data.name || addr.state || "Tamil Nadu Region";
                }

                locationCache[key] = result;
                return result;
            } else if (data && data.name) {
                locationCache[key] = data.name;
                return data.name;
            }
        }
    } catch (e) {
        console.warn("Geocoding failed", e);
    }
    locationCache[key] = "Tamil Nadu Region";
    return "Tamil Nadu Region";
}

const $ = (id) => document.getElementById(id);

function initMap() {
    state.map = L.map("map", { zoomControl: false }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.control.zoom({ position: "bottomleft" }).addTo(state.map);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap & CartoDB"
    }).addTo(state.map);

    state.layers.heat = null;
    state.layers.grid = L.layerGroup().addTo(state.map);
    state.layers.prediction = L.layerGroup().addTo(state.map);
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
                `<strong>Predicted fire cell</strong><br>` +
                `Risk: ${formatPercent(Number(cell.predicted_risk || 0))}<br>` +
                `Forecast: ${String(cell.forecast_date).slice(0, 10)}`
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
                    `<strong>Forecast hotspot</strong><br>` +
                    `Risk: ${formatPercent(risk)}<br>` +
                    `Forecast: ${String(cell.forecast_date).slice(0, 10)}<br>` +
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

async function renderRiskList() {
    const list = $("riskList");
    if (!list) return;

    const renderId = ++currentRenderId;

    const topZones = state.predictions
        .slice()
        .sort((a, b) => Number(b.predicted_risk || 0) - Number(a.predicted_risk || 0))
        .slice(0, 5);

    if (!topZones.length) {
        list.innerHTML = `<div class="empty-state">No prediction data available.</div>`;
        return;
    }

    list.innerHTML = topZones.map((row, index) => {
        const risk = Number(row.predicted_risk || 0);
        const band = riskBand(risk);
        const locId = `zone-loc-${renderId}-${index}`;
        return `
            <article class="risk-row ${band}" style="cursor: pointer;" onclick="state.map.flyTo([${row.lat}, ${row.lon}], 10)">
                <div class="row-head">
                    <span>Area ${index + 1}</span>
                    <span>${formatPercent(risk)}</span>
                </div>
                <div class="progress"><span class="${band}" style="width:${risk * 100}%"></span></div>
                <p class="metric-note">
                    <span id="${locId}">Loading location...</span><br>
                    ${Number(row.lat).toFixed(2)}, ${Number(row.lon).toFixed(2)} for ${String(row.forecast_date).slice(0, 10)}. This area may need closer watch.
                </p>
            </article>
        `;
    }).join("");

    for (let index = 0; index < topZones.length; index++) {
        const row = topZones[index];
        const name = await getLocationName(Number(row.lat), Number(row.lon));
        if (renderId !== currentRenderId) return;
        const el = $(`zone-loc-${renderId}-${index}`);
        if (el) el.textContent = name;
    }
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
            <p class="metric-note">${Number(feature.geometry.coordinates[1]).toFixed(2)}, ${Number(feature.geometry.coordinates[0]).toFixed(2)} with confidence ${feature.properties.confidence}</p>
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
        fetchJson("/", null),
        fetchJson("/risk/recent", { type: "FeatureCollection", features: [] })
    ]);

    setApiStatus(Boolean(health));
    state.recent = recent || { type: "FeatureCollection", features: [] };

    renderHeatmap();
    renderRecentList();
    await loadPredictions(day);
    fitToData();
}

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    bindControls();
    loadAll();
});
