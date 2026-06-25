---
name: uv-env
description: Rules for managing Python environments and packages with uv. Governs environment creation, package installation, build isolation, package updates, and publishing to PyPI.
license: MIT
---

# Python Environment Management with uv

Rules for how a coding agent should manage Python environments and packages using uv. The guiding principle: **always use uv — never fall back to pip or venv directly.**

## 1. Always Create Environments with uv

Python virtual environments must always be created using `uv`:

```bash
uv venv
```

or as part of a project:

```bash
uv init
```

- Never use `python -m venv`, `virtualenv`, or `conda` unless the user explicitly requests it.
- If a `.venv` already exists, check whether it was created by uv before recreating it.

## 2. Check for uv Before Doing Anything

Before running any uv command, verify that `uv` is available on the PATH:

```bash
which uv
```

If uv is **not found**, stop and inform the user:

> "`uv` was not found on your PATH. Please install it (e.g. `curl -Ls https://astral.sh/uv/install.sh | sh`) or provide the full path to the uv executable."

Do not attempt to fall back to pip or venv. Wait for the user to resolve the issue.

## 3. Install Packages with `uv add`

To add a dependency to a project, use:

```bash
uv add <package>
```

- **Do not use `uv pip install`** except in exceptional cases (e.g., installing a local editable package outside a project context, or when `uv add` is not applicable). If you must use it, inform the user why.
- `uv add` keeps `pyproject.toml` and the lockfile in sync automatically.
- To add a dev dependency: `uv add --dev <package>`
- To add an optional dependency group: `uv add --optional <group> <package>`

## 4. Handle Build Isolation Issues

Some packages (e.g., those requiring pre-installed system libraries or custom build backends) may fail when build isolation is enabled. If a package fails to install and the error suggests a build isolation problem:

1. Inform the user:
   > "Installing `<package>` failed, likely due to build isolation. This means the build backend cannot access pre-installed system libraries or packages."

2. Offer two remedies:

   **Option A — flag per install:**
   ```bash
   uv add <package> --no-build-isolation
   ```

   **Option B — configure in `pyproject.toml`** (preferred for reproducibility):
   ```toml
   [tool.uv]
   no-build-isolation-package = ["<package>"]
   ```

3. Always tell the user which option you are applying and why, so they can make an informed decision.

## 5. Updating Packages

When the user asks to update a package:

1. **Search online** for the latest released version of the package (check PyPI or the project's release page).
2. Check the current version in `pyproject.toml` or `uv.lock`.
3. Assess compatibility: review the package's changelog or release notes for breaking changes relative to the current version and the project's Python version and other dependencies.
4. Report findings to the user before making any changes:
   > "The latest version of `<package>` is `X.Y.Z` (current: `A.B.C`). There are [no / the following] breaking changes: ..."
5. Only proceed with the update after the user confirms.

To update:

```bash
uv add <package>@latest
```

or pin to a specific version:

```bash
uv add <package>==X.Y.Z
```

## 6. Publishing to PyPI

To publish a package, use the uv build and publish workflow:

```bash
uv build
uv publish
```

### Before Building

- Check for existing build artifacts in the `dist/` directory.
- If `dist/` contains files, **prompt the user**:
  > "The `dist/` directory already contains build artifacts. Publishing with stale builds can cause the wrong version to be uploaded. Should I remove them before building?"
- Only remove `dist/` contents after explicit user confirmation.

### Build and Publish Steps

```bash
# 1. (Optional, after user confirms) Remove stale artifacts
rm -rf dist/

# 2. Build source distribution and wheel
uv build

# 3. Publish to PyPI
uv publish
```

- To publish to TestPyPI first (recommended for first-time or major releases):
  ```bash
  uv publish --index testpypi
  ```
- Credentials can be passed via environment variables (`UV_PUBLISH_TOKEN`) or a `~/.pypirc` file. Never hardcode credentials.

## Quick Reference

| Task | Command |
|---|---|
| Create environment | `uv venv` |
| Initialize project | `uv init` |
| Add a dependency | `uv add <package>` |
| Add a dev dependency | `uv add --dev <package>` |
| Install without build isolation | `uv add <package> --no-build-isolation` |
| Run a script in the env | `uv run <script>` |
| Update a package | `uv add <package>@latest` |
| Build for distribution | `uv build` |
| Publish to PyPI | `uv publish` |
| Publish to TestPyPI | `uv publish --index testpypi` |
