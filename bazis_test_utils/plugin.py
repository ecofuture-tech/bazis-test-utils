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
The pytest plugin of the Bazis projects (the entry point `pytest11` `bazis`, loaded with
the package):

- the triggers of `django-pgtrigger` are installed in the test database once it is set up
  (`django_db_setup`, also when a conftest overrides it), if `pgtrigger` is installed;
- `apply_declarations()` and the fixture `bazis_declared` apply the declarations of the
  code, the roles of bazis-permit (`roles.py`) and the workflows of bazis-statusy
  (`workflow.py`), as `migrate` does, and forget the cached permissions and content types.

`migrate` and `flush` already apply the declarations (`post_migrate`), also on a database
kept by `--reuse-db` (Django runs `migrate` on it): the fixture is for a test that changes
the declared rows itself.

- the database connections opened by other threads than the one of the tests, such as the
  worker threads of the endpoints called by `get_api_client` (a `TestClient` starts new
  ones for every request), are closed once their thread has ended (when another thread
  opens one), once each test is over and before the test database is destroyed. A
  connection is kept by its thread (`CONN_MAX_AGE` of Bazis) and was left to the garbage
  collector when the thread ended: a `ResourceWarning` of the driver, and open sessions
  that kept the test database from being dropped.

Nothing of Django is imported before it is needed: the plugin is loaded in every pytest
session where the package is installed.
"""

import threading
from importlib.util import find_spec

import pytest


#: the declarations of the Bazis packages: the application and its module of declarations
DECLARATIONS = (
    ('bazis.contrib.permit', 'bazis.contrib.permit.declare'),
    ('bazis.contrib.statusy', 'bazis.contrib.statusy.declare'),
)

_TRIGGERS_INSTALLED = pytest.StashKey[bool]()

#: (thread, connection): the connections opened by other threads than the one of the tests
_thread_connections = []
_thread_connections_lock = threading.Lock()


def apply_declarations(using: str = 'default') -> list[str]:
    """
    Applies the declarations of the installed Bazis packages that have them (bazis-permit
    2.9, bazis-statusy 2.9) with their own function, the one `migrate` calls, then forgets
    the cached permissions and content types. Returns the changes.
    """
    from importlib import import_module

    from django.apps import apps

    changes = []
    for app, module in DECLARATIONS:
        if apps.is_installed(app) and find_spec(module):
            changes += import_module(module).apply_declarations(using)

    if apps.is_installed('django.contrib.contenttypes'):
        from django.contrib.contenttypes.models import ContentType

        ContentType.objects.clear_cache()
    if apps.is_installed('bazis.contrib.statusy'):
        apps.get_model('statusy.StatusyContentType').objects.clear_cache()
    if apps.is_installed('bazis.contrib.permit') and find_spec('bazis.contrib.permit.declare'):
        from bazis.contrib.permit.schemas import perms_cache_invalidate

        perms_cache_invalidate()
    return changes


@pytest.fixture
def bazis_declared(db) -> list[str]:
    """
    The declarations of the code applied to the test database (see `apply_declarations`):
    the changes it made.
    """
    return apply_declarations()


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(fixturedef, request):
    result = yield
    if fixturedef.argname == 'django_db_setup':
        if not request.config.stash.get(_TRIGGERS_INSTALLED, False):
            request.config.stash[_TRIGGERS_INSTALLED] = True
            _install_triggers(request)
            _track_thread_connections()
        # before the test database is destroyed (a finalizer added now runs before the
        # teardown of the fixture)
        fixturedef.addfinalizer(_close_thread_connections)
    return result


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    _close_thread_connections()


def _install_triggers(request) -> None:
    from django.apps import apps

    if not apps.is_installed('pgtrigger'):
        return
    from django.core.management import call_command

    with request.getfixturevalue('django_db_blocker').unblock():
        call_command('pgtrigger', 'install')


def _track_thread_connections() -> None:
    """
    Records the connections that the other threads than this one open from now on; the
    ones of the threads that have ended are closed at once, so that a test with many
    requests does not keep a session per request.
    """
    from django.db.backends.signals import connection_created

    ident = threading.get_ident()

    def opened(sender, connection, **kwargs):
        if threading.get_ident() == ident:
            return
        with _thread_connections_lock:
            ended = [it for it in _thread_connections if not it[0].is_alive()]
            _thread_connections[:] = [it for it in _thread_connections if it not in ended]
            _thread_connections.append((threading.current_thread(), connection))
        _close([it[1] for it in ended])

    connection_created.connect(opened, weak=False, dispatch_uid='bazis_test_utils.plugin')


def _close_thread_connections() -> None:
    """
    Closes the recorded connections of the other threads: their tests are over, the
    threads are done with them (a thread that uses its connection again reconnects).
    """
    with _thread_connections_lock:
        opened = [it[1] for it in _thread_connections]
        _thread_connections.clear()
    _close(opened)


def _close(connections) -> None:
    for connection in connections:
        connection.inc_thread_sharing()
        try:
            connection.close()
        finally:
            connection.dec_thread_sharing()
