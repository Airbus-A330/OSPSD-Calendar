"""Runs the reusable HTTP suite against an in-memory reference implementation."""

import json as json_module
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from calendar_contract.conformance import ProviderFailure
from calendar_contract.event import Event
from calendar_contract.http_conformance import (
    CREATE_BODY,
    CalendarHttpConformance,
    FailingHttpClientFactory,
    HttpClient,
    HttpResponse,
)
from calendar_contract.requests import CreateEvent, ReplaceEvent


@dataclass
class ReferenceResponse:
    """Small response object implementing the shared test protocol."""

    status_code: int
    payload: object | None = None

    @property
    def content(self) -> bytes:
        """Return an empty 204 body or the serialized payload."""
        if self.payload is None:
            return b""
        return json_module.dumps(self.payload).encode()

    def json(self) -> object:
        """Return the response payload."""
        return self.payload


def _error(status: int, code: str, message: str) -> ReferenceResponse:
    """Build a non-retryable shared error response."""
    return ReferenceResponse(
        status,
        {"error": {"code": code, "message": message, "retryable": False}},
    )


class ReferenceHttpClient:
    """In-memory HTTP-shaped implementation used to exercise the shared suite."""

    def __init__(self) -> None:
        self.events: dict[str, Event] = {}

    def request(
        self,
        method: str,
        path: str,
        *,
        json: object | None = None,
        content: bytes | str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> HttpResponse:
        del headers
        if method in ("POST", "PUT"):
            if content is not None:
                try:
                    json = json_module.loads(content)
                except (json_module.JSONDecodeError, UnicodeDecodeError):
                    return _error(400, "invalid_input", "Malformed JSON.")
            if not isinstance(json, dict):
                return _error(422, "invalid_input", "Invalid request body.")

        if method == "POST" and path == "/events":
            return self._create(json)

        prefix = "/events/"
        if not path.startswith(prefix):
            return _error(404, "not_found", "Route not found.")
        event_id = path.removeprefix(prefix)
        if method == "GET":
            return self._get(event_id)
        if method == "PUT":
            return self._replace(event_id, json)
        if method == "DELETE":
            return self._delete(event_id)
        return _error(404, "not_found", "Route not found.")

    def _create(self, body: object) -> ReferenceResponse:
        try:
            request = CreateEvent.model_validate(body)
        except ValidationError:
            return _error(422, "invalid_input", "Invalid event.")
        event = Event(id=secrets.token_hex(8), **request.model_dump())
        self.events[event.id] = event
        return ReferenceResponse(201, self._event_payload(event))

    def _get(self, event_id: str) -> ReferenceResponse:
        event = self.events.get(event_id)
        if event is None:
            return _error(404, "not_found", "Event not found.")
        return ReferenceResponse(200, self._event_payload(event))

    def _replace(self, event_id: str, body: object) -> ReferenceResponse:
        if event_id not in self.events:
            return _error(404, "not_found", "Event not found.")
        try:
            request = ReplaceEvent.model_validate(body)
        except ValidationError:
            return _error(422, "invalid_input", "Invalid event.")
        event = Event(id=event_id, **request.model_dump())
        self.events[event_id] = event
        return ReferenceResponse(200, self._event_payload(event))

    def _delete(self, event_id: str) -> ReferenceResponse:
        if event_id not in self.events:
            return _error(404, "not_found", "Event not found.")
        del self.events[event_id]
        return ReferenceResponse(204)

    @staticmethod
    def _event_payload(event: Event) -> dict[str, object]:
        """Return allowed extensions and an equivalent normalized UTC offset."""
        payload: dict[str, object] = event.model_dump()
        for field in ("start", "end"):
            timestamp = datetime.fromisoformat(str(payload[field])).astimezone(UTC)
            payload[field] = timestamp.isoformat().replace("+00:00", "Z")
        payload["implementation"] = "reference"
        return payload


class FailingReferenceHttpClient:
    """HTTP-shaped client returning one controlled provider failure."""

    def __init__(self, failure: ProviderFailure) -> None:
        self.failure = failure

    def request(
        self,
        method: str,
        path: str,
        *,
        json: object | None = None,
        content: bytes | str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> HttpResponse:
        del method, path, json, content, headers
        if self.failure == ProviderFailure.ACCESS_DENIED:
            return _error(403, "access_denied", "Access denied.")
        if self.failure == ProviderFailure.UNAVAILABLE:
            response = _error(503, "provider_unavailable", "Provider unavailable.")
            assert isinstance(response.payload, dict)
            error = response.payload["error"]
            assert isinstance(error, dict)
            error["retryable"] = True
            return response
        return _error(502, "provider_error", "Provider failure.")


class TestReferenceHttpCalendar(CalendarHttpConformance):
    @pytest.fixture
    def http_client(self) -> HttpClient:
        return ReferenceHttpClient()

    @pytest.fixture
    def failing_http_client(self) -> FailingHttpClientFactory:
        return FailingReferenceHttpClient


class WrongCreateStatusClient(ReferenceHttpClient):
    """Reference implementation with an intentionally wrong create status."""

    def _create(self, body: object) -> ReferenceResponse:
        response = super()._create(body)
        if response.status_code == 201:
            response.status_code = 200
        return response


class MissingRetryableClient(ReferenceHttpClient):
    """Reference implementation that omits a required error member."""

    def _get(self, event_id: str) -> ReferenceResponse:
        response = super()._get(event_id)
        if response.status_code == 404:
            assert isinstance(response.payload, dict)
            error = response.payload["error"]
            assert isinstance(error, dict)
            del error["retryable"]
        return response


def test_suite_catches_wrong_create_status() -> None:
    suite = CalendarHttpConformance()
    with pytest.raises(AssertionError):
        suite.test_create_returns_201_and_shared_event(WrongCreateStatusClient(), [])


def test_suite_catches_missing_retryable_error_member() -> None:
    client = MissingRetryableClient()
    suite = CalendarHttpConformance()
    with pytest.raises(AssertionError):
        suite.test_missing_event_returns_not_found(client, "missing-id", "GET")


def test_suite_accepts_equivalent_offsets_and_response_extensions() -> None:
    client = ReferenceHttpClient()
    response = client.request("POST", "/events", json=CREATE_BODY)
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body, dict)
    assert body["implementation"] == "reference"
