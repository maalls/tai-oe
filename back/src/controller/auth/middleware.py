"""
JWT authentication middleware for protecting routes.
"""
from functools import wraps
from flask import request, jsonify
from src.supabase import get_supabase_anon
from gotrue.errors import AuthApiError


def require_auth(f):
    """
    Decorator to protect routes with JWT authentication.
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            # Access user from request.user
            user = request.user
            return jsonify({'user_id': user.id})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get the token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No authorization token provided'}), 401
            
            token = auth_header.split(' ')[1]
            
            supabase = get_supabase_anon()
            
            # Verify the token and get the user
            response = supabase.auth.get_user(token)
            
            if not response.user:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Attach user to request for use in the route
            request.user = response.user
            
            return f(*args, **kwargs)
            
        except AuthApiError as e:
            return jsonify({'error': 'Authentication failed', 'details': str(e)}), 401
        except Exception as e:
            return jsonify({'error': 'Authentication error', 'details': str(e)}), 500
    
    return decorated_function


def optional_auth(f):
    """
    Decorator to optionally add user information to request if token is provided.
    Route will still be accessible without authentication.
    
    Usage:
        @app.route('/public')
        @optional_auth
        def public_route():
            user = getattr(request, 'user', None)
            if user:
                return jsonify({'message': 'Hello ' + user.email})
            return jsonify({'message': 'Hello guest'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                supabase = get_supabase_anon()
                response = supabase.auth.get_user(token)
                if response.user:
                    request.user = response.user
        except:
            # Silently fail - this is optional auth
            pass
        
        return f(*args, **kwargs)
    
    return decorated_function
