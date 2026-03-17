let map;

function initMap() {
    const mapElement = document.getElementById('map');
    if (!mapElement) {
        console.error('Map element not found');
        return;
    }
    map = L.map('map').setView([9.02, 38.75], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attributions">CARTO</a>',
    }).addTo(map);
    console.log('Leaflet map initialized successfully');
}

const routeColors = ['#006dff', '#ff6d00', '#05944d', '#b2095a'];
let mapRoutes = [];
let stopMarkers = [];

function renderMap(data) {
    mapRoutes.forEach((line) => map.removeLayer(line));
    stopMarkers.forEach((m) => map.removeLayer(m));
    mapRoutes = [];
    stopMarkers = [];

    data.taxi_routes.forEach((route, i) => {
        const poly = L.polyline(route.polyline, {
            color: routeColors[i % routeColors.length],
            weight: 4,
            opacity: 0.9,
        }).addTo(map);
        mapRoutes.push(poly);
        poly.bindPopup(`<strong>${route.name}</strong><br>${route.start} → ${route.end}<br>Fare ETB ${route.fare}`);
    });

    data.locations.forEach((loc) => {
        const marker = L.circleMarker([loc.latitude, loc.longitude], {
            radius: 6,
            color: '#2d2d7c',
            fillColor: '#8cb1ff',
            fillOpacity: 0.9,
        }).addTo(map);
        marker.bindPopup(`<strong>${loc.name}</strong>`);
        stopMarkers.push(marker);
    });

    if (data.locations.length > 0) {
        const latlngs = data.locations.map((stop) => [stop.latitude, stop.longitude]);
        map.fitBounds(latlngs, { padding: [20, 20] });
    }
}

async function loadData() {
    try {
        const res = await fetch('/api/map-data/');
        if (!res.ok) {
            throw new Error(`Map API failed with status ${res.status}`);
        }
        const data = await res.json();
        renderMap(data);
    } catch (err) {
        console.error('Map data loading failed', err);
        const mapError = document.getElementById('map-error');
        if (mapError) {
            mapError.textContent = 'Could not load route data. Try refreshing.';
        }
    }
}

function showCurrentPosition() {
    if (!navigator.geolocation) {
        return;
    }
    navigator.geolocation.getCurrentPosition((pos) => {
        const marker = L.marker([pos.coords.latitude, pos.coords.longitude], {
            title: 'Your location',
        }).addTo(map);
        marker.bindPopup('You are here').openPopup();
        map.setView([pos.coords.latitude, pos.coords.longitude], 14);
    }, () => {
        // ignore permission denial
    });
}

async function setupRouteSearch() {
    const form = document.getElementById('route-search-form');
    const result = document.getElementById('route-result');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const start = form.start.value.trim();
        const destination = form.destination.value.trim();
        if (!start || !destination) {
            result.textContent = 'Enter both starting location and destination.';
            return;
        }

        result.textContent = 'Searching route...';
        try {
            const searchUrl = `/route-search/?start=${encodeURIComponent(start)}&destination=${encodeURIComponent(destination)}`;
            const res = await fetch(searchUrl);
            const payload = await res.json();
            if (!res.ok) {
                result.textContent = payload.error || 'Could not find a route. Try another stop.';
                return;
            }
            if (payload.path) {
            let html = `<strong>${payload.path}</strong><br>${payload.start} → ${payload.end}<br>Fare estimate ETB ${payload.total_fare.toFixed(2)}<br><strong>Steps:</strong><ol>`;
            payload.steps.forEach((step) => {
                if (step.type === 'taxi') {
                    html += `<li>Taxi: ${step.route} (${step.from} → ${step.to}, ETB ${step.fare.toFixed(2)})</li>`;
                } else {
                    html += `<li>Walk: ${step.from} → ${step.to}</li>`;
                }
            });
            html += '</ol>';
            result.innerHTML = html;
        } else {
            const transfer = payload.transfer?.length ? `Transfer at ${payload.transfer.join(', ')}.` : '';
            result.innerHTML = `<strong>Best Route:</strong> ${payload.route} <br /><strong>Board:</strong> ${payload.board} <br /><strong>Exit:</strong> ${payload.exit} <br /><strong>Fare:</strong> ETB ${payload.fare.toFixed(2)} <br /><strong>Steps:</strong> ${payload.steps.join(' → ')} <br />${transfer}`;
        }
        } catch (err) {
            console.error(err);
            result.textContent = 'Unexpected server error. Please refresh.';
        }
    });
}

window.addEventListener('DOMContentLoaded', async () => {
    try {
        initMap();
        setupRouteSearch();
        await loadData();
        showCurrentPosition();
    } catch (err) {
        console.error('Unexpected map startup error', err);
        const mapError = document.getElementById('map-error');
        if (mapError) {
            mapError.textContent = 'Map failed to initialize. Check browser console for details.';
        }
    }
});