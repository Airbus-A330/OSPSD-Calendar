# Shared Calendar Contract

This repository contains the provider-independent Calendar contract shared by
OSPSD Teams 2, 5, and 7. It is a Python package, not a Calendar server, and must
not contain Google Calendar integration or other provider-specific behavior.

Each release is a git tag such as `v0.1.0`. Services install a tag, never a
branch (see [Installing in a service](#installing-in-a-service)).

## Agreed Common API

The required common core contains four operations:

```text
POST   /events
GET    /events/{event_id}
PUT    /events/{event_id}
DELETE /events/{event_id}
```

The common Event representation contains:

```text
id
title
start
end
```

The full HTTP behavior is in [`docs/HTTP_CONTRACT.md`](docs/HTTP_CONTRACT.md).
The shared Calendar decision memo keeps the reasoning behind each rule.

## Optional Extensions

Listing, PATCH, all-day events, richer event fields, and calendar metadata are
outside the required shared core unless the teams later agree to include them.

## Repository Scope

This repository will contain:

- shared domain and request/response models;
- shared errors;
- provider-independent operation interfaces;
- reusable conformance checks;
- shared HTTP contract documentation.

Individual service repositories remain responsible for Google Calendar
integration, authentication, FastAPI or other server implementation,
configuration, and provider-specific adapters.

## Installing in a service

Add a release tag to your service's dependencies with uv, replacing
`<release-tag>` with the newest tag on the repository's Releases page:

```bash
uv add "git+https://github.com/Airbus-A330/OSPSD-Calendar" --tag <release-tag>
```

Or with pip:

```bash
pip install "calendar-contract @ git+https://github.com/Airbus-A330/OSPSD-Calendar@<release-tag>"
```

The package ships a `py.typed` marker, so `mypy --strict` checks your code
against its types.

## Versions

Versions follow [Semantic Versioning](https://semver.org/). While the version
is below 1.0.0, a release that changes the shared contract bumps the minor
version, and any other release bumps the patch version. The full rules and the
release steps are in [`docs/RELEASING.md`](docs/RELEASING.md).

## Setup

Use Python 3.12 and [uv](https://docs.astral.sh/uv/) 0.12.17 or newer
(`pyproject.toml` requires it) from the repository root:

```bash
uv sync --locked
```

The package supports Python 3.12 and newer. CI runs the checks below on
Python 3.12, 3.13 and 3.14.

## Checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

These commands verify formatting, linting, typing, package installation, and the
initial smoke test without provider credentials or network access at test time.
