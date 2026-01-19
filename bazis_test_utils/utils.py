import typing

from fastapi.testclient import TestClient


_RequestData = typing.Mapping[str, str | typing.Iterable[str]]


def get_api_client(app, token: str = None):
    class ApiClient:
        def __init__(self):
            self.headers = {'Content-Type': 'application/vnd.api+json'}
            if token:
                self.headers['Authorization'] = f'Bearer {token}'

            self.client = TestClient(app)

        def get(self, url: str, params: dict = None, headers: dict = None):
            return self.client.get(
                url,
                params=params,
                headers=self.headers | (headers or {}),
            )

        def post(
            self,
            url: str,
            params: dict = None,
            content: dict = None,
            cookies: dict = None,
            data: dict = None,
            json_data: dict = None,
            files: dict = None,
            headers: dict = None,
        ):
            headers = self.headers | (headers or {})
            if files:
                headers.pop('Content-Type', None)

            return self.client.post(
                url,
                params=params,
                content=content,
                data=data,
                cookies=cookies,
                json=json_data,
                headers=headers,
                files=files,
            )

        def patch(
            self,
            url: str,
            params: dict = None,
            content: dict = None,
            cookies: dict = None,
            data: dict = None,
            json_data: dict = None,
            files: dict = None,
            headers: dict = None,
        ):
            headers = self.headers | (headers or {})
            if files:
                headers.pop('Content-Type', None)

            return self.client.patch(
                url,
                params=params,
                content=content,
                data=data,
                cookies=cookies,
                json=json_data,
                headers=headers,
                files=files,
            )

        def delete(self, url: str, params: dict = None, headers: dict = None):
            return self.client.delete(url, params=params, headers=self.headers | (headers or {}))

        def put(
            self,
            url: str,
            params: dict = None,
            content: dict = None,
            cookies: dict = None,
            data: dict = None,
            json_data: dict = None,
            files: dict = None,
            headers: dict = None,
        ):
            headers = self.headers | (headers or {})
            if files:
                headers.pop('Content-Type', None)

            return self.client.put(
                url,
                params=params,
                content=content,
                data=data,
                cookies=cookies,
                json=json_data,
                headers=headers,
                files=files,
            )

        def options(self, url: str, params: dict = None, headers: dict = None):
            return self.client.options(url, params=params, headers=self.headers | (headers or {}))

        def head(self, url: str, params: dict = None, headers: dict = None):
            return self.client.head(url, params=params, headers=self.headers | (headers or {}))

    client = ApiClient()
    return client
