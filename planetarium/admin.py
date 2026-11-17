from django.contrib import admin

from planetarium.models import (
    ShowTheme,
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    Reservation, Ticket,
)


# Register your models here.
@admin.register(ShowTheme)
@admin.register(AstronomyShow)
@admin.register(PlanetariumDome)
@admin.register(ShowSession)
@admin.register(Reservation)
@admin.register(Ticket)
class ModelAdmin(admin.ModelAdmin):
    pass

