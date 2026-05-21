import os
import requests

from src.infrastructure.clients.oauth.state import decode_oauth_state, encode_oauth_state


def get_azure_oauth_url(redirect_url=None):
    """Generate Azure OAuth2 login URL."""
    client_id = os.getenv('AZURE_SECRET_ID')
    client_secret = os.getenv('AZURE_VALUE')
    default_redirect_uri = os.getenv('AZURE_REDIRECT_URI')
    tenant = os.getenv('AZURE_TENANT_ID', 'common')
    
    # State can include redirect_url, user_id, etc.
    state_payload = {
        'redirect_url': redirect_url or default_redirect_uri,
    }
    state = encode_oauth_state(state_payload)

    authorize_url = (
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?"
        f"client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri={default_redirect_uri}"
        f"&response_mode=query"
        f"&scope=openid%20email%20profile%20offline_access%20User.Read"
        f"&state={state}"
    )
    return {'status': 'ok', 'auth_url': authorize_url}

def handle_azure_oauth_callback(code, state=None):
    """Exchange code for tokens and return redirect URL."""
    client_id = os.getenv('AZURE_SECRET_ID')
    client_secret = os.getenv('AZURE_VALUE')
    redirect_uri = os.getenv('AZURE_REDIRECT_URI')
    tenant = os.getenv('AZURE_TENANT_ID', 'common')
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    # Decode state
    redirect_url = redirect_uri
    if state:
        try:
            payload = decode_oauth_state(state)
            redirect_url = payload.get('redirect_url') or redirect_uri
        except Exception:
            pass

    data = {
        'client_id': client_id,
        'scope': 'openid email profile offline_access User.Read',
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'client_secret': client_secret,
    }
    try:
        resp = requests.post(token_url, data=data)
        resp.raise_for_status()
        tokens = resp.json()
        # TODO: Use id_token/access_token to identify user, create session, etc.
        return {'status': 'ok', 'redirect_url': redirect_url, 'tokens': tokens}
    except Exception as e:
        return {'status': 'error', 'message': f'Azure OAuth failed: {e}'}
