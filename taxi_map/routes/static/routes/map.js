let map;
let routeLayers = [];
let locationLookup = {};

function initMap() {
  const mapElement = document.getElementById('map');
  if (!mapElement) {
    console.error('Map element not found');
    return;
  }

  map = L.map('map').setView([9.02, 38.75], 13);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attributions">CARTO</a>',
  }).addTo(map);

  console.log('Leaflet map initialized successfully');
}

function clearRouteLayers() {
  routeLayers.forEach((layer) => map.removeLayer(layer));
  routeLayers = [];
}

function drawRoute(steps) {
  clearRouteLayers();
  if (!steps || !steps.length) {
    return;
  }

  const allBounds = [];

  steps.forEach((step) => {
    if (step.type === 'taxi') {
      let coordinates = step.polyline || step.coordinates;
      if (!coordinates || coordinates.length < 2) {
        const fromCoord = locationLookup[step.from];
        const toCoord = locationLookup[step.to];
        if (fromCoord && toCoord) {
          coordinates = [fromCoord, toCoord];
        }
      }
      if (!coordinates || coordinates.length < 2) {
        console.warn('Skipping taxi step due to invalid coordinates', step);
        return;
      }
      const polyline = L.polyline(coordinates, {
        color: '#006dff',
        weight: 5,
        opacity: 0.95,
      }).addTo(map);
      polyline.bindPopup(`${step.route} (${step.from} → ${step.to})`);
      routeLayers.push(polyline);
      allBounds.push(...polyline.getLatLngs());
    } else if (step.type === 'walk') {
      let coordinates = step.coordinates;
      if (!coordinates && step.from && step.to) {
        const fromCoord = locationLookup[step.from];
        const toCoord = locationLookup[step.to];
        if (fromCoord && toCoord) {
          coordinates = [fromCoord, toCoord];
        }
      }
      if (!coordinates || coordinates.length < 2) {
        return;
      }
      const polyline = L.polyline(coordinates, {
        color: '#6f6f6f',
        weight: 3,
        opacity: 0.8,
        dashArray: '8, 6',
      }).addTo(map);
      polyline.bindPopup(`Walk: ${step.from} → ${step.to}`);
      routeLayers.push(polyline);
      allBounds.push(...polyline.getLatLngs());
    }
  });

  if (allBounds.length > 0) {
    map.fitBounds(allBounds, { padding: [20, 20] });
  }
}

function addLocationMarkers(locations) {
  locationLookup = {};
  locations.forEach((loc) => {
    locationLookup[loc.name] = [loc.latitude, loc.longitude];
    L.circleMarker([loc.latitude, loc.longitude], {
      radius: 4,
      color: '#1f456e',
      fillColor: '#7ab4ff',
      fillOpacity: 0.9,
    })
      .bindPopup(`<strong>${loc.name}</strong>`)
      .addTo(map);
  });
}

async function loadData() {
  try {
    const res = await fetch('/api/map-data/');
    if (!res.ok) {
      throw new Error('Failed to load map data');
    }
    const data = await res.json();
    addLocationMarkers(data.locations);
  } catch (err) {
    console.error('Map data loading failed', err);
    const mapError = document.getElementById('map-error');
    if (mapError) {
      mapError.textContent = 'Could not load location data.';
    }
  }
}

function showCurrentPosition() {
  if (!navigator.geolocation) {
    console.warn('Geolocation not available in browser.');
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const coords = [pos.coords.latitude, pos.coords.longitude];
      const marker = L.marker(coords, {
        title: 'Your location',
      }).addTo(map);
      marker.bindPopup('Your current location').openPopup();
      map.setView(coords, 14);
    },
    (err) => {
      console.error('Geolocation error', err);
      const mapError = document.getElementById('map-error');
      if (mapError) {
        mapError.textContent =
          'Could not get your location. Please allow location access or try again.';
      }
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0,
    }
  );
}

async function setupRouteSearch() {
  const form = document.getElementById('route-search-form');
  const result = document.getElementById('route-result');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const start = form.querySelector('[name="start"]').value.trim();
    const destination = form.querySelector('[name="destination"]').value.trim();

    if (!start || !destination) {
      result.textContent = 'Enter both starting location and destination.';
      return;
    }

    result.textContent = 'Searching route...';
    try {
      const searchUrl = `/route-search/?start=${encodeURIComponent(
        start
      )}&destination=${encodeURIComponent(destination)}`;
      const res = await fetch(searchUrl);
      const payload = await res.json();

      if (!res.ok) {
        result.textContent = payload.error || 'Could not find a route.';
        clearRouteLayers();
        return;
      }

      if (payload.steps) {
        let html = `<strong>${payload.path || 'Recommended path'}</strong><br>${
          payload.start || start
        } → ${payload.end || destination} <br>Fare: ETB ${(
          payload.total_fare || payload.fare || 0
        ).toFixed(2)}<br><strong>Steps:</strong><ol>`;
        payload.steps.forEach((step) => {
          if (step.type === 'taxi') {
            html += `<li>Taxi: ${step.route} (${step.from} → ${step.to}, ETB ${step.fare?.toFixed(2) || 0})</li>`;
          } else {
            html += `<li>Walk: ${step.from} → ${step.to}</li>`;
          }
        });
        html += '</ol>';
        result.innerHTML = html;
        drawRoute(payload.steps);
      } else {
        result.textContent = payload.route || 'Route found.';
      }
    } catch (err) {
      console.error(err);
      result.textContent = 'Unexpected server error. Please refresh.';
      clearRouteLayers();
    }
  });
}

window.addEventListener('DOMContentLoaded', async () => {
  try {
    initMap();
    await loadData();
    await setupRouteSearch();
    showCurrentPosition();
  } catch (err) {
    console.error('Unexpected map startup error', err);
    const mapError = document.getElementById('map-error');
    if (mapError) {
      mapError.textContent = 'Map failed to initialize. Check console for details.';
    }
  }
});
