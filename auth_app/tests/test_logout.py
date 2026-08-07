from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class LogoutViewTest(APITestCase):
    """Tests for POST /api/logout/."""

    def setUp(self):
        """Create a user and provide login/logout urls."""
        self.user = User.objects.create_user(
            username="logoutuser",
            email="logoutuser@mail.de",
            password="securepassword123",
        )
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")

    def _login(self):
        """Log in so the test client stores the auth cookies."""
        self.client.post(
            self.login_url,
            {"username": "logoutuser", "password": "securepassword123"},
        )

    def test_logout_success(self):
        """An authenticated user can log out and receives 200."""
        self._login()
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_logout_deletes_cookies(self):
        """Logout clears the access and refresh token cookies."""
        self._login()
        response = self.client.post(self.logout_url)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_logout_unauthenticated(self):
        """Logout without authentication is rejected with 401."""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_cookie(self):
        """A tampered access_token cookie is rejected with 401."""
        self.client.cookies["access_token"] = "invalid.token.value"
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
