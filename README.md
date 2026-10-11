# bazis-test-utils

[![PyPI version](https://img.shields.io/pypi/v/bazis-test-utils.svg)](https://pypi.org/project/bazis-test-utils/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bazis-test-utils.svg)](https://pypi.org/project/bazis-test-utils/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A utility package for testing in the [Bazis](https://github.com/ecofuture-tech/bazis) ecosystem — a framework based on Django + FastAPI + Pydantic.

## Quick Start

```bash
# Install the package
uv add bazis-test-utils

# Create test models
from bazis_test_utils.models_abstract import ParentEntityBase

class TestEntity(ParentEntityBase):
    pass

# Use in tests
from bazis_test_utils.factories_abstract import ParentEntityFactoryAbstract

class TestEntityFactory(ParentEntityFactoryAbstract):
    class Meta:
        model = TestEntity
```

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Creating Test Models](#creating-test-models)
  - [Using Factories](#using-factories)
  - [Testing FastAPI Endpoints](#testing-fastapi-endpoints)
  - [Parallel requests](#parallel-requests)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)
- [Links](#links)

## Description

`bazis-test-utils` provides base models and factories to simplify test writing in Bazis packages. The package includes standard models for testing hierarchical and dependent entities, as well as utilities for working with the FastAPI test client.

## Features

- **Base Django test models:**
  - `ChildEntityBase` — base model for child entities
  - `DependentEntityBase` — base model for dependent entities
  - `ExtendedEntityBase` — base model for extended entities
  - `ParentEntityBase` — base model for parent entities

- **Abstract factory classes** for rapid test data generation with `factory_boy` integration

- **API testing utilities:**
  - `get_api_client()` — function to create a FastAPI test client with optional authentication
  - `parallel()` — runs calls (requests) at once in threads, for the tests of the invariants under concurrent requests


## Installation

### Using uv (recommended)

```bash
uv add bazis-test-utils
```

### Using pip

```bash
pip install bazis-test-utils
```

### Development installation

```bash
git clone https://github.com/ecofuture-tech/bazis-test-utils.git
cd bazis-test-utils
uv sync --dev
```

## Usage

### Creating Test Models

In your project, create models by inheriting from the base classes:

```python
from bazis_test_utils.models_abstract import ParentEntityBase, ChildEntityBase

class TestParentEntity(ParentEntityBase):
    """Model for testing parent entities"""
    pass

class TestChildEntity(ChildEntityBase):
    """Model for testing child entities"""
    pass
```

### Using Factories

Create factories for your models using abstract factory classes:

```python
from bazis_test_utils.factories_abstract import ParentEntityFactoryAbstract
from .models import TestParentEntity

class ParentEntityFactory(ParentEntityFactoryAbstract):
    class Meta:
        model = TestParentEntity
```

Then use them in your tests:

```python
import pytest

@pytest.mark.django_db
def test_parent_entity_creation():
    parent = ParentEntityFactory.create()
    assert parent.id is not None
    assert parent.created_at is not None
```

### Testing FastAPI Endpoints

Use `get_api_client` to create a test client:

```python
# conftest.py
import pytest

@pytest.fixture(scope='function')
def sample_app():
    from sample.main import app
    return app

# test_sample_app.py
from bazis_test_utils.utils import get_api_client

def test_api_endpoint(sample_app):
    # Without authentication
    client = get_api_client(sample_app)
    response = client.get("/api/v1/entities/")
    assert response.status_code == 200

def test_authenticated_endpoint(sample_app):
    # With authentication token
    token = "your-test-token"
    client = get_api_client(sample_app, token=token)
    response = client.get("/api/v1/protected/")
    assert response.status_code == 200
```

### Parallel requests

An invariant that must hold under concurrent requests ("no more than 3 steps per memo", a
unique value) needs a test that sends the requests at once. `parallel(count, func)` calls
`func` `count` times, `parallel([f1, f2, ...])` each function once, every call in a thread
of its own: the threads wait for each other before the calls, the results come in the
order of the calls, each thread closes its database connections when its call is done, and
the first exception of a call is raised in the test once all have ended. The endpoints see
only committed data, so such a test uses `transaction=True`:

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

Two paths that create the same item (a custom action and the create route) race with
`parallel([lambda: by_action(...), lambda: by_create(...)])`: the answers are 2xx, 409 or
422, never 500. A request that answers 500 raises in the `TestClient` of `get_api_client` (and so in
`parallel`); to count the statuses of such responses instead, call
`TestClient(app, raise_server_exceptions=False)` in the functions.

## Examples

### Basic Factory Usage

```python
from bazis_test_utils.factories_abstract import (
    ParentEntityFactoryAbstract,
    ChildEntityFactoryAbstract
)

# Create a single instance
parent = ParentEntityFactory.create(name="Test Parent")

# Create multiple instances
parents = ParentEntityFactory.create_batch(5)

# Create without saving to database
parent = ParentEntityFactory.build()
```

### Testing Hierarchical Relationships

```python
import pytest
from .factories import ParentEntityFactory, ChildEntityFactory

@pytest.mark.django_db
def test_parent_child_relationship():
    parent = ParentEntityFactory.create()
    child = ChildEntityFactory.create(parent=parent)
    
    assert child.parent == parent
    assert child in parent.children.all()
```

### Using with pytest-factoryboy

```python
# conftest.py
from pytest_factoryboy import register
from .factories import ParentEntityFactory, ChildEntityFactory

register(ParentEntityFactory)
register(ChildEntityFactory)

# test_entities.py
@pytest.mark.django_db
def test_with_fixtures(parent_entity, child_entity):
    # Fixtures are automatically created
    assert parent_entity.id is not None
    assert child_entity.id is not None
```

### API Integration Testing

```python
from bazis_test_utils.utils import get_api_client
from .factories import ParentEntityFactory

def test_crud_operations(sample_app):
    client = get_api_client(sample_app)
    
    # Create
    response = client.post("/api/v1/entities/", json={"name": "Test"})
    assert response.status_code == 201
    entity_id = response.json()["id"]
    
    # Read
    response = client.get(f"/api/v1/entities/{entity_id}/")
    assert response.status_code == 200
    
    # Update
    response = client.put(f"/api/v1/entities/{entity_id}/", json={"name": "Updated"})
    assert response.status_code == 200
    
    # Delete
    response = client.delete(f"/api/v1/entities/{entity_id}/")
    assert response.status_code == 204
```

## Usage in Bazis

This package is used in the sample project in the Bazis core to create standard test models. Models in the sample project inherit from `bazis-test-utils` models, and factories are used to generate test data across all main framework packages.

The typical workflow in Bazis packages:

1. Define concrete models in `sample/models.py` by inheriting from abstract base models
2. Create factories in `sample/factories.py` using abstract factory classes
3. Register factories in `conftest.py` for use across all tests
4. Use generated fixtures in integration and unit tests

### The pytest plugin

Installed, the package is a pytest plugin (entry point `pytest11` `bazis`):

- the triggers of `django-pgtrigger` are installed in the test database once it is set up,
  if `pgtrigger` is in `INSTALLED_APPS` (a conftest no longer overrides `django_db_setup`
  for them);
- the roles of bazis-permit (`roles.py`), the workflows of bazis-statusy (`workflow.py`)
  and the schedules of bazis-bg (`schedules.py`) declared in the code are applied by
  `migrate` and `flush`, so the test
  database has them; `bazis_test_utils.plugin.apply_declarations()` applies them again and
  forgets the cached permissions and content types, and the fixture `bazis_declared`
  calls it, for a test that changes the declared rows itself (`--reuse-db` still runs
  `migrate`, which applies them):

```python
def test_the_client_sees_his_tickets(bazis_declared, client_user):
    ...
```

- the counts of the request rate limits of Bazis (`bazis.core.throttle`, kept in Redis
  between the runs) are reset before each test by `throttle_reset()` of the core (Bazis
  2.16), so a test never inherits a 429 from the tests run before it; within a test the
  throttles count as usual, so a test of a throttle needs no fixture of its own.

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please make sure to:
- Write tests for new features
- Update documentation as needed
- Follow the existing code style
- Add your changes to the changelog

## Development

### Setup development environment

```bash
# Clone the repository
git clone https://github.com/ecofuture-tech/bazis-test-utils.git
cd bazis-test-utils

# Install dependencies with development extras
uv sync --dev

# Run linting
ruff check .

# Format code
ruff format .
```

## License

Apache License 2.0

See [LICENSE](LICENSE) file for details.

## Links

- [Bazis Framework](https://github.com/ecofuture-tech/bazis) — main repository
- [Issue Tracker](https://github.com/ecofuture-tech/bazis/issues) — report bugs or request features

## Support

If you have questions or issues, please:
- Check the [documentation](https://github.com/ecofuture-tech/bazis)
- Search [existing issues](https://github.com/ecofuture-tech/bazis/issues)
- Create a [new issue](https://github.com/ecofuture-tech/bazis/issues/new) with detailed information

---

Made with ❤️ by the Bazis team
