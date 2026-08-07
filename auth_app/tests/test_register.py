from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationViewTest(APITestCase):
    """Tests for POST /api/register/."""

    def setUp(self):
        """Provide the register url and a valid payload."""
        self.url = reverse("register")
        self.valid_payload = {
            "username": "newuser",
            "email": "newuser@mail.de",
            "password": "securepassword123",
            "confirmed_password": "securepassword123",
        }

    def test_register_success(self):
        """Valid data creates a user and returns 201 with a detail message."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["detail"], "User created successfully!")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_hashed(self):
        """The stored password is hashed, not saved in plain text."""
        self.client.post(self.url, self.valid_payload)
        user = User.objects.get(username="newuser")
        self.assertNotEqual(user.password, "securepassword123")
        self.assertTrue(user.check_password("securepassword123"))

    def test_register_passwords_do_not_match(self):
        """Mismatched passwords are rejected with a 400."""
        payload = self.valid_payload.copy()
        payload["confirmed_password"] = "differentpassword"
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_register_duplicate_username(self):
        """A username that already exists is rejected with a 400."""
        User.objects.create_user(
            username="newuser",
            email="existing@mail.de",
            password="somepassword123",
        )
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_not_in_response(self):
        """The response never exposes the password fields."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertNotIn("password", response.data)
        self.assertNotIn("confirmed_password", response.data)
