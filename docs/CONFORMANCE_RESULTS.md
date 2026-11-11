# Calendar Conformance Results

This file records cross-team runs of the reusable shared conformance suite.
Failures are implementation findings; they do not change or weaken the shared
contract.

## Status before the stable release

The stable tag waits until every team has a recorded passing run of both suites at the
release candidate commit ([`RELEASING.md`](RELEASING.md)). Update this table with each run.

| Team | Latest recorded run | Python suite | HTTP suite | Passing? |
| --- | --- | --- | --- | --- |
| Team 2 | Nov 9, suite `be8ae2b` | not recorded | 9 passed, 46 failed | No: fixes pending, rerun needed |
| Team 5 | none | not recorded | not recorded | Not yet recorded |
| Team 7 | Nov 11, suite `fd4a056` | 37 passed | 55 passed | Yes, with three BASK'D PRs still open (see below) |

## Team 2

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

## Team 7

Tested on November 11, 2026, by Karthik Ganeshan:

- shared suite revision: `fd4a056` (`ms3-submission`);
- service repository: [samthropic/BASKD](https://github.com/samthropic/BASKD) `main` at
  `f24c312`, merged locally with three open pull requests that make the remaining contract
  changes: #38 (`a55ae5a`, adopts this package and runs the Python suite), #54 (`31da6db`,
  `400` for a body that is not JSON) and #56 (`94a7604`, `403 access_denied`);
- execution boundary: BASK'D's FastAPI application through `TestClient`. The success and
  validation checks use its in-memory provider. The failure checks use its real Google
  Calendar adapter over a fake Google SDK, so they go through BASK'D's own error
  translation;
- credentials and network access: not used. Separately, the integration job in BASK'D #38
  runs the Python suite's create, get, replace and delete checks against the real Google
  Calendar;
- result: Python suite 37 passed; HTTP suite 55 passed.

Before those three PRs, the HTTP suite found two gaps on BASK'D's `main`: malformed JSON
returned `422` instead of `400`, and an access denial returned `502` instead of
`403 access_denied`. Both are fixed by the PRs above. No shared assertions were relaxed. An
earlier run also found that the suite used `location` as its unknown field, which the
contract allows as an extension; #24 now uses `not_a_contract_field`.

