# Shared Calendar HTTP MS2 Contract

## Status

This document states the HTTP behavior that Teams 2, 5, and 7 agreed to on
October 28, 2026, in version 4 of the shared Calendar decision memo. The memo
keeps the reasoning, the history and the open questions; this document keeps
only the resulting rules. Rule numbers in brackets refer to the memo.

Every conforming server implements everything below except the items under
[Allowed differences](#allowed-differences) and
[Optional extensions](#optional-extensions). Changing any rule here requires
review by all three teams (see `AGENTS.md`).

## Operations

| Operation | Request | Success | Response body |
| --- | --- | --- | --- |
| Create | `POST /events` | `201 Created` | the created event |
| Get by id | `GET /events/{event_id}` | `200 OK` | the event |
| Replace | `PUT /events/{event_id}` | `200 OK` | the replaced event |
| Delete | `DELETE /events/{event_id}` | `204 No Content` | none |

[Rules 8, 15]

The contract does not make create idempotent: repeating a successful `POST`
can create a second event.

## Event

Create, get and replace return the event as a JSON object:

```json
{
  "id": "4k9v2m1q8s7d6f5g3h2j1l0p9o",
  "title": "Team sync",
  "start": "2026-11-04T15:00:00Z",
  "end": "2026-11-04T15:30:00Z"
}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Assigned by the provider. Treat it as an opaque string. |
| `title` | string | See [Titles](#titles). |
| `start` | string | RFC 3339 timestamp. See [Timestamps](#timestamps). |
| `end` | string | RFC 3339 timestamp, an instant strictly after `start`. |

A response contains at least these four fields. A server may add others, and
clients ignore fields they do not recognize. [Rule 15]

## Request bodies

`POST /events` and `PUT /events/{event_id}` take the same JSON object:

```json
{
  "title": "Team sync",
  "start": "2026-11-04T10:00:00-05:00",
  "end": "2026-11-04T10:30:00-05:00"
}
```

- `title`, `start` and `end` are all required. A missing field, or one sent as
  `null`, is rejected with `422 invalid_input`. [Rules 1, 3]
- A field the server does not know is rejected with `422 invalid_input`
  before the provider is called. [Rule 7]
- `PUT` replaces `title`, `start` and `end`, and never changes `id`. What
  `PUT` does to fields outside the shared four is up to each server. [Rule 1]

### Titles

[Rule 13]

- On `POST` and `PUT`, `title` must be a string that is not empty after
  trimming leading and trailing whitespace. A missing, `null`, non-string or
  blank title is rejected with `422 invalid_input`.
- Trimming only decides whether a title is blank. A server may store the
  title trimmed or as sent.
- Each server documents its maximum title length.
- When `GET` finds a provider event with a missing or empty title, it returns
  `200` with `"title": ""`. A server never invents a title.

### Timestamps

[Rules 2, 14]

- Requests send RFC 3339 timestamp strings with an explicit UTC offset: `Z`
  or `±hh:mm`.
- A numeric timestamp, or one without an offset, is rejected with
  `422 invalid_input`.
- `end` must be an instant strictly after `start`. Otherwise the request is
  rejected with `422 invalid_input`.
- Responses carry the instants the provider stored, written with any
  equivalent UTC offset. A server does not have to keep the offset the
  request used, so clients compare instants, not timestamp strings.
- Timestamps may have fractional seconds, and a server may drop them from
  the times it receives. A server that drops them checks that `end` is after
  `start` after dropping them, so `10:00:00.1` to `10:00:00.9` is rejected
  there with `422 invalid_input`. Clients that need the same result from every
  server send whole seconds.

## Errors

### Error body

[Rule 4]

Every error response has this body:

```json
{
  "error": {
    "code": "not_found",
    "message": "Event not found.",
    "retryable": false
  }
}
```

- `code`, `message` and `retryable` are required.
- `details` is optional. When present, it is sanitized.
- Clients ignore keys they do not recognize.
- `retryable`, not the status code, tells the client whether to retry.

### Statuses and codes

[Rules 3, 5, 6, 9, 11]

| Situation | Status | `code` |
| --- | --- | --- |
| The body is not valid JSON | `400` | `invalid_input` |
| Valid JSON that breaks a rule: a missing, unknown or wrongly typed field, or a bad value such as a timestamp without an offset or an `end` not after `start` | `422` | `invalid_input` |
| A bad path or query parameter | `422` | `invalid_input` |
| `GET`, `PUT` or `DELETE` on an id the calendar does not have | `404` | `not_found` |
| A `DELETE` repeated after it succeeded | `404` | `not_found` |
| The configured provider identity lacks permission for the operation | `403` | `access_denied` |
| The provider returned an invalid or unexpected response | `502` | `provider_error` |
| A create or replace whose outcome is unknown, such as one that timed out | `502` | `provider_error` |
| The provider is temporarily unavailable | `503` | `provider_unavailable` |

- These five codes are shared. A server uses another code only for a case
  this contract does not cover, such as `internal_error` for a `500`.
  [Rule 12]
- A `503` may include a `Retry-After` header when there is a meaningful
  retry delay. [Rule 9]
- A create or replace whose outcome is unknown always has
  `"retryable": false`, even when the response also has `Retry-After`. The
  server never retries the write on its own, because sending it again may
  create a duplicate. [Rules 4, 6]
- A server cannot tell an event deleted earlier from one that never existed,
  so a client that repeats a `DELETE` can treat `404` as "already gone".
  [Rule 5]

## Allowed differences

Each server makes and documents its own choice for each of these. They are
not shared behavior, and a client that must work with every server does not
rely on any of them:

- what `PUT` does to fields outside the shared four [Rule 1];
- which UTC offset responses use [Rule 2];
- whether sub-seconds are dropped [Rule 14];
- the maximum title length [Rule 13];
- whether the stored title is trimmed [Rule 13];
- whether create returns a `Location` header [Rule 8];
- which optional extensions it offers.

The decision memo lists each team's current choices.

## Optional extensions

These are outside the shared core. A server may offer them and documents how
they work:

- listing (`GET /events`);
- partial update (`PATCH /events/{event_id}`);
- all-day events;
- fields beyond the shared four, such as description and location;
- calendar metadata;
- a `Location` header on create.

## Known limitation

A create that times out returns no `id`, and listing is not shared, so the
shared core alone gives a client no way to check whether the event was
created before it sends the request again. The memo keeps this as an open
question; a shared listing or an idempotency key on create would close it.
