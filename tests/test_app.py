import pytest

from gifsync import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client


def test_routes(client):
    routes_and_codes = [
        {'route': '/', 'code': 200},
        {'route': '/home', 'code': 308},
        {'route': '/home/', 'code': 200},
        {'route': '/about', 'code': 308},
        {'route': '/about/', 'code': 200},
        {'route': '/collection', 'code': 308},
        {'route': '/collection/', 'code': 200},
        {'route': '/create', 'code': 308},
        {'route': '/create/', 'code': 200},
        {'route': '/show', 'code': 308},
        {'route': '/show/', 'code': 200},
        {'route': '/favicon.ico', 'code': 200}
    ]
    assert_routes_with_codes(client, routes_and_codes)


def test_html_for_skeleton(client):
    routes = ['/', '/home/', '/about/', '/collection/', '/create/', '/show/']
    print()
    for route in routes:
        assert_html_skeleton_exists(client, route)


def assert_routes_with_codes(client, routes_and_codes):
    print()
    for route_and_code in routes_and_codes:
        route = route_and_code['route']
        code = route_and_code['code']
        print(f'Testing Response Code from route "{route}" without following redirects.')
        response = client.get(route)
        assert(response.status_code == code)
        print(f'Testing Response Code from route "{route}" while following redirects.')
        response = client.get(route, follow_redirects=True)
        assert(response.status_code == 200)


def assert_html_skeleton_exists(client, route):
    print(f'Testing for Skeleton HTML in route "{route}".')
    response = client.get(route)
    assert(b'<nav class="navbar' in response.data)
    assert(b'<div class="container">' in response.data)
    assert(b'<footer class="page-footer">' in response.data)
    assert(b'Copyright 2020' in response.data)
    assert(b'| Made with Flask, Bootstrap, and' in response.data)
    assert(b'MIT License' in response.data)
