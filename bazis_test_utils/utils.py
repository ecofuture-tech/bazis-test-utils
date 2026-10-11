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

import threading
import typing
from collections.abc import Callable, Sequence

from fastapi.testclient import TestClient


_RequestData = typing.Mapping[str, str | typing.Iterable[str]]


def parallel[T](
    calls: int | Sequence[Callable[[], T]], func: Callable[[], T] | None = None
) -> list[T]:
    """
    Runs calls at once, each in a thread of its own, and returns their results in the
    order of the calls: `parallel(count, func)` calls `func` `count` times,
    `parallel([f1, f2, ...])` calls each function once. The threads wait for each other
    before the calls (a barrier), so the requests of a test of an invariant under
    concurrent requests really race; each thread closes its database connections when its
    call is done. The first exception of a call is raised once all the threads have ended.
    A test that calls the API with it uses `@pytest.mark.django_db(transaction=True)`.
    """
    if isinstance(calls, int):
        if func is None:
            raise TypeError('parallel(count, func): the function to call is missing')
        funcs = [func] * calls
    else:
        if func is not None:
            raise TypeError('parallel([f1, f2, ...]) takes the functions in the list only')
        funcs = list(calls)
    if not funcs:
        return []

    from django.db import connections

    barrier = threading.Barrier(len(funcs))
    results: list = [None] * len(funcs)
    errors: list[BaseException | None] = [None] * len(funcs)

    def worker(index: int, call: Callable[[], T]) -> None:
        try:
            barrier.wait()
            results[index] = call()
        except BaseException as e:
            # raised in the thread of the test, after the others
            errors[index] = e
        finally:
            connections.close_all()

    threads = [threading.Thread(target=worker, args=item) for item in enumerate(funcs)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    for error in errors:
        if error is not None:
            raise error
    return results


def get_api_client(app, token: str | None = None):
    class ApiClient:
        def __init__(self):
            self.headers = {'Content-Type': 'application/vnd.api+json'}
            if token:
                self.headers['Authorization'] = f'Bearer {token}'

            self.client = TestClient(app, client=("127.0.0.1", 50000))

        def get(self, url: str, params: dict | None = None, headers: dict | None = None):
            return self.client.get(
                url,
                params=params,
                headers=self.headers | (headers or {}),
            )

        def post(
            self,
            url: str,
            params: dict | None = None,
            content: dict | None = None,
            cookies: dict | None = None,
            data: dict | None = None,
            json_data: dict | None = None,
            files: dict | None = None,
            headers: dict | None = None,
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
            params: dict | None = None,
            content: dict | None = None,
            cookies: dict | None = None,
            data: dict | None = None,
            json_data: dict | None = None,
            files: dict | None = None,
            headers: dict | None = None,
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

        def delete(self, url: str, params: dict | None = None, headers: dict | None = None):
            return self.client.delete(url, params=params, headers=self.headers | (headers or {}))

        def put(
            self,
            url: str,
            params: dict | None = None,
            content: dict | None = None,
            cookies: dict | None = None,
            data: dict | None = None,
            json_data: dict | None = None,
            files: dict | None = None,
            headers: dict | None = None,
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

        def options(self, url: str, params: dict | None = None, headers: dict | None = None):
            return self.client.options(url, params=params, headers=self.headers | (headers or {}))

        def head(self, url: str, params: dict | None = None, headers: dict | None = None):
            return self.client.head(url, params=params, headers=self.headers | (headers or {}))

    client = ApiClient()
    return client
