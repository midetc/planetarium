from rest_framework import serializers

from planetarium.models import (
    ShowTheme,
    PlanetariumDome,
    AstronomyShow,
    ShowSession,
    Ticket,
)


class ShowThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowTheme
        fields = ("id", "name")


class PlanetariumDomeSerializer(serializers.ModelSerializer):
    capacity = serializers.ReadOnlyField()

    class Meta:
        model = PlanetariumDome
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class AstronomyShowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronomyShow
        fields = ("id", "title", "description", "show_themes")


class AstronomyShowListSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)
    show_themes = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = AstronomyShow
        fields = ("id", "title", "description", "show_themes", "image")


class AstronomyShowDetailSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)
    show_themes = ShowThemeSerializer(many=True, read_only=True)

    class Meta:
        model = AstronomyShow
        fields = ("id", "title", "description", "show_themes", "image")


class ItemImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronomyShow
        fields = ("id", "image")


class ShowSessionListSerializer(serializers.ModelSerializer):
    astronomy_show = serializers.SlugRelatedField(slug_field="title", read_only=True, )
    planetarium_dome = serializers.SlugRelatedField(slug_field="name", read_only=True, )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = ShowSession
        fields = (
            "id",
            "astronomy_show",
            "planetarium_dome",
            "show_time",
            "tickets_available",
        )


class TicketSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class ShowSessionDetailSerializer(serializers.ModelSerializer):
    planetarium_dome = PlanetariumDomeSerializer()
    astronomy_show = AstronomyShowDetailSerializer()
    taken_places = TicketSeatSerializer(source="tickets", many=True, read_only=True)

    class Meta:
        model = ShowSession
        fields = (
            "id",
            "astronomy_show",
            "planetarium_dome",
            "show_time",
            "taken_places",
        )


class ShowSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowSession
        fields = ("id", "astronomy_show", "planetarium_dome", "show_time")
