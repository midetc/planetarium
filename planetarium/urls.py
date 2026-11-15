from django.urls import include, path
from rest_framework.routers import DefaultRouter
from planetarium.views import PlanetariumDomeViewSet, ShowThemeViewSet

app_name = "planetarium"

router = DefaultRouter()

router.register("planetarium-dome", PlanetariumDomeViewSet)
router.register("show-theme", ShowThemeViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
