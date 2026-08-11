from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticates users via the JWT stored in the access_token cookie."""

    def authenticate(self, request):
        """Return the user and token from the access_token cookie, or None."""
        access_token = request.COOKIES.get("access_token")

        if access_token is None:
            return None

        validated_token = self.get_validated_token(access_token)
        user = self.get_user(validated_token)

        return (user, validated_token)
