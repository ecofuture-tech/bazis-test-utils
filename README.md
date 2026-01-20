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
