# Copyright 2026 EcoFuture Technology Services LLC and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
