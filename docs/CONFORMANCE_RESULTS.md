# Calendar Conformance Results

This file records cross-team runs of the reusable shared conformance suite.
Failures are implementation findings; they do not change or weaken the shared
contract.

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
