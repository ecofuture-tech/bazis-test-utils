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
`parallel` (bazis_test_utils.utils): the calls start together in threads, the results come
in the order of the calls, the connections of the threads are closed, an exception of a
call is raised in the test. Run in a test project in a subprocess (Django with SQLite).
"""

import pytest


SETTINGS = """
SECRET_KEY = 'test'
INSTALLED_APPS = ['django.contrib.contenttypes', 'django.contrib.auth']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'db.sqlite3',
                         'TEST': {'NAME': 'test.sqlite3'}}}
USE_TZ = True
"""


@pytest.fixture
def project(pytester):
    pytester.makepyfile(project_settings=SETTINGS)
    pytester.makeini('[pytest]\nDJANGO_SETTINGS_MODULE = project_settings\n')
    return pytester


def test_parallel(project):
    project.makepyfile(
        """
        import threading

        import pytest
        from django.db import connections

        from bazis_test_utils.utils import parallel


        def test_the_results_in_the_order_of_the_calls():
            assert parallel(3, lambda: 'same') == ['same'] * 3
            assert parallel([lambda: 1, lambda: 2, lambda: 3]) == [1, 2, 3]
            assert parallel([]) == []


        def test_the_calls_run_at_once():
            # each call waits for all the others: in a row the first one would time out
            together = threading.Barrier(4, timeout=5)
            threads = parallel(4, lambda: (together.wait(), threading.get_ident())[1])
            assert len(set(threads)) == 4 and threading.get_ident() not in threads


        @pytest.mark.django_db(transaction=True)
        def test_the_connections_of_the_threads_are_closed():
            from django.contrib.auth.models import User

            def count():
                User.objects.count()
                return connections['default']

            opened = parallel(3, count)
            assert len(set(map(id, opened))) == 3
            assert all(conn.connection is None for conn in opened)


        def test_an_exception_of_a_call():
            done = []

            def fail():
                raise ValueError('refused')

            with pytest.raises(ValueError, match='refused'):
                parallel([fail, lambda: done.append(1)])
            # the other calls are done before it is raised
            assert done == [1]


        def test_a_wrong_call():
            with pytest.raises(TypeError):
                parallel(2)
            with pytest.raises(TypeError):
                parallel([lambda: 1], lambda: 2)
        """
    )
    project.runpytest_subprocess('-p', 'no:cacheprovider').assert_outcomes(passed=5)
