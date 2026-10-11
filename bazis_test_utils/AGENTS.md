# bazis-test-utils — guide for AI agents

Test helpers for Bazis packages and projects: an API test client (`get_api_client`), and
abstract models and `factory_boy` factories of the sample entities (parent, child,
dependent, extended) used by the test suites of the Bazis packages. Install it in the
test dependencies; it brings pytest, pytest-django, pytest-mock, factory_boy and the
test client of Starlette. It does not depend on `bazis`.

## Test setup (as in the Bazis packages)

```ini
# pytest.ini at the repository root
[pytest]
DJANGO_SETTINGS_MODULE=sample.settings
```

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_app():
    from sample.main import app                # the FastAPI app: `from bazis.core.app import app`
    return app
```

Run with the `BS_*` environment of a test database: `cd sample && python -m pytest ../tests`.

## The pytest plugin

The package is a pytest plugin (entry point `pytest11` `bazis`, active once it is
installed):

- the triggers of `django-pgtrigger` (the Bazis models need them) are installed in the
  test database once it is set up, if `pgtrigger` is in `INSTALLED_APPS`; a
  `django_db_setup` of a conftest that installs them too (before 2.5) still works;
- the declarations of the code, the roles of bazis-permit (`roles.py`), the workflows
  of bazis-statusy (`workflow.py`) and the schedules of bazis-bg (`schedules.py`), are
  applied by `migrate` and `flush` (`post_migrate`), so the migrated test database has
  them, also after a test with `transaction=True`: no fixture creates the roles,
  statuses, transits or periodic tasks. `bazis_test_utils.plugin.apply_declarations(using='default')`
  applies them again with the functions `migrate` calls and forgets the cached
  permissions and content types; the fixture `bazis_declared` (needs `db`) calls it and
  gives the changes. Use it only in a test that changes the declared rows itself: with
  `--reuse-db` Django still runs `migrate` on the kept database, which applies them;
- the database connections of other threads than the one of the tests (the worker
  threads of the endpoints: a `TestClient` outside a `with` block starts new ones for
  every request) are closed when their thread has ended, after each test and before the
  test database is destroyed, so the test database is dropped at the end of the session
  and psycopg reports no unclosed connection (`ResourceWarning`). A conftest needs no
  `CONN_MAX_AGE` override nor `connections.close_all()` for it.

```python
def test_client_sees_his_tickets(bazis_declared, client_user): ...
```

## API client

```python
import pytest
from bazis_test_utils.utils import get_api_client

@pytest.mark.django_db(transaction=True)
def test_create(sample_app):
    client = get_api_client(sample_app)                 # or get_api_client(app, token)
    response = client.post('/api/v1/entity/parent_entity/', json_data={
        'data': {'type': 'entity.parent_entity', 'bs:action': 'add',
                 'attributes': {'name': 'Parent'}},
    })
    assert response.status_code == 201
```

- Methods: `get`, `post`, `patch`, `put`, `delete`, `options`, `head`; they return the
  response of the Starlette `TestClient`. `post`, `patch`, `put` take the JSON body as
  `json_data=` (not `json=`), multipart as `data=` + `files=` (then the `Content-Type`
  header is left to the client); every method takes `params=` and `headers=`.
- Requests send `Content-Type: application/vnd.api+json` (not with `files=`) and, with
  `token`, `Authorization: Bearer <token>`. With bazis-users the token is
  `user.jwt_build()`.
- The client address is `127.0.0.1`. The `TestClient` is not entered as a context
  manager, so the lifespan (startup and shutdown) of the app does not run.
- A test that calls the API uses `@pytest.mark.django_db(transaction=True)`: the
  endpoints run in worker threads with their own database connections and do not see the
  uncommitted transaction of a plain `django_db` test.

## Parallel requests

`parallel(count, func)` calls `func` `count` times, `parallel([f1, f2, ...])` calls each
function once (`bazis_test_utils.utils`), every call in a thread of its own, started
together (a barrier). It returns the results in the order of the calls; each thread closes
its database connections when its call is done; the first exception of a call is raised in
the test once all have ended. Every invariant under concurrent requests (a limit per
parent, a unique value) gets a test of parallel requests, with
`@pytest.mark.django_db(transaction=True)`: the invariant holds, and the answers are 201,
409 or 422, never 500.

```python
import pytest
from bazis_test_utils.utils import get_api_client, parallel

@pytest.mark.django_db(transaction=True)
def test_no_more_than_3_steps_per_memo(sample_app, memo):
    def add_step():
        return get_api_client(sample_app).post('/api/v1/catalog/step/', json_data={
            'data': {'type': 'catalog.step', 'relationships': {
                'memo': {'data': {'type': 'catalog.memo', 'id': str(memo.pk)}}}},
        }).status_code

    assert sorted(parallel(6, add_step)) == [201] * 3 + [422] * 3
    assert memo.steps.count() == 3
```

- Two paths that create the same item (an action and the create route) race with
  `parallel([lambda: by_action(...), lambda: by_create(...)])`.
- A 500 raises in the `TestClient` of `get_api_client`, and so in `parallel`; to assert on
  the statuses of all the responses, build `TestClient(app,
  raise_server_exceptions=False)` in the functions.

## Sample models and factories

- `bazis_test_utils.models_abstract`: `ParentEntityBase`, `ChildEntityBase`,
  `DependentEntityBase`, `ExtendedEntityBase` (plain abstract Django models). Combine them
  with the Bazis mixins and add the relations, as the sample apps do:
  `class ParentEntity(DtMixin, UuidMixin, JsonApiMixin, ParentEntityBase)` with
  `child_entities = ManyToManyField(ChildEntity, related_name='parent_entities')`;
  `DependentEntity.parent_entity` (ForeignKey, `related_name='dependent_entities'`);
  `ExtendedEntity.parent_entity` (OneToOneField, `related_name='extended_entity'`).
- `bazis_test_utils.factories_abstract`: `<Name>FactoryAbstract`; subclass each with
  `class Meta: model = ...`. `ParentEntityFactoryAbstract` creates a dependent and an
  extended entity through `tests.factories.DependentEntityFactory` and
  `tests.factories.ExtendedEntityFactory`: define them under these names in
  `tests/factories.py`.
- `ParentEntityFactory.create(child_entities=True)` adds 1–10 new children (from the
  child factory subclass of the same model); pass a child or a list of children to add
  those; omit it or pass `False` for none.
