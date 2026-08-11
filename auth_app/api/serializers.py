from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates registration data and creates a new user."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirmed_password"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, data):
        """Ensure the password and its confirmation match."""
        if data["password"] != data["confirmed_password"]:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        """Create a user with a hashed password."""
        validated_data.pop("confirmed_password")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """Extends token login with basic user data in the response."""

    def validate(self, attrs):
        """Validate credentials and attach user data to the result."""
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
        }
        return data
