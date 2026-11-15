from rest_framework import viewsets

from planetarium.models import ShowTheme, PlanetariumDome
from planetarium.permissions import IsAdminOrAuthenticatedReadOnly
from planetarium.serializers import ShowThemeSerializer, PlanetariumDomeSerializer


class ShowThemeViewSet(viewsets.ModelViewSet):
    queryset = ShowTheme.objects.all()
    serializer_class = ShowThemeSerializer
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)


class PlanetariumDomeViewSet(viewsets.ModelViewSet):
    queryset = PlanetariumDome.objects.all()
    serializer_class = PlanetariumDomeSerializer
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)
