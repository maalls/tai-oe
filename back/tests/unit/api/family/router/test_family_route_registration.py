from src.api.main import create_app


def test_family_routes_registered():
    app = create_app()
    paths = {route.path for route in app.routes}

    assert '/api/family/{family_id}' in paths
    assert '/api/family' in paths