import requests
from requests import Response


def spotify_request(
    path: str, access_token: str, timeout: int = 60
) -> tuple[Response, dict]:
    response = requests.get(
        f"https://api.spotify.com/v1/{path}",
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + access_token,
        },
        timeout=timeout,
    )
    return response, response.json()
