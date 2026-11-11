"""Reusable HTTP conformance tests for shared Calendar implementations.

Subclass :class:`CalendarHttpConformance` and override the ``http_client``
fixture with a client for the implementation under test. The client only needs
the small structural interface declared here; no HTTP framework is required by
the shared package.
"""

from collections.abc import Callable, Iterator, Mapping
from datetime import datetime
from typing import Protocol

import pytest

from calendar_contract.conformance import ProviderFailure


class HttpResponse(Protocol):
    """HTTP response behavior used by the conformance suite."""

    status_code: int

    @property
    def content(self) -> bytes:
        """Return the raw response body."""
        ...

    def json(self) -> object:
        """Return the decoded JSON response body."""
        ...


class HttpClient(Protocol):
    """Minimal synchronous HTTP client behavior used by the suite."""

    def request(
        self,
        method: str,
        path: str,
        /,
        *,
        json: object | None = None,
        content: bytes | str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> HttpResponse:
        """Send one request to the implementation under test."""
        ...


FailingHttpClientFactory = Callable[[ProviderFailure], HttpClient]


CREATE_BODY: dict[str, object] = {
    "title": "Conformance event",
    "start": "2030-01-07T15:00:00Z",
    "end": "2030-01-07T15:30:00Z",
}
REPLACE_BODY: dict[str, object] = {
    "title": "Conformance event (replaced)",
    "start": "2030-01-07T16:00:00+01:00",
    "end": "2030-01-07T17:00:00+01:00",
}

INVALID_BODIES = (
    pytest.param(
        {"start": CREATE_BODY["start"], "end": CREATE_BODY["end"]},
        id="missing-title",
    ),
    pytest.param({**CREATE_BODY, "title": None}, id="null-title"),
    pytest.param({**CREATE_BODY, "title": 7}, id="non-string-title"),
    pytest.param({**CREATE_BODY, "title": ""}, id="empty-title"),
    pytest.param({**CREATE_BODY, "title": "   "}, id="blank-title"),
    pytest.param(
        {"title": CREATE_BODY["title"], "end": CREATE_BODY["end"]},
        id="missing-start",
    ),
    pytest.param({**CREATE_BODY, "start": None}, id="null-start"),
    pytest.param(
        {"title": CREATE_BODY["title"], "start": CREATE_BODY["start"]},
        id="missing-end",
    ),
    pytest.param({**CREATE_BODY, "end": None}, id="null-end"),
    pytest.param({**CREATE_BODY, "start": "2030-01-07T15:00:00"}, id="no-offset"),
    pytest.param({**CREATE_BODY, "start": "not-a-timestamp"}, id="bad-timestamp"),
    pytest.param({**CREATE_BODY, "start": 1894028400}, id="numeric-timestamp"),
    pytest.param({**CREATE_BODY, "end": CREATE_BODY["start"]}, id="equal-time-range"),
    pytest.param(
        {
            **CREATE_BODY,
            "start": "2030-01-07T16:00:00Z",
            "end": "2030-01-07T15:00:00Z",
        },
        id="reversed-time-range",
    ),
    pytest.param({**CREATE_BODY, "location": "Room 101"}, id="unknown-field"),
)


def _same_instant(actual: str, expected: object) -> bool:
    """Return whether two RFC 3339 strings represent the same instant."""
    assert isinstance(expected, str)
    return datetime.fromisoformat(actual) == datetime.fromisoformat(expected)


def _event_body(
    response: HttpResponse, expected: Mapping[str, object]
) -> dict[str, object]:
    """Validate and return a successful shared Event response body."""
    body = response.json()
    assert isinstance(body, dict)
    for field in ("id", "title", "start", "end"):
        assert isinstance(body.get(field), str)
    assert body["id"]
    assert body["title"] == expected["title"]
    assert _same_instant(body["start"], expected["start"])
    assert _same_instant(body["end"], expected["end"])
    return body


def _error_body(
    response: HttpResponse, status: int, code: str, retryable: bool | None
) -> dict[str, object]:
    """Validate and return a shared error response body."""
    assert response.status_code == status
    body = response.json()
    assert isinstance(body, dict)
    error = body.get("error")
    assert isinstance(error, dict)
    assert error.get("code") == code
    assert isinstance(error.get("message"), str)
    assert error["message"]
    if retryable is None:
        assert isinstance(error.get("retryable"), bool)
    else:
        assert error.get("retryable") is retryable
    return error


def _call_operation(client: HttpClient, operation: str) -> HttpResponse:
    """Call one shared operation with valid input."""
    if operation == "create":
        return client.request("POST", "/events", json=CREATE_BODY)
    if operation == "get":
        return client.request("GET", "/events/conformance-event")
    if operation == "replace":
        return client.request("PUT", "/events/conformance-event", json=REPLACE_BODY)
    return client.request("DELETE", "/events/conformance-event")


class CalendarHttpConformance:
    """Shared externally observable HTTP behavior for Calendar services."""

    @pytest.fixture
    def http_client(self) -> HttpClient:
        """Return the client under test; subclasses must override this fixture."""
        raise NotImplementedError("override the `http_client` fixture")

    @pytest.fixture
    def failing_http_client(self) -> FailingHttpClientFactory:
        """Return controlled failing clients; subclasses must override this fixture."""
        raise NotImplementedError("override the `failing_http_client` fixture")

    @pytest.fixture
    def created_ids(self, http_client: HttpClient) -> Iterator[list[str]]:
        """Track created IDs and remove any events left after a test."""
        ids: list[str] = []
        yield ids
        for event_id in ids:
            response = http_client.request("DELETE", f"/events/{event_id}")
            assert response.status_code in (204, 404)

    @pytest.fixture
    def created_event(
        self, http_client: HttpClient, created_ids: list[str]
    ) -> dict[str, object]:
        """Create and track one event for a test."""
        response = http_client.request("POST", "/events", json=CREATE_BODY)
        assert response.status_code == 201
        event = _event_body(response, CREATE_BODY)
        created_ids.append(str(event["id"]))
        return event

    @pytest.fixture
    def missing_id(self, http_client: HttpClient) -> str:
        """Return the opaque ID of an event that has already been deleted."""
        created = http_client.request("POST", "/events", json=CREATE_BODY)
        assert created.status_code == 201
        event = _event_body(created, CREATE_BODY)
        event_id = str(event["id"])
        deleted = http_client.request("DELETE", f"/events/{event_id}")
        assert deleted.status_code == 204
        return event_id

    def test_create_returns_201_and_shared_event(
        self, http_client: HttpClient, created_ids: list[str]
    ) -> None:
        response = http_client.request("POST", "/events", json=CREATE_BODY)
        assert response.status_code == 201
        event = _event_body(response, CREATE_BODY)
        created_ids.append(str(event["id"]))

    def test_get_returns_200_and_created_event(
        self, http_client: HttpClient, created_event: dict[str, object]
    ) -> None:
        response = http_client.request("GET", f"/events/{created_event['id']}")
        assert response.status_code == 200
        event = _event_body(response, CREATE_BODY)
        assert event["id"] == created_event["id"]

    def test_replace_returns_200_preserves_id_and_persists_values(
        self, http_client: HttpClient, created_event: dict[str, object]
    ) -> None:
        path = f"/events/{created_event['id']}"
        response = http_client.request("PUT", path, json=REPLACE_BODY)
        assert response.status_code == 200
        replaced = _event_body(response, REPLACE_BODY)
        assert replaced["id"] == created_event["id"]

        fetched = http_client.request("GET", path)
        assert fetched.status_code == 200
        assert _event_body(fetched, REPLACE_BODY)["id"] == created_event["id"]

    def test_delete_returns_204_with_no_body_and_removes_event(
        self, http_client: HttpClient, created_event: dict[str, object]
    ) -> None:
        path = f"/events/{created_event['id']}"
        response = http_client.request("DELETE", path)
        assert response.status_code == 204
        assert response.content == b""
        _error_body(http_client.request("GET", path), 404, "not_found", False)

    @pytest.mark.parametrize("method", ("GET", "DELETE"))
    def test_missing_event_returns_not_found(
        self, http_client: HttpClient, missing_id: str, method: str
    ) -> None:
        response = http_client.request(method, f"/events/{missing_id}")
        _error_body(response, 404, "not_found", False)

    def test_replace_missing_event_returns_not_found(
        self, http_client: HttpClient, missing_id: str
    ) -> None:
        response = http_client.request(
            "PUT", f"/events/{missing_id}", json=REPLACE_BODY
        )
        _error_body(response, 404, "not_found", False)

    def test_repeated_delete_returns_not_found(
        self, http_client: HttpClient, created_event: dict[str, object]
    ) -> None:
        path = f"/events/{created_event['id']}"
        assert http_client.request("DELETE", path).status_code == 204
        _error_body(http_client.request("DELETE", path), 404, "not_found", False)

    @pytest.mark.parametrize("body", INVALID_BODIES)
    def test_create_rejects_valid_json_that_breaks_contract_rules(
        self, http_client: HttpClient, body: dict[str, object]
    ) -> None:
        response = http_client.request("POST", "/events", json=body)
        _error_body(response, 422, "invalid_input", False)

    @pytest.mark.parametrize("body", INVALID_BODIES)
    def test_replace_rejects_valid_json_that_breaks_contract_rules(
        self,
        http_client: HttpClient,
        created_event: dict[str, object],
        body: dict[str, object],
    ) -> None:
        response = http_client.request(
            "PUT", f"/events/{created_event['id']}", json=body
        )
        _error_body(response, 422, "invalid_input", False)

    def test_create_rejects_malformed_json(self, http_client: HttpClient) -> None:
        response = http_client.request(
            "POST",
            "/events",
            content=b'{"title":',
            headers={"content-type": "application/json"},
        )
        _error_body(response, 400, "invalid_input", False)

    def test_replace_rejects_malformed_json(
        self, http_client: HttpClient, created_event: dict[str, object]
    ) -> None:
        response = http_client.request(
            "PUT",
            f"/events/{created_event['id']}",
            content=b'{"title":',
            headers={"content-type": "application/json"},
        )
        _error_body(response, 400, "invalid_input", False)

    @pytest.mark.parametrize("operation", ("create", "get", "replace", "delete"))
    def test_access_denied_uses_shared_http_error(
        self, failing_http_client: FailingHttpClientFactory, operation: str
    ) -> None:
        response = _call_operation(
            failing_http_client(ProviderFailure.ACCESS_DENIED), operation
        )
        _error_body(response, 403, "access_denied", None)

    @pytest.mark.parametrize("operation", ("create", "get", "replace", "delete"))
    def test_unexpected_provider_response_uses_shared_http_error(
        self, failing_http_client: FailingHttpClientFactory, operation: str
    ) -> None:
        response = _call_operation(
            failing_http_client(ProviderFailure.UNEXPECTED_RESPONSE), operation
        )
        _error_body(response, 502, "provider_error", None)

    @pytest.mark.parametrize("operation", ("create", "get", "replace", "delete"))
    def test_unavailable_provider_uses_shared_http_error(
        self, failing_http_client: FailingHttpClientFactory, operation: str
    ) -> None:
        response = _call_operation(
            failing_http_client(ProviderFailure.UNAVAILABLE), operation
        )
        _error_body(response, 503, "provider_unavailable", None)

    @pytest.mark.parametrize("operation", ("create", "replace"))
    def test_uncertain_write_is_non_retryable_provider_error(
        self, failing_http_client: FailingHttpClientFactory, operation: str
    ) -> None:
        response = _call_operation(
            failing_http_client(ProviderFailure.UNCERTAIN_WRITE), operation
        )
        _error_body(response, 502, "provider_error", False)

    def test_common_consumer_workflow(
        self, http_client: HttpClient, created_ids: list[str]
    ) -> None:
        """Exercise create, get, replace, and delete as one portable workflow."""
        created_response = http_client.request("POST", "/events", json=CREATE_BODY)
        assert created_response.status_code == 201
        created = _event_body(created_response, CREATE_BODY)
        event_id = str(created["id"])
        created_ids.append(event_id)
        path = f"/events/{event_id}"

        assert (
            _event_body(http_client.request("GET", path), CREATE_BODY)["id"] == event_id
        )
        assert (
            _event_body(
                http_client.request("PUT", path, json=REPLACE_BODY), REPLACE_BODY
            )["id"]
            == event_id
        )
        deleted = http_client.request("DELETE", path)
        assert deleted.status_code == 204
        assert deleted.content == b""
        _error_body(http_client.request("GET", path), 404, "not_found", False)
