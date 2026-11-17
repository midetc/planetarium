from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from planetarium.models import (
    ShowTheme,
    PlanetariumDome,
    AstronomyShow,
    ShowSession,
    Ticket,
    Reservation,
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
    astronomy_show = serializers.SlugRelatedField(
        slug_field="title",
        read_only=True,
    )
    planetarium_dome = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )
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
    taken_places = TicketSeatSerializer(
        source="tickets",
        many=True,
        read_only=True
    )

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


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = (
            "row",
            "seat",
            "show_session",
        )

    def validate(self, attrs: Any) -> Any:
        show_session = attrs.get("show_session")
        row = attrs.get("row")
        seat = attrs.get("seat")
        if show_session.planetarium_dome.rows < row or row < 1:
            raise serializers.ValidationError("Invalid row number")
        if show_session.planetarium_dome.seats_in_row < seat or seat < 1:
            raise serializers.ValidationError("Invalid seat number")
        if show_session.tickets.filter(row=row, seat=seat).exists():
            raise serializers.ValidationError("This seat is already taken")
        if show_session.show_time < timezone.now():
            raise serializers.ValidationError(
                "This show session has already started"
            )
        return attrs


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "user", "created_at", "tickets")
        extra_kwargs = {
            "user": {"read_only": True},
            "created_at": {"read_only": True},
        }

    def validate(self, attrs: Any) -> Any:
        tickets = attrs.get("tickets")
        seen = set()
        for ticket in tickets:
            key = (ticket["show_session"].id, ticket["row"], ticket["seat"])
            if key in seen:
                raise serializers.ValidationError("Duplicate tickets")
            seen.add(key)

        return attrs

    @transaction.atomic
    def save(self, **kwargs: Any):
        tickets = self.validated_data.pop("tickets")
        reservation = super().save(user=self.context["request"].user)
        for ticket in tickets:
            Ticket.objects.create(reservation=reservation, **ticket)
        return reservation
