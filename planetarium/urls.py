from django.urls import include, path
from rest_framework.routers import DefaultRouter
from planetarium.views import (
    PlanetariumDomeViewSet,
    ShowThemeViewSet,
    AstronomyShowViewSet,
    ShowSessionViewSet,
    ReservationViewSet,
)

app_name = "planetarium"

router = DefaultRouter()

router.register("planetarium-domes", PlanetariumDomeViewSet)
router.register("show-themes", ShowThemeViewSet)
router.register("astronomy-shows", AstronomyShowViewSet)
router.register("show-sessions", ShowSessionViewSet)
router.register("reservations", ReservationViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
