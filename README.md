# Shared Calendar Contract

This repository contains the provider-independent Calendar contract shared by
OSPSD Teams 2, 5, and 7. It is a Python package, not a Calendar server, and must
not contain Google Calendar integration or other provider-specific behavior.

Version `0.1.0` currently identifies the initial package scaffold. It is not a
completed shared-contract release.

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

Detailed behavior is governed by the shared Calendar decision memo. Code and
documentation in this repository will implement that approved agreement.

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

## Setup

Use Python 3.12 and [uv](https://docs.astral.sh/uv/) from the repository root:

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
