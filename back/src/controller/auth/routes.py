"""
Authentication routes for Supabase user management.
"""
from flask import Blueprint, request, jsonify
from src.supabase import get_supabase_anon
from gotrue.errors import AuthApiError

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Register a new user with email and password.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "securepassword"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        supabase = get_supabase_anon()
        
        # Sign up the user
        response = supabase.auth.sign_up({
            'email': email,
            'password': password
        })
        
        return jsonify({
            'user': response.user.model_dump() if response.user else None,
            'session': response.session.model_dump() if response.session else None
        }), 201
        
    except AuthApiError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login with email and password.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "securepassword"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        supabase = get_supabase_anon()
        
        # Sign in the user
        response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        
        return jsonify({
            'user': response.user.model_dump() if response.user else None,
            'session': response.session.model_dump() if response.session else None,
            'access_token': response.session.access_token if response.session else None
        }), 200
        
    except AuthApiError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout the current user.
    
    Expects Authorization header with Bearer token.
    """
    try:
        # Get the token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token provided'}), 401
        
        token = auth_header.split(' ')[1]
        
        supabase = get_supabase_anon()
        
        # Set the session using the token
        supabase.auth.set_session(token, token)
        
        # Sign out
        supabase.auth.sign_out()
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except AuthApiError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/user', methods=['GET'])
def get_user():
    """
    Get the current user information.
    
    Expects Authorization header with Bearer token.
    """
    try:
        # Get the token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token provided'}), 401
        
        token = auth_header.split(' ')[1]
        
        supabase = get_supabase_anon()
        
        # Set the session and get the user
        response = supabase.auth.set_session(token, token)
        
        if response.user:
            return jsonify({'user': response.user.model_dump()}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
        
    except AuthApiError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
