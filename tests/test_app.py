import pytest

from gifsync import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'devkey'
    client = app.test_client()
    yield client


def test_routes_while_logged_out(client):
    routes_and_codes = [
        {'route': '/', 'code': 302},
        {'route': '/home', 'code': 200},
        {'route': '/home/', 'code': 404},
        {'route': '/collection', 'code': 302},
        {'route': '/collection/', 'code': 404},
        {'route': '/create', 'code': 302},
        {'route': '/create/', 'code': 404},
        {'route': '/show', 'code': 302},
        {'route': '/show/', 'code': 404},
        {'route': '/favicon.ico', 'code': 200}
    ]
    assert_routes_with_codes(client, routes_and_codes)


def test_html_for_skeleton_while_logged_out(client):
    routes = ['/', '/home']
    print()
    for route in routes:
        assert_html_skeleton_exists(client, route)


def assert_routes_with_codes(client, routes_and_codes):
    print()
    for route_and_code in routes_and_codes:
        route = route_and_code['route']
        code = route_and_code['code']
        print(
            f'Testing Response Code from route "{route}" '
            'without following redirects.')
        response = client.get(route)
        assert(response.status_code == code)
        if 'redirect' in route_and_code:
            assert('Location' in response.headers and
                   response.headers['Location'].endswith(
                       route_and_code['redirect']))


def assert_html_skeleton_exists(client, route):
    print(f'Testing for Skeleton HTML in route "{route}".')
    response = client.get(route, follow_redirects=True)
    assert(b'<nav class="navbar' in response.data)
    assert(b'<div class="container">' in response.data)
    assert(b'<footer class="page-footer">' in response.data)
