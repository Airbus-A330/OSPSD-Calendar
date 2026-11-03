# AGENTS.md

Repository-wide guidance for contributors and coding agents.

## Scope

This repository defines the shared Calendar contract used by Teams 2, 5, and 7.

Allowed here:

- provider-independent models and validation rules;
- shared error definitions;
- provider-independent operation protocols and interfaces;
- reusable conformance tests;
- shared HTTP contract documentation.

Not allowed here:

- Google Calendar SDK or OAuth code;
- credentials, tokens, provider configuration, or secrets;
- FastAPI route or server implementations;
- team-specific adapters or business logic.

Keep the package provider-independent. Do not generalize beyond behavior required
by the approved shared contract.

## Contract Changes

Changes to public contract semantics require cross-team review. This includes
adding or removing operations, changing Event or request fields, changing
validation semantics, changing status or error meanings, changing shared error
codes, and changing request or response behavior.

The team implementing a file does not unilaterally own the public contract.
Coordinate semantic changes with every affected team and update the relevant
tests and documentation together.

## Development Expectations

- Use Python 3.12 and `uv`; do not add `requirements.txt`.
- Keep pull requests focused and easy to review.
- Keep public APIs typed.
- Add or update focused tests when behavior changes.
- Prefer simple, explicit code over unnecessary abstraction.
- Do not introduce provider dependencies or team-specific behavior.
- Do not implement future contract behavior before it has been approved.
- Run formatting, linting, type checking, and tests before requesting review.

The canonical commands are:

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

Do not commit generated build artifacts, credentials, local virtual environments,
caches, editor state, environment files, or secrets. Review the complete diff
before committing and keep `uv.lock` synchronized with `pyproject.toml`.
