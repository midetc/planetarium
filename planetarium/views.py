from django.db.models import Count, F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from planetarium.models import ShowTheme, PlanetariumDome, AstronomyShow, ShowSession
from planetarium.permissions import IsAdminOrAuthenticatedReadOnly
from planetarium.serializers import (
    ShowThemeSerializer,
    PlanetariumDomeSerializer,
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer,
    AstronomyShowCreateSerializer,
    ItemImageSerializer,
    ShowSessionListSerializer,
    ShowSessionCreateSerializer, ShowSessionDetailSerializer,
)


class ShowThemeViewSet(viewsets.ModelViewSet):
    queryset = ShowTheme.objects.all()
    serializer_class = ShowThemeSerializer
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)


class PlanetariumDomeViewSet(viewsets.ModelViewSet):
    queryset = PlanetariumDome.objects.all()
    serializer_class = PlanetariumDomeSerializer
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)


class AstronomyShowViewSet(viewsets.ModelViewSet):
    queryset = AstronomyShow.objects.all()
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return AstronomyShowListSerializer
        elif self.action == "retrieve":
            return AstronomyShowDetailSerializer
        elif self.action == "upload_image":
            return ItemImageSerializer
        return AstronomyShowCreateSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        item = self.get_object()
        serializer = self.get_serializer(item, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShowSessionViewSet(viewsets.ModelViewSet):
    queryset = ShowSession.objects.all()
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset
        astronomy_show_filter = self.request.query_params.get("astronomy_show")
        date_filter = self.request.query_params.get("date")

        if date_filter:
            queryset = queryset.filter(show_time__date=date_filter)

        if astronomy_show_filter:
            astronomy_show_ids = [int(str_id) for str_id in
                astronomy_show_filter.split(",")]
            queryset = queryset.filter(astronomy_show__id__in=astronomy_show_ids)

        if self.action == "list":
            queryset = (
                queryset
                .select_related("planetarium_dome")
                .annotate(
                    tickets_available=F("planetarium_dome__rows") * F(
                        "planetarium_dome__seats_in_row",
                    ) - Count("tickets"),
                )
            ).order_by("id")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ShowSessionListSerializer
        elif self.action == "retrieve":
            return ShowSessionDetailSerializer
        return ShowSessionCreateSerializer
