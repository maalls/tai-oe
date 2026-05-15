"""
Authentication handler for Supabase user management.
Integrates with the RAG HTTP server.
"""
import json

from src.api.routes.server_body_helpers import read_body
from src.api.routes.server_query_helpers import get_qs_value
from src.api.routes.server_response_helpers import send_error, send_redirect
from src.api.routes.server_status_helpers import pop_status, status_from_result
from src.infrastructure.clients.supabase import get_supabase_anon
from supabase import AuthApiError


class AuthHandler:
    """Handle authentication operations with Supabase."""
    
    def __init__(self):
        self.supabase = get_supabase_anon()
    
    def handle_signup(self, body: bytes) -> dict:
        """
        Register a new user with email and password.
        
        Request body:
        {
            "email": "user@example.com",
            "password": "securepassword"
        }
        """
        try:
            data = json.loads(body)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return {'error': 'Email and password are required', 'status': 400}
            
            response = self.supabase.auth.sign_up({
                'email': email,
                'password': password
            })
            
            return {
                'user': response.user.model_dump() if response.user else None,
                'session': response.session.model_dump() if response.session else None,
                'status': 201
            }
            
        except AuthApiError as e:
            return {'error': str(e), 'status': 400}
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    def handle_login(self, body: bytes) -> dict:
        """
        Login with email and password.
        
        Request body:
        {
            "email": "user@example.com",
            "password": "securepassword"
        }
        """
        try:
            data = json.loads(body)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return {'error': 'Email and password are required', 'status': 400}
            
            response = self.supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            return {
                'user': response.user.model_dump() if response.user else None,
                'session': response.session.model_dump() if response.session else None,
                'access_token': response.session.access_token if response.session else None,
                'status': 200
            }
            
        except AuthApiError as e:
            return {'error': str(e), 'status': 401}
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    def handle_logout(self, auth_header: str) -> dict:
        """
        Logout the current user.
        
        Expects Authorization header with Bearer token.
        """
        try:
            if not auth_header or not auth_header.startswith('Bearer '):
                return {'error': 'No authorization token provided', 'status': 401}
            
            token = auth_header.split(' ')[1]
            
            # Set the session using the token
            self.supabase.auth.set_session(token, token)
            
            # Sign out
            self.supabase.auth.sign_out()
            
            return {'message': 'Logged out successfully', 'status': 200}
            
        except AuthApiError as e:
            return {'error': str(e), 'status': 401}
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    def handle_get_user(self, auth_header: str) -> dict:
        """
        Get the current user information.
        
        Expects Authorization header with Bearer token.
        """
        try:
            if not auth_header or not auth_header.startswith('Bearer '):
                return {'error': 'No authorization token provided', 'status': 401}
            
            token = auth_header.split(' ')[1]
            
            # Verify the token and get the user
            response = self.supabase.auth.get_user(token)
            
            if response.user:
                return {'user': response.user.model_dump(), 'status': 200}
            else:
                return {'error': 'User not found', 'status': 404}
            
        except AuthApiError as e:
            return {'error': str(e), 'status': 401}
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    def verify_token(self, auth_header: str) -> tuple[bool, dict]:
        """
        Verify JWT token and return (is_valid, user_dict).
        Used for protecting routes.
        """
        try:
            if not auth_header or not auth_header.startswith('Bearer '):
                print(f"[AuthHandler] Invalid auth header format: {auth_header[:50] if auth_header else 'None'}")
                return False, None
            
            token = auth_header.split(' ')[1]
            print(f"[AuthHandler] Verifying token: {token[:50]}...")
            response = self.supabase.auth.get_user(token)
            
            if response.user:
                print(f"[AuthHandler] Token valid for user: {response.user.email}")
                return True, response.user.model_dump()
            print(f"[AuthHandler] No user in response")
            return False, None
            
        except Exception as e:
            print(f"[AuthHandler] Exception during token verification: {e}")
            return False, None


def handle_auth_signup_post(handler):
    """Handle /api/auth/signup POST endpoint."""
    body = read_body(handler)
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_auth_signup(body)
    status = pop_status(result)
    return handler.json(result, status)


def handle_auth_login_post(handler):
    """Handle /api/auth/login POST endpoint."""
    body = read_body(handler)
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_auth_login(body)
    status = pop_status(result)
    return handler.json(result, status)


def handle_auth_logout_post(handler):
    """Handle /api/auth/logout POST endpoint."""
    auth_header = handler.headers.get('Authorization', '')
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_auth_logout(auth_header)
    status = pop_status(result)
    return handler.json(result, status)


def handle_auth_user_get(handler):
    """Handle /api/auth/user GET endpoint."""
    auth_header = handler.headers.get('Authorization', '')
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_auth_user(auth_header)
    status = pop_status(result)
    return handler.json(result, status)


def handle_oauth_login_get(handler, qs):
    """Handle /api/oauth/login GET endpoint."""
    provider = get_qs_value(qs, 'provider')
    if not provider:
        return send_error(handler, 400, 'Missing provider parameter')
    redirect_url = get_qs_value(qs, 'redirect_url')

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_oauth_login(provider=provider, redirect_url=redirect_url)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_oauth_callback_get(handler, qs):
    """Handle /api/oauth/callback GET endpoint."""
    provider = get_qs_value(qs, 'provider')
    code = get_qs_value(qs, 'code')
    state = get_qs_value(qs, 'state')
    if not provider:
        return send_error(handler, 400, 'Missing provider parameter')
    if not code:
        return send_error(handler, 400, 'Missing code parameter')

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_oauth_callback(provider=provider, code=code, state=state)

    if result.get('status') == 'ok' and result.get('redirect_url'):
        return send_redirect(handler, result['redirect_url'])

    status = status_from_result(result)
    return handler.json(result, status)
