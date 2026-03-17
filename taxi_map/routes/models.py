from django.db import models
from django.core.exceptions import ValidationError
import json


def _normalize_polyline_data(data):
    # Accept list of [lat, lng]
    if isinstance(data, list):
        normalized = []
        for item in data:
            if (isinstance(item, list) or isinstance(item, tuple)) and len(item) == 2:
                lat, lng = item
                normalized.append([float(lat), float(lng)])
            else:
                raise ValidationError("Polyline list must contain [lat, lng] pairs.")
        if len(normalized) < 2:
            raise ValidationError("Polyline requires at least two coordinate points.")
        return normalized

    # Accept GeoJSON FeatureCollection of Point features or LineString geometry
    if isinstance(data, dict):
        geo_type = data.get("type")
        if geo_type == "FeatureCollection":
            points = []
            for feat in data.get("features", []):
                geom = feat.get("geometry", {})
                if geom.get("type") == "Point":
                    lon, lat = geom.get("coordinates", [None, None])
                    points.append([float(lat), float(lon)])
                elif geom.get("type") == "LineString":
                    for lon, lat in geom.get("coordinates", []):
                        points.append([float(lat), float(lon)])
                else:
                    continue
            if len(points) < 2:
                raise ValidationError(
                    "GeoJSON FeatureCollection requires at least two points or a LineString."
                )
            return points
        elif geo_type == "LineString":
            points = []
            for lon, lat in data.get("coordinates", []):
                points.append([float(lat), float(lon)])
            if len(points) < 2:
                raise ValidationError("LineString requires at least two coordinates.")
            return points
        else:
            raise ValidationError("Unsupported GeoJSON type for polyline.")

    raise ValidationError(
        "Polyline must be JSON list of [lat, lng] pairs or GeoJSON features."
    )


def validate_json_polyline(value):
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        raise ValidationError("Polyline must be valid JSON.")
    _normalize_polyline_data(parsed)


class Location(models.Model):
    name = models.CharField(max_length=120, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaxiRoute(models.Model):
    name = models.CharField(max_length=130)
    start_location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="taxi_routes_from"
    )
    end_location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="taxi_routes_to"
    )
    estimated_fare = models.DecimalField(max_digits=8, decimal_places=2)
    polyline = models.TextField(
        help_text="JSON list of [lat, lng] points or GeoJSON FeatureCollection/LineString",
        validators=[validate_json_polyline],
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}: {self.start_location} → {self.end_location}"

    def get_polyline(self):
        value = json.loads(self.polyline)
        return _normalize_polyline_data(value)


class TravelPath(models.Model):
    name = models.CharField(max_length=150)
    start_location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="travel_paths_start"
    )
    end_location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="travel_paths_end"
    )
    description = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}: {self.start_location} → {self.end_location}"


class TravelStep(models.Model):
    STEP_TYPE_TAXI = "taxi"
    STEP_TYPE_WALK = "walk"
    STEP_TYPE_CHOICES = [
        (STEP_TYPE_TAXI, "Taxi"),
        (STEP_TYPE_WALK, "Walk"),
    ]

    travel_path = models.ForeignKey(
        TravelPath, on_delete=models.CASCADE, related_name="steps"
    )
    order = models.PositiveIntegerField()
    step_type = models.CharField(max_length=10, choices=STEP_TYPE_CHOICES)
    taxi_route = models.ForeignKey(
        TaxiRoute, null=True, blank=True, on_delete=models.SET_NULL
    )
    from_location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="walk_from_steps",
    )
    to_location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="walk_to_steps",
    )

    class Meta:
        ordering = ["travel_path", "order"]

    def clean(self):
        if self.step_type == self.STEP_TYPE_TAXI and not self.taxi_route:
            raise ValidationError("Taxi step requires taxi_route.")
        if self.step_type == self.STEP_TYPE_WALK and (
            not self.from_location or not self.to_location
        ):
            raise ValidationError("Walk step requires from_location and to_location.")

    def __str__(self):
        return f"{self.travel_path.name} step {self.order + 1}: {self.step_type}"


class Route(models.Model):
    name = models.CharField(max_length=120)
    start = models.CharField(max_length=120)
    end = models.CharField(max_length=120)
    estimated_fare = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.start} → {self.end})"


class Stop(models.Model):
    name = models.CharField(max_length=120)
    latitude = models.FloatField()
    longitude = models.FloatField()
    routes = models.ManyToManyField(Route, through="RouteStop", related_name="stops")

    def __str__(self):
        return self.name


class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["route", "order"]
        unique_together = ("route", "stop")

    def __str__(self):
        return f"{self.route.name} - {self.order+1}: {self.stop.name}"
