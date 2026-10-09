# bazis-test-utils

Test helpers shared by the Bazis packages: abstract test models, `factory_boy` factories,
an API test client (`bazis_test_utils/utils.py`) and a pytest plugin
(`bazis_test_utils/plugin.py`, entry point `pytest11`: the pgtrigger triggers of the test
database, `apply_declarations` and the fixture `bazis_declared`). Every Bazis package
depends on it through its `test` extra and loads the plugin, so a change here affects all
their test suites. The plugin imports nothing of Django or Bazis at import time.

## Checks

```bash
ruff check bazis_test_utils tests
python -m pytest tests
```

`tests/` runs the plugin in pytester subprocesses (Django with SQLite, no Bazis package).
CI also imports the modules and exercises `get_api_client` on Python 3.12–3.14 with the
highest and the lowest allowed dependency versions, and builds the distribution. Changes
should also be checked against the test suites of the Bazis packages.

## Releasing

A release is the tag `vX.Y.Z` on `main`: the Build and Publish workflow builds the package
(the version comes from the tag through setuptools-scm) and publishes it to PyPI
(pre-releases `-alphaN`/`-betaN`/`-rcN` go to Test PyPI) and creates the GitHub release.

Claude Code sessions cannot push tags. Release through the **Release** workflow instead:

1. Make sure the changes are merged into `main` and the Tests workflow is green on the
   `main` head commit (the Release workflow checks this and refuses otherwise).
2. Add the release notes as `docs/releases/X.Y.Z.md` in the change being released.
3. Start the workflow `release.yml` on `ref: main` with the input `version: X.Y.Z`
   (GitHub API: `POST /repos/ecofuture-tech/bazis-test-utils/actions/workflows/release.yml/dispatches`;
   with the GitHub MCP tools: `actions_run_trigger`, method `run_workflow`).
4. The Release run creates the annotated tag and starts Build and Publish on it. Check
   that both runs succeed and that the version appears on https://pypi.org/project/bazis-test-utils/.

Release the Bazis packages in dependency order: a package is tested in CI against the
versions of its Bazis dependencies published on PyPI. Pick the version by semver:
breaking changes (settings renamed or required, dependency removed, behavior changed)
bump the minor version while the project is below 3.0.
