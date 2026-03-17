from django.http import JsonResponse
from django.shortcuts import render
from .models import Location, TaxiRoute, TravelPath, TravelStep, Route, Stop, RouteStop
import json


def seed_sample_data():
    if (
        TravelPath.objects.exists()
        and Location.objects.exists()
        and TaxiRoute.objects.exists()
    ):
        return

    loc_data = {
        "Goro": (9.048, 38.753),
        "Megenagna": (9.028, 38.758),
        "Piazza": (9.022, 38.758),
        "Piazza Taxi Stop": (9.024, 38.757),
        "Bole": (9.027, 38.761),
        "Merkato": (9.033, 38.744),
        "Meskel Square": (9.020, 38.748),
        "Gerji": (9.005, 38.771),
    }

    locations = {}
    for name, (lat, lng) in loc_data.items():
        locations[name], _ = Location.objects.get_or_create(
            name=name, defaults={"latitude": lat, "longitude": lng}
        )

    taxi1, _ = TaxiRoute.objects.get_or_create(
        name="Goro → Megenagna",
        defaults={
            "start_location": locations["Goro"],
            "end_location": locations["Megenagna"],
            "estimated_fare": 30.00,
            "polyline": json.dumps([[9.048, 38.753], [9.041, 38.755], [9.028, 38.758]]),
        },
    )
    taxi2, _ = TaxiRoute.objects.get_or_create(
        name="Piazza Taxi Stop → Piazza",
        defaults={
            "start_location": locations["Piazza Taxi Stop"],
            "end_location": locations["Piazza"],
            "estimated_fare": 5.00,
            "polyline": json.dumps([[9.024, 38.757], [9.022, 38.758]]),
        },
    )

    path1, _ = TravelPath.objects.get_or_create(
        name="Goro to Piazza via Megenagna",
        defaults={
            "start_location": locations["Goro"],
            "end_location": locations["Piazza"],
            "description": "Taxi + walk + taxi segment path",
        },
    )
    if path1.steps.count() == 0:
        TravelStep.objects.create(
            travel_path=path1,
            order=0,
            step_type=TravelStep.STEP_TYPE_TAXI,
            taxi_route=taxi1,
        )
        TravelStep.objects.create(
            travel_path=path1,
            order=1,
            step_type=TravelStep.STEP_TYPE_WALK,
            from_location=locations["Megenagna"],
            to_location=locations["Piazza Taxi Stop"],
        )
        TravelStep.objects.create(
            travel_path=path1,
            order=2,
            step_type=TravelStep.STEP_TYPE_TAXI,
            taxi_route=taxi2,
        )
    else:
        step0 = path1.steps.filter(order=0, step_type=TravelStep.STEP_TYPE_TAXI).first()
        if step0 and not step0.taxi_route:
            step0.taxi_route = taxi1
            step0.save()

    route1, _ = Route.objects.get_or_create(
        name="Bole to Merkato",
        defaults={"start": "Bole", "end": "Merkato", "estimated_fare": 20.00},
    )
    route2, _ = Route.objects.get_or_create(
        name="Meskel Square to Gerji",
        defaults={"start": "Meskel Square", "end": "Gerji", "estimated_fare": 15.00},
    )
    route3, _ = Route.objects.get_or_create(
        name="Bole to Piazza",
        defaults={"start": "Bole", "end": "Piazza", "estimated_fare": 18.00},
    )

    stops = {
        "Bole": (9.027, 38.761),
        "Meskel Square": (9.020, 38.748),
        "Sarit": (9.032, 38.762),
        "Kazanchis": (9.023, 38.742),
        "Piassa": (9.022, 38.758),
        "Merkato": (9.033, 38.744),
        "Gerji": (9.005, 38.771),
    }

    stop_objs = {}
    for name, (lat, lng) in stops.items():
        stop_objs[name] = Stop.objects.create(name=name, latitude=lat, longitude=lng)

    RouteStop.objects.bulk_create(
        [
            RouteStop(route=route1, stop=stop_objs["Bole"], order=0),
            RouteStop(route=route1, stop=stop_objs["Sarit"], order=1),
            RouteStop(route=route1, stop=stop_objs["Kazanchis"], order=2),
            RouteStop(route=route1, stop=stop_objs["Merkato"], order=3),
            RouteStop(route=route2, stop=stop_objs["Meskel Square"], order=0),
            RouteStop(route=route2, stop=stop_objs["Kazanchis"], order=1),
            RouteStop(route=route2, stop=stop_objs["Gerji"], order=2),
            RouteStop(route=route3, stop=stop_objs["Bole"], order=0),
            RouteStop(route=route3, stop=stop_objs["Meskel Square"], order=1),
            RouteStop(route=route3, stop=stop_objs["Piassa"], order=2),
        ]
    )


def home(request):
    seed_sample_data()
    return render(request, "routes/home.html")


def map_data(request):
    seed_sample_data()
    locations = [
        {
            "id": loc.id,
            "name": loc.name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
        }
        for loc in Location.objects.all()
    ]
    taxi_routes = [
        {
            "id": tr.id,
            "name": tr.name,
            "start": tr.start_location.name,
            "end": tr.end_location.name,
            "fare": float(tr.estimated_fare),
            "polyline": tr.get_polyline(),
        }
        for tr in TaxiRoute.objects.all()
    ]

    # keep legacy route/stop for compatibility
    routes = []
    for route in Route.objects.all():
        stops_data = []
        for rs in RouteStop.objects.filter(route=route).order_by("order"):
            stops_data.append(
                {
                    "name": rs.stop.name,
                    "latitude": rs.stop.latitude,
                    "longitude": rs.stop.longitude,
                }
            )
        routes.append(
            {
                "id": route.id,
                "name": route.name,
                "start": route.start,
                "end": route.end,
                "fare": float(route.estimated_fare),
                "stops": stops_data,
            }
        )

    stops = []
    for stop in Stop.objects.all():
        stops.append(
            {
                "id": stop.id,
                "name": stop.name,
                "latitude": stop.latitude,
                "longitude": stop.longitude,
                "routes": [r.name for r in stop.routes.all()],
            }
        )

    return JsonResponse(
        {
            "locations": locations,
            "taxi_routes": taxi_routes,
            "routes": routes,
            "stops": stops,
        }
    )


def route_search(request):
    seed_sample_data()
    start_name = request.GET.get("start", "").strip()
    dest_name = request.GET.get("destination", "").strip()

    if not start_name or not dest_name:
        return JsonResponse(
            {"error": "Please provide both start and destination names."}, status=400
        )

    taxi_route = TaxiRoute.objects.filter(
        start_location__name__iexact=start_name,
        end_location__name__iexact=dest_name,
    ).first()
    if taxi_route:
        response = {
            "path": taxi_route.name,
            "start": taxi_route.start_location.name,
            "end": taxi_route.end_location.name,
            "total_fare": float(taxi_route.estimated_fare),
            "steps": [
                {
                    "type": "taxi",
                    "route": taxi_route.name,
                    "from": taxi_route.start_location.name,
                    "to": taxi_route.end_location.name,
                    "fare": float(taxi_route.estimated_fare),
                    "polyline": taxi_route.get_polyline(),
                }
            ],
        }
        return JsonResponse(response)

    travel_paths = TravelPath.objects.filter(
        start_location__name__icontains=start_name,
        end_location__name__icontains=dest_name,
    )
    if travel_paths.exists():
        path = travel_paths.first()
        steps = []
        for step in path.steps.all().order_by("order"):
            if step.step_type == TravelStep.STEP_TYPE_TAXI:
                steps.append(
                    {
                        "type": "taxi",
                        "route": step.taxi_route.name,
                        "from": step.taxi_route.start_location.name,
                        "to": step.taxi_route.end_location.name,
                        "fare": float(step.taxi_route.estimated_fare),
                        "polyline": step.taxi_route.get_polyline(),
                    }
                )
            else:
                walk_coords = None
                if step.from_location and step.to_location:
                    walk_coords = [
                        [step.from_location.latitude, step.from_location.longitude],
                        [step.to_location.latitude, step.to_location.longitude],
                    ]
                steps.append(
                    {
                        "type": "walk",
                        "from": step.from_location.name if step.from_location else "",
                        "to": step.to_location.name if step.to_location else "",
                        "coordinates": walk_coords,
                    }
                )

        total_fare = sum(step["fare"] for step in steps if step.get("fare"))
        response = {
            "path": path.name,
            "start": path.start_location.name,
            "end": path.end_location.name,
            "description": path.description,
            "total_fare": total_fare,
            "steps": steps,
        }
        return JsonResponse(response)

    # fallback: existing route-stop search
    start_stops = list(Stop.objects.filter(name__icontains=start_name))
    dest_stops = list(Stop.objects.filter(name__icontains=dest_name))
    if not start_stops:
        start_stops = list(Stop.objects.all())
    if not dest_stops:
        dest_stops = list(Stop.objects.all())

    best = None
    for route in Route.objects.all():
        route_stop_ids = [
            rs.stop.id for rs in RouteStop.objects.filter(route=route).order_by("order")
        ]
        for s in start_stops:
            for d in dest_stops:
                if (
                    s.id in route_stop_ids
                    and d.id in route_stop_ids
                    and route_stop_ids.index(s.id) < route_stop_ids.index(d.id)
                ):
                    distance = route_stop_ids.index(d.id) - route_stop_ids.index(s.id)
                    candidate = {
                        "route": route.name,
                        "board": s.name,
                        "exit": d.name,
                        "fare": float(route.estimated_fare),
                        "transfer": [],
                        "steps": [
                            f"Board {route.name} at {s.name}",
                            f"Exit at {d.name}",
                        ],
                        "distance": distance,
                    }
                    if best is None or candidate["distance"] < best["distance"]:
                        best = candidate
    if best:
        return JsonResponse(
            {
                "route": best["route"],
                "board": best["board"],
                "exit": best["exit"],
                "fare": best["fare"],
                "transfer": best["transfer"],
                "steps": best["steps"],
            }
        )

    return JsonResponse(
        {"error": "No route recommendation found. Try nearby stops."}, status=404
    )
