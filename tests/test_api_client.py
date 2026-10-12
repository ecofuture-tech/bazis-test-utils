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

"""
`get_api_client` (bazis_test_utils.utils): the methods with a body send JSON:API with the
token, a multipart body with the content type of the client.
"""

from fastapi import FastAPI, Request

import pytest

from bazis_test_utils.utils import get_api_client


app = FastAPI()


@app.api_route('/echo/', methods=['POST', 'PATCH', 'PUT'])
async def echo(request: Request):
    return {
        'method': request.method,
        'query': dict(request.query_params),
        'content_type': request.headers['content-type'].split(';')[0],
        'authorization': request.headers.get('authorization'),
        'body': (await request.body()).decode(),
    }


@pytest.mark.parametrize('method', ['post', 'patch', 'put'])
def test_a_json_body(method):
    client = get_api_client(app, token='token')
    # the parameters keep their positions: the second one is params
    response = getattr(client, method)('/echo/', {'x': '1'}, json_data={'data': None})
    assert response.json() == {
        'method': method.upper(),
        'query': {'x': '1'},
        'content_type': 'application/vnd.api+json',
        'authorization': 'Bearer token',
        'body': '{"data":null}',
    }


@pytest.mark.parametrize('method', ['post', 'patch', 'put'])
def test_a_multipart_body(method):
    response = getattr(get_api_client(app), method)(
        '/echo/', data={'name': 'a'}, files={'file': ('a.txt', b'text')}
    )
    assert response.json()['content_type'] == 'multipart/form-data'
    assert 'text' in response.json()['body']
