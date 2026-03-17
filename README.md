# Taxi Map

A Django project for Addis Ababa minibus taxi navigation with route search and map display.

## Features

- Interactive Leaflet map
- Search start/destination and compute recommended routes
- Static assets and custom UI

## Run locally

1. Create and activate virtualenv:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install requirements (if available):
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   cd taxi_map
   python3 manage.py migrate
   ```
4. Start server:
   ```bash
   python3 manage.py runserver
   ```
5. Open `http://127.0.0.1:8000/`.

## Notes

- Favicon and logo are served from `templates/routes/favicon.png` via Django static.
- Update `taxis`, `routes` logic in `routes/views.py` and models as needed.
