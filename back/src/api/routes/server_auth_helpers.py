"""Authentication convenience helpers for legacy API server."""


def authorize_request(handler):
    """Require authentication and raise the legacy unauthorized exception payload."""
    user_data = handler._require_auth()
    if user_data is None:
        raise Exception({"Unauthorized"}, 401)
    return user_data


def get_optional_user_id_from_auth(handler, auth_header: str):
    """Extract user id from auth header without enforcing auth."""
    if not auth_header:
        return None
    user_data = handler._require_auth(auth_header=auth_header, required=False)
    return user_data.get('id') if user_data else None


def require_auth_user_id(handler):
    """Require authenticated user and return its id."""
    user_data = handler._require_auth()
    if user_data is None:
        return None
    return user_data.get('id') if user_data else None
