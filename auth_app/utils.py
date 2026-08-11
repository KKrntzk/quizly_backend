def set_auth_cookie(response, key, value):
    """Set a single JWT cookie with secure default flags."""
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=True,
        samesite="Lax",
    )


def set_token_cookies(response, access=None, refresh=None):
    """Set access and/or refresh token cookies on a response."""
    if access is not None:
        set_auth_cookie(response, "access_token", access)
    if refresh is not None:
        set_auth_cookie(response, "refresh_token", refresh)
