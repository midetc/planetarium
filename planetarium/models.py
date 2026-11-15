from django.contrib.auth import get_user_model
from django.db import models


class AstronomyShow(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    show_themes = models.ManyToManyField(
        "ShowTheme",
        blank=True,
        related_name="astronomy_shows",
    )

    def __str__(self):
        return self.title


class ShowTheme(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class PlanetariumDome(models.Model):
    name = models.CharField(max_length=200)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()

    @property
    def capacity(self):
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class ShowSession(models.Model):
    astronomy_show = models.ForeignKey(
        AstronomyShow,
        on_delete=models.CASCADE,
        related_name="show_sessions",
    )
    planetarium_dome = models.ForeignKey(
        PlanetariumDome,
        on_delete=models.CASCADE,
        related_name="show_sessions",
    )
    show_time = models.DateTimeField()

    def __str__(self):
        return f"{self.astronomy_show} - {self.show_time}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="reservations",
    )

    def __str__(self):
        return f"Reservation by {self.user} - {self.created_at}"


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    show_session = models.ForeignKey(
        ShowSession,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="tickets",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["show_session", "row", "seat"],
                name="unique_ticket_seat_per_session",
            ),
        ]

    def __str__(self):
        return f"{self.show_session} - Row {self.row}, Seat {self.seat}"
