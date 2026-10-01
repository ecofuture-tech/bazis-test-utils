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
from django.core.management import call_command
import pytest

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('pgtrigger', 'install')   # the triggers of the Bazis models

@pytest.fixture
def sample_app():
    from sample.main import app                # the FastAPI app: `from bazis.core.app import app`
    return app
```

Run with the `BS_*` environment of a test database: `cd sample && python -m pytest ../tests`.

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
