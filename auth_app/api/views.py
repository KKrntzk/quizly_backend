from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from auth_app.utils import set_token_cookies
from .serializers import RegistrationSerializer, LoginSerializer


class RegistrationView(APIView):
    """Registers a new user account."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate the data and create a new user."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Authenticates a user and sets JWT cookies."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        """Validate credentials and set access and refresh cookies."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        response = Response(
            {"detail": "Login successfully!", "user": data["user"]},
            status=status.HTTP_200_OK,
        )
        set_token_cookies(response, access=data["access"], refresh=data["refresh"])
        return response


class LogoutView(APIView):
    """Logs the user out by blacklisting the refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Blacklist the refresh token and clear the auth cookies."""
        refresh_token = request.COOKIES.get("refresh_token")
        self._blacklist_token(refresh_token)

        response = Response(
            {
                "detail": "Log-Out successfully! All Tokens will be deleted. "
                "Refresh token is now invalid."
            },
            status=status.HTTP_200_OK,
        )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

    def _blacklist_token(self, refresh_token):
        """Blacklist the given refresh token, ignoring invalid ones."""
        if not refresh_token:
            return
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass


class CookieTokenRefreshView(TokenRefreshView):
    """Refreshes the access token using the refresh token cookie."""

    def post(self, request, *args, **kwargs):
        """Read the refresh cookie and set a new access token cookie."""
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = self._get_new_access_token(refresh_token)
        if access_token is None:
            return Response(
                {"detail": "Refresh token invalid."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response({"detail": "Token refreshed"}, status=status.HTTP_200_OK)
        set_token_cookies(response, access=access_token)
        return response

    def _get_new_access_token(self, refresh_token):
        """Return a new access token, or None if the refresh token is invalid."""
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError, ValidationError):
            return None
        return serializer.validated_data["access"]
