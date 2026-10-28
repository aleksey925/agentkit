---
name: py-bootstrap
description: "Help bootstrap a Python project or apply best practices to an existing one"
---

## Task
Analyze the current project and apply my Python project configuration standards.

## User's Stack & Preferences

### Tool Management: mise
I use `mise` for managing tool versions (python, node, uv, etc).

**Default mise.toml:**
```toml
[[env]]
_.python.venv = { path = ".venv", create = true }

[[env]]
_.source = { path = ".env.sh", tools = true }

[[env]]
_.file = { path = ".env", tools = true }

[tools]
python = "3.13"  # adjust based on project requirements
```

**Additional section for UV projects:**
If the project uses `uv` as package manager, also add:
```toml
[settings.python]
uv_venv_create_args = ['--seed']  # tell uv to create new venv with pip
```

**Important:** Never use `latest` in mise.toml — always specify exact version numbers. To get the current latest version of a tool, run: `mise latest <tool>`

### .gitignore
Ensure `.gitignore` contains these entries (add if missing):
```gitignore
.env
.env.sh
```
Keep `.env` and `.env.sh` together in the gitignore file.

### Package Manager: uv
I use `uv` as my primary Python package manager.

Key commands:
- `uv init` - initialize new project
- `uv add <package>` - add dependency
- `uv add --dev <package>` - add dev dependency
- `uv sync` - sync dependencies
- `uv lock` - update lock file
- `uv run <command>` - run command in venv

**pyproject.toml configuration for dev dependencies:**
```toml
[dependency-groups]
dev = []

[tool.uv]
default-groups = ["dev"]
```

All dev dependencies should be added to the `dev` group (using `uv add --dev`), and this group is marked as default so it's installed automatically with `uv sync`.

### Dev Dependencies: ruff, mypy, prek, pyproject-fmt
These tools are always installed as dev dependencies in pyproject.toml with exact pinned versions.

**IMPORTANT:** Before adding these dependencies, always check PyPI for the latest versions:
- https://pypi.org/project/ruff/
- https://pypi.org/project/mypy/
- https://pypi.org/project/prek/
- https://pypi.org/project/pyproject-fmt/

Example (versions may be outdated — always verify):
```toml
[dependency-groups]
dev = [
    "ruff==0.14.10",
    "mypy==1.19.1",
    "prek==0.5.4",
    "pyproject-fmt==2.7.0",
]
```

**Rules:**
- Always use exact versions (`==`), never use `>=`, `^`, or `~`
- Never rely on versions in this prompt — they may be outdated
- Install via `uv add --dev ruff==<version> mypy==<version> prek==<version> pyproject-fmt==<version>`

**Note on prek:** `prek` is a drop-in replacement for `pre-commit` written in Go. It's faster and has no Python dependencies. The config file remains `.pre-commit-config.yaml` and uses the same format. If project currently uses `pre-commit`, consider migrating to `prek` (see Migration section).

### Linting: ruff
**pyproject.toml configuration:**
```toml
[tool.ruff]
target-version = "py313"
line-length = 120  # If another string length was used in the project, use it

[tool.ruff.format]
quote-style = "single"  # Before adding it, ask, because sometimes I need to use "double"

[tool.ruff.lint]
select = [
    "A",        # flake8-builtins
    "E",        # pycodestyle errors
    "W",        # pycodestyle warnings
    "F",        # pyflakes
    "I",        # isort
    "N",        # pep8-naming
    "T20",      # flake8-print
    "C90",      # flake8-complexity (mccabe)
    "UP",       # pyupgrade
    "RUF",      # ruff
    "S",        # flake8-bandit
    "PLC0415",  # import-outside-top-level
]
ignore = [
    "A003",  # class attribute {name} is shadowing a python builtin
    "S101",  # use of assert detected
    "S104",  # binding to all interfaces — safe for dockerized apps
]
```

### Type Checking: mypy
**pyproject.toml configuration:**
```toml
[tool.mypy]
python_version = "<adjust to project's python version>"
plugins = ["pydantic.mypy"]  # ONLY if pydantic is a dependency!
strict = true
show_error_codes = true
no_implicit_optional = false
```

**Important notes:**
- `python_version` must match the project's actual Python version (from mise.toml or pyproject.toml)
- `plugins = ["pydantic.mypy"]` should ONLY be added if `pydantic` is in the project dependencies
- If pydantic is not used, omit the `plugins` line entirely

### Makefile

| Target   | Purpose                              | When needed              |
|----------|--------------------------------------|--------------------------|
| deps     | Install/sync dependencies            | Always                   |
| test     | Run tests                            | Always                   |
| lint     | Run linters and formatters           | Always                   |
| test-int | Run integration tests only           | With integration tests   |
| test-all | Run all tests (unit + integration)   | With integration tests   |
| db-up    | Apply database migrations            | With DB migrations       |
| db-rev   | Create new migration                 | With DB migrations       |
| img      | Build Docker image                   | With Dockerfile          |
| build    | Build package                        | Libraries                |
| publish  | Publish to PyPI                      | Libraries                |

**Core targets (always add):**
```makefile
deps:
	uv sync --all-extras

test:
	uv run pytest

lint:
	@uv run prek run --all-files
```

**If project separates unit/integration tests:**
```makefile
test-int:
	uv run pytest -m integration

test-all:
	uv run pytest -m ''
```

**If project uses alembic for DB migrations:**
```makefile
db-up:
	@uv run alembic upgrade head

db-rev:
	@if [ -z "$(msg)" ]; then \
		uv run alembic revision --autogenerate ; \
	else \
		uv run alembic revision --autogenerate -m "$(msg)" ; \
	fi
```

Usage: `make db-rev` or `make db-rev msg="add users table"`

**If project has Dockerfile:**
```makefile
img:
	docker build -t $(IMAGE_NAME) .
```

**If project is a library published to PyPI:**
```makefile
build:
	uv build

publish:
	uv publish
```

**Notes:**
- Marker names may vary (`integration`, `slow`, `db`, etc.) — adapt to project conventions
- When existing project uses different target names, suggest renaming for consistency, but don't force
- `img` is the preferred target name for building Docker images; `image` is also acceptable

### Prek Hooks

**Installation:**
prek is installed as a dev dependency in pyproject.toml (see "Dev Dependencies" section above).

**IMPORTANT:** Only include hooks and parameters that are relevant to the project. Don't add hooks for file types that don't exist in the project (e.g., don't add JSON formatting if there are no JSON files). The config below is a template — adjust based on actual project needs.

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: builtin
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
        exclude: helm|helmfile.yaml  # ONLY if helm files exist
      - id: detect-private-key
      - id: check-yaml
        exclude: helm|helmfile.yaml  # ONLY if helm files exist

  - repo: https://github.com/google/yamlfmt
    rev: v0.20.0  # check latest at https://github.com/google/yamlfmt/releases
    hooks:
      - id: yamlfmt
        args: [-formatter, retain_line_breaks_single=true]
        exclude: helm|helmfile.yaml  # ONLY if helm files exist

  - repo: local
    hooks:
      - id: prettier
        name: prettier
        language: system
        entry: prettier --write --prose-wrap always --print-width 79
        files: ^README\.md$

      - id: name-tests
        name: check test naming
        entry: |
          bash -c '
            pattern="${1:-prefix}"
            shift
            for f in "$@"; do
              b=$(basename "$f")
              [[ "$b" == conftest.py ]] || [[ "$b" == __init__.py ]] && continue
              if [[ "$pattern" == "prefix" ]]; then
                [[ "$b" =~ ^test_.*\.py$ ]] || { echo "ERROR: $f should be test_*.py"; exit 1; }
              else
                [[ "$b" =~ .*_test\.py$ ]] || { echo "ERROR: $f should be *_test.py"; exit 1; }
              fi
            done
          ' --
        language: system
        files: ^tests/.*\.py$
        # exclude: <add patterns for test helpers/fixtures if needed>
        args: [prefix]  # set prefix or suffix based on project convention

      - id: ruff-format
        name: ruff-format
        language: system
        entry: ruff format
        types: [python]

      - id: ruff
        name: ruff
        language: system
        entry: ruff check --fix
        types: [python]

      - id: lock-file-check
        name: lock file check
        language: system
        entry: uv lock --check
        pass_filenames: false
        files: ^(pyproject\.toml|.*\.lock)$

      - id: pyproject-fmt
        name: pyproject-fmt
        language: system
        entry: pyproject-fmt --no-generate-python-version-classifiers  # remove --no-generate-python-version-classifiers for libraries
        files: ^pyproject\.toml$

      - id: mypy
        name: mypy
        language: system
        require_serial: true
        entry: mypy
        pass_filenames: false
        types: [python]
        args: ["<source_directory>"]  # replace with actual source dir
```

**Notes on hooks:**
- `yamlfmt` is always useful since `.pre-commit-config.yaml` itself is YAML
- `builtin` hooks are native to prek (no Python dependencies, faster)
- `exclude` patterns should only be added if those files/dirs exist in the project
- `name-tests` args: use `prefix` for `test_*.py` or `suffix` for `*_test.py` naming convention
- `prettier` is installed via `mise.toml` (not as a Python dev dependency) and formats `README.md`. Useful in projects that contain `README.md`
- Check latest `yamlfmt` version before adding: https://github.com/google/yamlfmt/releases

**Migrating from pre-commit:**
If project uses `pre-commit`, migrate to `prek`:
1. Replace `pre-commit` with `prek` in dev dependencies
2. Update `.pre-commit-config.yaml`:
   - Replace `repo: https://github.com/pre-commit/pre-commit-hooks` with `repo: builtin`
   - Replace `name-tests-test` hook with custom `name-tests` hook (see config above)
3. Update Makefile: replace `pre-commit run --all` with `prek run --all-files`
4. Update any CI scripts that reference `pre-commit`

**Why prek?** Drop-in replacement written in Go — faster, no Python dependencies, more stable.

## Behavior Rules

### Default Behavior (no migration)
By default, DO NOT migrate between tools. For example:
- If project uses `poetry` → keep poetry, just update configs
- If project uses `pip`/`requirements.txt` → keep it unless explicitly asked
- If project uses different linter → add ruff config alongside or skip
- **If project uses `pre-commit`** → ask user if they want to migrate to `prek` (see "Migrating from pre-commit" in Prek Hooks section)

### What to do by default:
1. **Analyze** current project structure and tools
2. **Update/Add** configurations that don't conflict:
   - Add missing ruff rules to existing ruff config
   - Add missing mypy settings to existing mypy config
   - **Check for latest versions of prek hooks** (search GitHub for latest releases)
   - Update prek hook versions to latest
   - Add missing prek hooks
   - Add/update mise.toml if not present
   - Add/update Makefile with standard targets
3. **Report** what was changed and what was skipped

### Hook Versions
**IMPORTANT:** Always check for the latest versions before adding hooks:
- `yamlfmt` → https://github.com/google/yamlfmt/releases

Don't rely on hardcoded versions in this prompt — they may be outdated.

**Note:** ruff runs as a local system hook (see prek config above), not as a separate repo hook.

### Migration (only when explicitly requested):
When user explicitly asks to migrate (e.g., "migrate from poetry to uv"):
1. Convert dependency definitions
2. Remove old config files (poetry.lock, etc.)
3. Create new lock file
4. Update prek hooks accordingly
5. Update any scripts/CI that reference old tool
6. **Check Dockerfile** — if exists, update package manager usage (see Docker section below)

### Docker
**IMPORTANT:** Always verify that the package manager version in Dockerfile matches the local version. This ensures consistent behavior between local development and Docker builds, regardless of how the local version is defined (mise.toml, .tool-versions, or other means).

#### Extracting versions from mise.toml
Copy mise.toml into the build stage and extract tool versions via sed, then install via pip. This is simpler and faster than installing mise itself:

```dockerfile
FROM python:3.13-slim-bookworm AS exporter

WORKDIR /opt/app/

# install package manager (changes rarely — cached separately)
COPY mise.toml ./
RUN UV_VERSION=$(sed -n 's/^uv = "\(.*\)"/\1/p' mise.toml) && \
    pip install --no-cache-dir uv==${UV_VERSION}

# export dependencies (changes more often)
COPY pyproject.toml uv.lock* ./
RUN uv export -o requirements.txt --no-default-groups --no-hashes --no-annotate --frozen --no-emit-project
```

**Notes:**
- Adjust Python version in base image to match project requirements
- For poetry: `POETRY_VERSION=$(sed -n 's/^poetry = "\(.*\)"/\1/p' mise.toml)` and `pip install poetry==${POETRY_VERSION}`
- The sed pattern expects format `tool = "version"` in mise.toml

#### Common: installing dependencies in final stage
```dockerfile
RUN pip install --no-cache-dir -r /opt/app/requirements.txt && \
    (find /usr/local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true) && \
    rm -rf /root/.cache /tmp/*
```
This cleans up caches to reduce image size.

When reviewing Dockerfile, check:
- Package manager version matches local version (not hardcoded to an arbitrary value)
- Correct lock file is used (uv.lock, poetry.lock, etc.)
- Correct export command is used (uv export, poetry export, etc.)

### GitHub Actions Workflows (for libraries)

**Note:** This section applies specifically to Python **libraries** that are published to PyPI. For web applications, CLI tools, or internal packages, the workflow may differ significantly (no PyPI release, different deployment targets, etc.).

#### When to apply:
- Project is a **library** intended for PyPI publication
- Has `[build-system]` in pyproject.toml
- Uses semantic versioning with git tags (e.g., `v1.0.0`)

#### CI Workflow (.github/workflows/ci.yml)

Runs on pull requests and pushes to master. Includes lint and tests on multiple Python versions.

```yaml
name: ci

on:
  pull_request:
    branches:
      - "*"
  push:
    branches:
      - "master"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Install tools
        uses: jdx/mise-action@v3

      - name: Install dependencies
        run: make deps

      - name: Run lint
        run: make lint

  test:
    strategy:
      matrix:
        py_version: ["3.11", "3.12", "3.13"]  # adjust based on requires-python
        os: [ubuntu-latest]
    runs-on: "${{ matrix.os }}"
    steps:
      - uses: actions/checkout@v5

      - name: Install tools
        uses: jdx/mise-action@v3
        with:
          install_args: python@${{ matrix.py_version }} uv

      - name: Install dependencies
        run: make deps

      - name: Run tests
        run: make test
```

**Notes:**
- Adjust `py_version` matrix to match `requires-python` from pyproject.toml
- If project has integration tests, add separate `test-integration` job with docker-compose

#### Release Workflow (.github/workflows/release.yml)

Triggered by pushing version tags. Publishes to PyPI and uploads artifacts to GitHub Release.

```yaml
name: release

on:
  push:
    tags:
      - "v*"

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0  # required for hatch-vcs

      - name: Install tools
        uses: jdx/mise-action@v3

      - name: Install dependencies
        run: make deps

      - name: Build package
        run: make build

      - name: Publish to PyPI
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: make publish

      - name: Upload to GitHub Release
        env:
          GH_TOKEN: ${{ github.token }}
        run: gh release upload ${{ github.ref_name }} dist/* --clobber
```

**Required setup:**
- Create `PYPI_TOKEN` secret in repository settings
- Create GitHub Release **before** pushing the tag (workflow uploads artifacts to existing release)
- Add `build` and `publish` targets to Makefile (see Makefile section above)

#### Dynamic Versioning (hatch-vcs)

Version is derived from git tags instead of hardcoded in pyproject.toml.

**pyproject.toml changes:**
```toml
[build-system]
build-backend = "hatchling.build"
requires = [ "hatch-vcs", "hatchling" ]

[project]
name = "mylib"
dynamic = [ "version" ]  # instead of version = "1.0.0"
# ... rest of metadata

[tool.hatch.version]
source = "vcs"
tag-pattern = "^v(?P<version>.*)$"  # strips 'v' prefix from tags
```

**How it works:**
- Tag `v1.0.0` → package version `1.0.0`
- Tag `v0.1.0a1` → package version `0.1.0a1`
- Between tags → version like `0.1.0a1.dev3+g1234567`

#### PyPI Package Metadata

For proper display on PyPI, add these fields to `[project]`:

```toml
[project]
name = "mylib"
description = "Short description"
readme = "README.md"
license = "MIT"
keywords = [ "keyword1", "keyword2" ]
authors = [ { name = "Name", email = "email@example.com" } ]
requires-python = ">=3.11"
classifiers = [
  "Development Status :: 3 - Alpha",  # or 4 - Beta, 5 - Production/Stable
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Operating System :: OS Independent",
  "Topic :: Software Development :: Libraries :: Python Modules",
  "Typing :: Typed",
]
dynamic = [ "version" ]

urls.Homepage = "https://github.com/user/repo"
urls.Repository = "https://github.com/user/repo"
urls.Issues = "https://github.com/user/repo/issues"
```

#### PEP 561 Typed Package Marker

For typed libraries, create empty marker file:

```bash
touch src/mylib/py.typed
```

This signals to type checkers (mypy, pyright) that the package includes inline type annotations.

## Arguments

$ARGUMENTS

## Instructions

1. First, scan the project to understand current setup:
   - Check for pyproject.toml, setup.py, requirements.txt
   - Identify current package manager (uv, poetry, pip, etc.)
   - Check existing linter/formatter configs
   - Check for prek/pre-commit config
   - Check for mise.toml or .tool-versions

2. Based on $ARGUMENTS, determine the action:
   - Empty/default → update existing configs, add missing ones
   - "init" or "new" → full initialization for new project
   - "migrate to uv" → migrate from current tool to uv
   - "migrate to poetry" → migrate to poetry
   - "add hooks" → only add/update prek hooks
   - "add ruff" → only add/update ruff config
   - "add mypy" → only add/update mypy config

3. Execute the appropriate actions following the behavior rules above.

4. After changes, provide a summary:
   - What was added/updated
   - What was skipped and why
   - Any manual steps needed (like running `uv sync`)
