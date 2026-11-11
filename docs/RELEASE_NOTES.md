# Release notes

## v0.1.0

**Status:** Final stable release. All three teams passed both shared
conformance suites, as recorded in
[`CONFORMANCE_RESULTS.md`](CONFORMANCE_RESULTS.md). The immutable `v0.1.0` tag
identifies the reviewed, green release commit on `ms3-submission`.

**Why `v0.1.0`.** It is the stable release of `v0.1.0-rc.1`. The package metadata already
says `0.1.0`, and nothing since `rc.1` changes contract semantics: no rule, model, error code
or `CalendarService` signature changed. Under `RELEASING.md`, no minor version bump is
required.

**Changes since `v0.1.0-rc.1`:**

- **New:** `calendar_contract.http_conformance.CalendarHttpConformance`, the shared HTTP
  conformance suite: the four operations, statuses, error bodies, validation, provider
  failures, uncertain writes and the common consumer workflow (#24). Its unknown-field check
  uses a field no team extends.
- **Public API:** the package root exports exactly `CalendarError`, `CalendarService`,
  `CreateEvent`, `ErrorCode`, `Event` and `ReplaceEvent`, plus `__version__`. The
  accidental `calendar_contract.version` re-export is gone, and module imports stay
  supported (#25).
- **Docs:** how to run both suites (README), which check covers which HTTP rule
  (`HTTP_CONTRACT.md`), and each team's recorded runs (`CONFORMANCE_RESULTS.md`).

**Unchanged:** the HTTP contract, the shared models and errors, and `CalendarService`.

**Known limitation (unchanged):** a create that times out returns no `id`, and listing is
not shared, so the shared core gives a client no way to check whether the event was created
before sending the request again (`HTTP_CONTRACT.md`, "Known limitation").
