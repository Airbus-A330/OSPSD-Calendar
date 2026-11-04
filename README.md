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

## Python API

The package exports immutable dataclasses and a string-valued error enum:

```python
from dataclasses import asdict

from calendar_contract import CalendarError, CreateEvent, ErrorCode, Event, ReplaceEvent

request = CreateEvent(
    title="  Team sync  ",
    start="2026-11-04T10:00:00-05:00",
    end="2026-11-04T15:30:00Z",
)
replacement = ReplaceEvent(**asdict(request))
event = Event(id="opaque-provider-id", **asdict(replacement))
assert event.title == "  Team sync  "

error = CalendarError(
    code=ErrorCode.INVALID_INPUT,
    message="A required field is missing.",
    retryable=False,
    details={"field": "title"},
)
```

`CreateEvent` and `ReplaceEvent` accept exactly the three shared write fields;
the provider-assigned ID is supplied separately to an operation. Both validate
the [agreed request rules](docs/HTTP_CONTRACT.md#request-bodies) at construction
and preserve the submitted strings. Timestamp comparisons account for offsets
and retain fractional precision. RFC 3339 leap-second positions are checked in
UTC, without a table of historical or future leap-second announcements.
`Event` validates string IDs/titles and timestamps, allowing an empty provider
title as required by the [title rules](docs/HTTP_CONTRACT.md#titles).

Missing or unknown constructor arguments and wrong field types raise
`TypeError`; invalid values raise `ValueError`. A service translates these into
`invalid_input` at its own boundary. This package has no HTTP or provider logic.
When consuming responses with extra fields, select the four shared fields
before constructing `Event`; the HTTP contract permits response extensions.

`CalendarError` is error data, not an exception or an HTTP response. Its five
codes are defined by the [error contract](docs/HTTP_CONTRACT.md#errors).
`retryable` is required and is never inferred from a code. In particular,
services must mark unknown write outcomes as non-retryable. `details` defaults
to `None` and has no shared schema. Callers must sanitize both messages and
details before construction; the package cannot identify arbitrary secrets.
Use `dataclasses.asdict` for serialization and omit `details` when it is `None`
if an absent optional field is preferred.

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
shared models and errors without provider credentials or network access at test time.
The model tests cover required fields, title validation, strict timestamp strings,
instant ordering, unknown write fields, and opaque IDs. Error tests cover all
shared codes, explicit retryability, and optional sanitized details.
