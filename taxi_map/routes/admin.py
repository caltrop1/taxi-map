from django.contrib import admin
from .models import Location, TaxiRoute, TravelPath, TravelStep, Route, Stop, RouteStop


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude")
    search_fields = ("name",)


@admin.register(TaxiRoute)
class TaxiRouteAdmin(admin.ModelAdmin):
    list_display = ("name", "start_location", "end_location", "estimated_fare")
    search_fields = ("name",)


class TravelStepInline(admin.TabularInline):
    model = TravelStep
    extra = 1


@admin.register(TravelPath)
class TravelPathAdmin(admin.ModelAdmin):
    list_display = ("name", "start_location", "end_location")
    inlines = [TravelStepInline]


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("name", "start", "end", "estimated_fare")
    search_fields = ("name", "start", "end")


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude")
    search_fields = ("name",)


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ("route", "stop", "order")
    list_filter = ("route",)
