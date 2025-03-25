import typing as T

import requests


class SkydioAPIClient(object):
    """
    Simple client for interacting with the Skydio API, utilizing the requests library
    """

    def __init__(self, api_token, url="https://api.skydio.com/api"):
        # type: (str, str) -> None
        self.api_token = api_token
        self.url = url

    def api_token_header(self):
        # type: () -> T.Dict
        return {
            "Accept": "application/json",
            "Authorization": "ApiToken " + self.api_token,
        }

    def get(self, endpoint, **kwargs):
        # type: (str, T.Any) -> T.Dict[str, T.Any]
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        # type: (str, T.Any) -> T.Dict[str, T.Any]
        return self._request("POST", endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        # type: (str, T.Any) -> T.Dict[str, T.Any]
        return self._request("DELETE", endpoint, **kwargs)

    def _request(self, method, endpoint, **kwargs):
        # type: (str, str, T.Any) -> T.Dict[str, T.Any]
        headers = kwargs.setdefault("headers", {})
        headers.update(self.api_token_header())
        resp = requests.request(method, self.url + endpoint, **kwargs)
        resp.raise_for_status()
        return resp.json()
