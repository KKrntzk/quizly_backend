from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class CookieTokenRefreshViewTest(APITestCase):
    """Tests for POST /api/token/refresh/."""

    def setUp(self):
        """Create a user and provide the relevant urls."""
        self.user = User.objects.create_user(
            username="refreshuser",
            email="refreshuser@mail.de",
            password="securepassword123",
        )
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.refresh_url = reverse("token_refresh")

    def _login(self):
        """Log in so the test client stores the auth cookies."""
        self.client.post(
            self.login_url,
            {"username": "refreshuser", "password": "securepassword123"},
        )

    def test_refresh_success(self):
        """A valid refresh cookie returns 200 with a detail message."""
        self._login()
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Token refreshed")

    def test_refresh_sets_new_access_cookie(self):
        """A successful refresh sets a new access_token cookie."""
        self._login()
        response = self.client.post(self.refresh_url)
        self.assertIn("access_token", response.cookies)
        self.assertNotEqual(response.cookies["access_token"].value, "")

    def test_refresh_access_cookie_is_httponly(self):
        """The new access_token cookie is flagged as HttpOnly."""
        self._login()
        response = self.client.post(self.refresh_url)
        self.assertTrue(response.cookies["access_token"]["httponly"])

    def test_refresh_token_not_in_body(self):
        """The raw access token is never exposed in the response body."""
        self._login()
        response = self.client.post(self.refresh_url)
        self.assertNotIn("access", response.data)

    def test_refresh_without_cookie(self):
        """A request without a refresh cookie is rejected with 401."""
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_cookie(self):
        """A tampered refresh cookie is rejected with 401."""
        self.client.cookies["refresh_token"] = "invalid.token.value"
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_fails_after_logout(self):
        """A refresh token blacklisted on logout can no longer be used."""
        self._login()
        self.client.post(self.logout_url)
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
