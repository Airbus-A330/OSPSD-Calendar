# Calendar Python Interface

This document defines the provider-independent Python interface and reusable
conformance API shared by Teams 2, 5, and 7.

## Public API

Import `CalendarService`, `Event`, `CreateEvent`, `ReplaceEvent`, `CalendarError`,
and `ErrorCode` from `calendar_contract`. Module imports such as
`calendar_contract.service.CalendarService` remain supported.

```python
class CalendarService(Protocol):
    def create(self, request: CreateEvent) -> Event: ...
    def get(self, event_id: str) -> Event: ...
    def replace(self, event_id: str, request: ReplaceEvent) -> Event: ...
    def delete(self, event_id: str) -> None: ...
```

An implementation supplies these methods without inheriting from the protocol.
The service selects its calendar through implementation configuration; callers
supply opaque event IDs, not calendar IDs. Each service repository owns its
provider adapter, credentials, HTTP translation, and dependency injection.

`create` receives validated title/start/end values and returns the created Event
with a provider-assigned ID. Creation is not idempotent. `get` reads an existing
event. `replace` requires all shared editable fields and preserves the event ID;
what happens to extension fields remains implementation-specific. `delete`
returns `None` on success. Missing get/replace/delete operations, including a
repeated delete, raise a non-retryable `NOT_FOUND` error.

## Failures and validation

Operation failures use `CalendarError(code, message, retryable, details=None)`:

| ErrorCode | Meaning |
| --- | --- |
| `INVALID_INPUT` | A request cannot be accepted under the shared rules. |
| `NOT_FOUND` | The requested event is missing or deleted. |
| `ACCESS_DENIED` | The configured provider identity lacks permission. |
| `PROVIDER_ERROR` | An unexpected provider response or uncertain create/replace. |
| `PROVIDER_UNAVAILABLE` | Temporary provider unavailability. |

An uncertain create/replace uses `PROVIDER_ERROR` and `retryable=False`; the
implementation never automatically retries it. Sanitize messages and optional
details before exposing them externally. Translate SDK exceptions to these
shared errors. HTTP statuses and headers belong to the HTTP boundary.

Constructing an invalid Pydantic request model raises `pydantic.ValidationError`
before a service call. That is distinct from a `CalendarError` raised by an
operation. The HTTP boundary maps malformed JSON to 400 and invalid valid-JSON
input to 422, both with the shared `invalid_input` error body.

## Consumer example

```python
from calendar_contract import CalendarService, CreateEvent, Event


def create_and_read(service: CalendarService) -> Event:
    created = service.create(
        CreateEvent(
            title="Interface review",
            start="2030-01-07T15:00:00Z",
            end="2030-01-07T15:30:00Z",
        )
    )
    return service.get(created.id)
```

The caller owns cleanup for events it creates. Timestamp comparisons use
instants; equivalent output offsets are allowed. Whole-second inputs avoid
implementation-specific sub-second handling.

## Python service conformance

The suite imports this exact protocol from `calendar_contract.service`.
Subclass `CalendarServiceConformance` in a test module and provide two
fixtures: a fresh, isolated `service` returning your implementation, and
`failing_service`, a factory that takes a `ProviderFailure` and returns your
implementation on a controlled provider that fails every call that way:

```python
import pytest

from calendar_contract import CalendarService
from calendar_contract.conformance import (
    CalendarServiceConformance,
    FailingServiceFactory,
)


class TestCalendar(CalendarServiceConformance):
    @pytest.fixture
    def service(self) -> CalendarService:
        return make_isolated_service()  # Supplied by the service's tests.

    @pytest.fixture
    def failing_service(self) -> FailingServiceFactory:
        return make_failing_service  # Takes a ProviderFailure.
```

`ProviderFailure` has four members, and the suite checks each translation:

| Failure | Operations | Expected `CalendarError` |
| --- | --- | --- |
| `ACCESS_DENIED` | all four | `access_denied`, `retryable` is a bool |
| `UNEXPECTED_RESPONSE` | all four | `provider_error`, `retryable` is a bool |
| `UNAVAILABLE` | all four | `provider_unavailable`, `retryable` is a bool |
| `UNCERTAIN_WRITE` | create, replace | `provider_error`, `retryable` is `False` |

The contract fixes `retryable` only for uncertain writes, so the suite checks
only its type for the other failures. It also checks that `CreateEvent` and
`ReplaceEvent` reject representative invalid input (an unknown field, a missing
shared field) with `pydantic.ValidationError`.

Install pytest in the consuming test environment. Importing the public package
or service interface does not import the pytest-based suite. Offline checks
must use controlled providers without credentials or network access. Passing
against the suite's in-memory service does not establish Google integration.

The failure hooks live only in test fixtures. Do not add test-control methods
to the four-operation production protocol.

## HTTP conformance

`CalendarHttpConformance` verifies the externally observable shared HTTP
contract for `POST`, `GET`, `PUT`, and `DELETE`. It is framework-neutral: a
service supplies any synchronous client with the small `HttpClient` shape from
`calendar_contract.http_conformance`.

Subclass the suite and override two fixtures. `http_client` returns a client for
an isolated service instance. `failing_http_client` returns a factory that
accepts the same `ProviderFailure` values used by the Python suite and creates a
client backed by a controlled failing provider:

```python
import pytest

from calendar_contract.conformance import ProviderFailure
from calendar_contract.http_conformance import (
    CalendarHttpConformance,
    FailingHttpClientFactory,
    HttpClient,
)


class TestCalendarHttp(CalendarHttpConformance):
    @pytest.fixture
    def http_client(self) -> HttpClient:
        return make_isolated_http_client()

    @pytest.fixture
    def failing_http_client(self) -> FailingHttpClientFactory:
        return lambda failure: make_failing_http_client(failure)
```

The client must support `request(method, path, json=..., content=...,
headers=...)`, and its response must expose `status_code`, `content`, and
`json()`. A framework client such as FastAPI's `TestClient` can be returned
directly or through a small typed adapter in the consuming repository.

The HTTP suite verifies:

- all four successful operations, status codes, and shared Event fields;
- a complete create, get, replace, and delete consumer workflow;
- title, timestamp, time-range, required-field, type, and unknown-field rules;
- the distinction between malformed JSON (`400`) and valid JSON that violates
  the contract (`422`);
- missing get, replace, and delete behavior, including repeated delete;
- the shared error envelope and controlled provider-failure mappings; and
- permitted response extensions and equivalent timestamp offsets.

Each test that creates an event records its opaque ID and deletes it during
fixture teardown. Cleanup accepts `204` and `404`, so a test that already
deleted its event remains safe. Implementations should still give each test an
isolated calendar or controlled provider where practical. The normal suite is
credential-free and network-free; real-provider verification remains the
responsibility of each service repository.
