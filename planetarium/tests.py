import io
import tempfile
from datetime import timedelta

from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from planetarium.models import (
    AstronomyShow,
    PlanetariumDome,
    Reservation,
    ShowSession,
    ShowTheme,
)
from user.models import User

NO_THROTTLE = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}


def make_png():
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color="black").save(buffer, format="PNG")
    return SimpleUploadedFile(
        "poster.png",
        buffer.getvalue(),
        content_type="image/png",
    )


@override_settings(
    REST_FRAMEWORK=NO_THROTTLE,
    MEDIA_ROOT=tempfile.mkdtemp(),
)
class PlanetariumApiTests(APITestCase):
    def setUp(self):
        self.visitor = User.objects.create_user(
            email="visitor@planetarium.test",
            password="seat42ok",
        )
        self.other = User.objects.create_user(
            email="other@planetarium.test",
            password="seat42ok",
        )
        self.admin = User.objects.create_user(
            email="admin@planetarium.test",
            password="seat42ok",
            is_staff=True,
        )
        self.theme = ShowTheme.objects.create(name="Mars")
        self.dome = PlanetariumDome.objects.create(
            name="Main hall",
            rows=2,
            seats_in_row=3,
        )
        self.show = AstronomyShow.objects.create(
            title="Night Sky",
            description="Stars",
        )
        self.show.show_themes.add(self.theme)
        self.session = ShowSession.objects.create(
            astronomy_show=self.show,
            planetarium_dome=self.dome,
            show_time=timezone.now() + timedelta(days=2),
        )

    def test_guest_cannot_list_themes(self):
        response = self.client.get("/api/planetarium/show-themes/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_read_but_cannot_create_theme(self):
        self.client.force_authenticate(self.visitor)
        listed = self.client.get("/api/planetarium/show-themes/")
        created = self.client.post(
            "/api/planetarium/show-themes/",
            {"name": "Stars"},
            format="json",
        )

        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_theme(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/planetarium/show-themes/",
            {"name": "Stars"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Stars")

    def test_dome_capacity_is_rows_times_seats(self):
        self.client.force_authenticate(self.visitor)
        response = self.client.get("/api/planetarium/planetarium-domes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["capacity"], 6)

    def test_show_list_uses_theme_names_and_detail_uses_objects(self):
        self.client.force_authenticate(self.visitor)
        listed = self.client.get("/api/planetarium/astronomy-shows/")
        detail = self.client.get(
            f"/api/planetarium/astronomy-shows/{self.show.id}/",
        )

        self.assertEqual(listed.data[0]["show_themes"], ["Mars"])
        self.assertEqual(
            detail.data["show_themes"],
            [{"id": self.theme.id, "name": "Mars"}],
        )

    def test_admin_can_upload_show_image(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            f"/api/planetarium/astronomy-shows/{self.show.id}/upload-image/",
            {"image": make_png()},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("night-sky-", response.data["image"])

    def test_session_list_reports_free_seats_and_filters_by_show(self):
        self.client.force_authenticate(self.visitor)
        response = self.client.get(
            "/api/planetarium/show-sessions/",
            {"astronomy_show": self.show.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["tickets_available"], 6)
        self.assertEqual(response.data[0]["astronomy_show"], "Night Sky")

    def test_reservation_belongs_to_token_user_and_hides_others(self):
        self.client.force_authenticate(self.visitor)
        created = self.client.post(
            "/api/planetarium/reservations/",
            {
                "tickets": [
                    {"row": 1, "seat": 1, "show_session": self.session.id},
                ],
            },
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["user"], self.visitor.id)
        self.assertEqual(len(created.data["tickets"]), 1)

        self.client.force_authenticate(self.other)
        listed = self.client.get("/api/planetarium/reservations/")

        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.data["count"], 0)

    def test_taken_seat_does_not_leave_an_empty_reservation(self):
        self.client.force_authenticate(self.visitor)
        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "show_session": self.session.id},
            ],
        }
        self.client.post(
            "/api/planetarium/reservations/",
            payload,
            format="json",
        )
        before = Reservation.objects.count()

        repeated = self.client.post(
            "/api/planetarium/reservations/",
            payload,
            format="json",
        )

        self.assertEqual(repeated.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), before)

    def test_cannot_book_a_seat_outside_the_dome_or_a_started_session(self):
        self.client.force_authenticate(self.visitor)
        outside = self.client.post(
            "/api/planetarium/reservations/",
            {
                "tickets": [
                    {"row": 1, "seat": 9, "show_session": self.session.id},
                ],
            },
            format="json",
        )
        past_session = ShowSession.objects.create(
            astronomy_show=self.show,
            planetarium_dome=self.dome,
            show_time=timezone.now() - timedelta(hours=1),
        )
        started = self.client.post(
            "/api/planetarium/reservations/",
            {
                "tickets": [
                    {"row": 1, "seat": 1, "show_session": past_session.id},
                ],
            },
            format="json",
        )

        self.assertEqual(outside.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(started.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)
