from django.conf import settings
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

NO_THROTTLE = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}


@override_settings(REST_FRAMEWORK=NO_THROTTLE)
class UserApiTests(APITestCase):
    def test_register_hides_password_and_ignores_is_staff(self):
        response = self.client.post(
            "/api/user/register/",
            {
                "email": "visitor@planetarium.test",
                "password": "seat42ok",
                "is_staff": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        self.assertFalse(response.data["is_staff"])

    def test_register_rejects_short_password(self):
        response = self.client.post(
            "/api/user/register/",
            {"email": "short@planetarium.test", "password": "1234"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_and_me(self):
        self.client.post(
            "/api/user/register/",
            {"email": "visitor@planetarium.test", "password": "seat42ok"},
            format="json",
        )
        token_response = self.client.post(
            "/api/user/token/",
            {"email": "visitor@planetarium.test", "password": "seat42ok"},
            format="json",
        )

        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", token_response.data)
        self.assertIn("refresh", token_response.data)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        me_response = self.client.get("/api/user/me/")

        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], "visitor@planetarium.test")

    def test_me_requires_token(self):
        response = self.client.get("/api/user/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
