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
The pytest plugin (bazis_test_utils.plugin), loaded by its entry point in a test project
run in a subprocess: Django with SQLite, no Bazis package.
"""

import pytest


SETTINGS = """
SECRET_KEY = 'test'
INSTALLED_APPS = ['django.contrib.contenttypes', 'django.contrib.auth']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
USE_TZ = True
"""

#: pgtrigger looks installed and its command is recorded (the test database is SQLite)
PGTRIGGER = """
import pytest
from django import apps as django_apps
from django.core import management

CALLS = []
_call_command = management.call_command


def call_command(*args, **kwargs):
    if args[:1] == ('pgtrigger',):
        CALLS.append(args)
        return None
    return _call_command(*args, **kwargs)


def pytest_configure(config):
    management.call_command = call_command
    is_installed = django_apps.apps.is_installed
    django_apps.apps.is_installed = lambda name: name == 'pgtrigger' or is_installed(name)
"""


@pytest.fixture
def project(pytester):
    pytester.makepyfile(project_settings=SETTINGS)
    pytester.makeini('[pytest]\nDJANGO_SETTINGS_MODULE = project_settings\n')
    return pytester


def test_the_triggers_are_installed_once(project):
    """
    Once, after the test database is set up, also when a conftest overrides
    `django_db_setup` (the fixture is set up twice).
    """
    project.makeconftest(
        PGTRIGGER
        + """

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup):
    pass
"""
    )
    project.makepyfile(
        """
        import pytest
        import conftest


        @pytest.mark.django_db
        def test_first():
            assert conftest.CALLS == [('pgtrigger', 'install')]


        @pytest.mark.django_db(transaction=True)
        def test_second():
            assert conftest.CALLS == [('pgtrigger', 'install')]
        """
    )
    project.runpytest_subprocess('-p', 'no:cacheprovider').assert_outcomes(passed=2)


def test_no_triggers_without_pgtrigger(project):
    project.makepyfile(
        """
        import pytest
        from django.core import management


        @pytest.mark.django_db
        def test_database():
            # nothing to install: the command would fail
            assert 'pgtrigger' not in management.get_commands()
        """
    )
    project.runpytest_subprocess('-p', 'no:cacheprovider').assert_outcomes(passed=1)


def test_the_declarations_of_the_installed_packages(project):
    """
    `bazis_declared` and `apply_declarations` call `apply_declarations(using)` of the
    module of declarations of each installed package that has one; none here.
    """
    project.makepyfile(
        fake_declare="""
        def apply_declarations(using):
            return [f'applied to {using}']
        """
    )
    project.makepyfile(
        """
        from bazis_test_utils import plugin


        def test_none(bazis_declared):
            assert bazis_declared == []


        def test_a_package(db, monkeypatch):
            monkeypatch.setattr(plugin, 'DECLARATIONS', (('django.contrib.auth', 'fake_declare'),))
            assert plugin.apply_declarations() == ['applied to default']
            # a package without the module (an older version) is skipped
            monkeypatch.setattr(plugin, 'DECLARATIONS', (('django.contrib.auth', 'missing_declare'),))
            assert plugin.apply_declarations() == []
        """
    )
    project.runpytest_subprocess('-p', 'no:cacheprovider').assert_outcomes(passed=2)


def test_the_connections_of_other_threads_are_closed(project):
    """
    The endpoints of the API client run in worker threads with database connections of
    their own; every request of a `TestClient` outside a `with` block starts new threads.
    Their connections are closed once the test is over, not left to the garbage collector
    (a ResourceWarning of the driver, and sessions that keep the test database from being
    dropped); those of the threads that have ended already when another one is opened.
    """
    # a database in a file: Django does not close the connections of one in memory
    project.makepyfile(
        project_settings=SETTINGS.replace(
            "'NAME': ':memory:'", "'NAME': 'db.sqlite3', 'TEST': {'NAME': 'test.sqlite3'}"
        )
    )
    project.makepyfile(
        """
        import threading

        import pytest
        from django.db.backends.signals import connection_created
        from fastapi import FastAPI

        from bazis_test_utils.utils import get_api_client

        app = FastAPI()
        OPENED = []


        def opened(sender, connection, **kwargs):
            if threading.current_thread() is not threading.main_thread():
                OPENED.append(connection)


        connection_created.connect(opened, weak=False)


        @app.get('/')
        def users():
            from django.contrib.auth.models import User

            return {'users': User.objects.count()}


        @pytest.mark.django_db(transaction=True)
        def test_requests():
            client = get_api_client(app)
            for _ in range(20):
                assert client.get('/').json() == {'users': 0}
            # a connection per request; those of the ended threads are closed already
            assert len(OPENED) == 20
            assert sum(it.connection is not None for it in OPENED) <= 2


        def test_closed_after_the_test():
            assert OPENED and all(it.connection is None for it in OPENED)
        """
    )
    project.runpytest_subprocess('-p', 'no:cacheprovider').assert_outcomes(passed=2)
