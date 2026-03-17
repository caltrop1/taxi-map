from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("route-search/", views.route_search, name="route_search"),
    path("api/map-data/", views.map_data, name="map_data"),
]
