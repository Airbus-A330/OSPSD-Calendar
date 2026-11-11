# Calendar Conformance Results

This file records cross-team runs of the reusable shared conformance suite.
Failures are implementation findings; they do not change or weaken the shared
contract.

## Status before the stable release

The stable tag waits until every team has a recorded passing run of both suites at the
release candidate commit ([`RELEASING.md`](RELEASING.md)). Update this table with each run.

| Team | Latest recorded run | Python suite | HTTP suite | Passing? |
| --- | --- | --- | --- | --- |
| Team 2 | Nov 11, service `5f25ac8`, suite `fd4a056` | 46 passed | 55 passed | Yes ([final rerun](#team-2-final-rerun)) |
| Team 5 | Nov 11, service `7859542`, suite `afd62a6` | 24 passed | 55 passed | Yes ([Team 5 verification](#team-5-verification)) |
| Team 7 | Nov 11, service `9c068e7`, suite `a00fe8a` | 37 passed | 55 passed | Yes ([final rerun](#team-7-final-rerun)) |

## Team 2 final rerun

Tested on November 11, 2026:

- service repository: `Airbus-A330/OSPSD-Team-2`;
- service revision:
  `5f25ac82825b99af661b834615c84f1f174ef4fb`;
- shared suite revision:
  `fd4a056`;
- Python execution boundary: Team 2's `CalendarServiceAdapter` was tested
  directly and through its HTTP-backed adapter, using the shared
  `CalendarServiceConformance` suite;
- HTTP execution boundary: Team 2's FastAPI application was exercised through
  `TestClient` using the shared `CalendarHttpConformance` suite;
- provider boundary: Team 2's real `GoogleCalendarProvider`, application
  adapter, cache and HTTP dependency path were used over a controlled fake
  Google SDK;
- credentials and network access: not used;
- result: Python suite 46 passed; HTTP suite 55 passed.

The Python count includes the inherited suite at both Team 2 application
boundaries. The HTTP count is the complete shared HTTP suite. The run covered
the four shared operations, validation, missing events, repeated deletion,
shared error responses, provider failures, uncertain writes and the common
consumer workflow.

The three failure groups recorded in Team 2's November 9 run are resolved:
valid contract violations now return `422 invalid_input`, error responses
include `retryable`, and provider permission failures use
`403 access_denied`. No shared assertions were weakened.

The suite source was loaded from the final shared revision for this
verification because Team 2 remains pinned to `v0.1.0-rc.1` until the stable
shared tag is published. Team 2 will update its dependency pin and lockfile
after that tag is available.

## Team 2 earlier integration run

Tested on November 9, 2026:

- service repository revision:
  `863cd3692d248c9cdb488aff1ac1d1ec2720b108`;
- shared suite revision: `be8ae2b`;
- execution boundary: Team 2's FastAPI application with a controlled in-memory
  `EventProvider` supplied through its normal dependency override;
- credentials and network access: not used;
- result: 9 passed, 46 failed.

The successful cases established the four-operation happy path, response Event
shape, delete behavior, the shared GET error path, and the complete consumer
workflow. The failures fell into these contract-level groups:

1. Valid JSON that violates a create or replace rule returned `400`; the shared
   contract requires `422 invalid_input`.
2. Several non-GET error responses omitted the required `retryable` member.
   This affected invalid input, missing replace/delete, provider failures, and
   uncertain writes.
3. Create, replace, and delete permission failures used
   `permission_denied`; the shared code is `access_denied`.

The repeated parameterized failures are multiple examples of these same
behaviors, including required and null fields, title rules, timestamp syntax,
time ordering, unknown fields, malformed JSON, and controlled provider
outcomes. Team 2 should correct its HTTP error translation and then run the
same suite in its service repository. No shared assertions were relaxed in
response to these findings.

## Team 5 verification

Tested on November 11, 2026, with Python 3.14.8.

- Service: `juno-junhyuk-lee/OSPSD-Team-5`, tag `v0.1.0-beta.6`, commit `7859542c83f8a051d4d287f811a7f27bd1150e9e`.
- Shared package and suites: `Airbus-A330/OSPSD-Calendar`, commit `afd62a60889f4d668945e40c105307277961cd21` on `ms3-submission`. Both suite files were unchanged from `fd4a056`.
- Python suite: `CalendarServiceConformance` exercised Team 5's `GoogleCalendarService` directly. Normal cases used Team 5's Google adapters with a fake Google SDK. Failure cases used Team 5's controlled failing adapters. Result: 24 passed, 0 failed, 0 skipped.
- HTTP suite: `CalendarHttpConformance` exercised Team 5's FastAPI routes through `TestClient`, including request validation, CRUD, the consumer workflow, and HTTP error translation. Failure cases supplied a `GoogleCalendarService` backed by controlled failing adapters. Result: 55 passed, 0 failed, 0 skipped.
- The run used temporary pytest fixture wiring with the shared assertions unchanged. Neither suite required Google credentials or made live Calendar calls. The separate [deployed workflow and cleanup verification](https://github.com/juno-junhyuk-lee/OSPSD-Team-5/pull/51#issuecomment-6807853904) covers the real Google Calendar path.

## Team 7 final rerun

Tested on November 11, 2026, by Karthik Ganeshan, after every BASK'D pull request the earlier
run depended on had merged:

- service repository: [samthropic/BASKD](https://github.com/samthropic/BASKD);
- service revision: `main` at `9c068e7068e3708485b9068fda9956e47a48bcfd`, which contains
  samthropic/BASKD#38, samthropic/BASKD#54 and samthropic/BASKD#56 as merged commits;
- shared suite revision: `a00fe8a` (`ms3-submission`). The two suite files are unchanged from
  `fd4a056`;
- execution boundary: the same as the earlier run below. Success and validation checks use
  BASK'D's in-memory provider through `TestClient`; failure checks use its real Google
  Calendar adapter over a fake Google SDK;
- credentials and network access: not used for these two suites;
- result: Python suite 37 passed; HTTP suite 55 passed.

Against the real Google Calendar, on the same revision: BASK'D's CI integration job ran the
Python suite's create, get, replace and delete checks through its Google provider
([run 43108298662](https://github.com/samthropic/BASKD/actions/runs/43108298662/job/130817519994)):
10 passed, 14 skipped (the failure checks, which a real calendar cannot produce on demand).
Until the stable tag exists that job uses BASK'D's pinned suite, `v0.1.0-rc.1`.

## Team 7 earlier local run

Tested on November 11, 2026, by Karthik Ganeshan:

- shared suite revision: `fd4a056` (`ms3-submission`);
- service repository: [samthropic/BASKD](https://github.com/samthropic/BASKD) `main` at
  `f24c312`, merged locally with three open pull requests that make the remaining contract
  changes: samthropic/BASKD#38 (`a55ae5a`, adopts this package and runs the Python suite),
  samthropic/BASKD#54 (`31da6db`, `400` for a body that is not JSON) and samthropic/BASKD#56
  (`94a7604`, `403 access_denied`);
- execution boundary: BASK'D's FastAPI application through `TestClient`. The success and
  validation checks use its in-memory provider. The failure checks use its real Google
  Calendar adapter over a fake Google SDK, so they go through BASK'D's own error
  translation;
- credentials and network access: not used in this run;
- result: Python suite 37 passed; HTTP suite 55 passed.

Separately, against the real Google Calendar: samthropic/BASKD#38 adds a credential-gated
integration test that runs the Python suite's create, get, replace and delete checks
through BASK'D's Google provider. It ran in BASK'D's CI at `aadd50c` (that PR's head on
Nov 4, with suite `v0.1.0-rc.1`), in the integration job of
[run 41888897047](https://github.com/samthropic/BASKD/actions/runs/41888897047/job/126780897225):
16 passed and 14 skipped (the failure checks, which a real calendar cannot produce on
demand). It has not been rerun against suite `fd4a056`.

Before those three PRs, the HTTP suite found two gaps on BASK'D's `main`: malformed JSON
returned `422` instead of `400`, and an access denial returned `502` instead of
`403 access_denied`. Both are fixed by the BASK'D PRs above. No shared assertions were relaxed. An
earlier run also found that the suite used `location` as its unknown field, which the
contract allows as an extension; #24 now uses `not_a_contract_field`.
