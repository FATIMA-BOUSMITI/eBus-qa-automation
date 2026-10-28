# API cases and traceability

The authoritative per-case list is `postman/fixtures/scenarios.json`. Each entry includes its ID, HTTP method/path, fixture prerequisites, expected status, mutation flag and cleanup. Request descriptions duplicate the essentials for Postman users.

| Requirement | Cases | Expected result |
| --- | --- | --- |
| Public availability | SMK-001–005 | UP health and JSON catalogues |
| Login and token validation | AUTH-001–007 | Valid login returns JWT; invalid credentials/tokens rejected |
| Authorization and account isolation | AUTH-008–010, ABO-004–005, CARD-002 | User cannot read administrator or other-account resources |
| Authenticated profile/dossier | USR-001, DOS-001 | Current account profile and recognized dossier status |
| Subscription reads and expiry | ABO-001–003 | Current/history owner matches; old ACTIF subscription reads EXPIRE |
| Cards, activity and admin reads | CARD-001, ACT-001, ADM-001–003 | Expected JSON collections |
| Eligibility and activation protection | PAY-001–005 | Pending/rejected/inactive cases refused; ACTIF cannot be manually assigned |
| Stripe test outcomes | STR-001–005 | Eligible account creates Checkout; unpaid/expired sessions remain pending; paid session activates; forged webhook rejected |
| Object validation and role restrictions | OBJ-001–005 | Public list, anonymous/USER restrictions, invalid data rejected |
| Object happy path and lifecycle | OBJ-006–011 | Create, read, reject invalid status, make available, signal collection, delete |
| Dossier transitions | DOS-002–003 | Validate or reject with reason on separate disposable dossiers |

## Manual object lifecycle

Preconditions: isolated DB, USER/ADMIN credentials, existing `ligneId`, `allowMutations=true`.

1. OBJ-006 creates a uniquely named synthetic object and stores `createdObjectId` locally.
2. OBJ-007 reads it and checks its ID.
3. OBJ-008 checks rejection of an unknown status. HTTP 500 is a failure.
4. OBJ-009 marks it DISPONIBLE.
5. OBJ-010 checks the legal transition to EN_ATTENTE_RECUPERATION.
6. OBJ-011 deletes it and clears `createdObjectId` after HTTP 204.

Always run cleanup even if steps 2–5 fail. If creation succeeded but a malformed response prevented ID capture, locate the unique QA name in the disposable DB and remove it there. Do not delete pre-existing user objects.

For independent repeatability, rerun the entire lifecycle with a fresh object. The manual lifecycle is the only intentionally ordered object chain; it is not advertised as an order-independent API suite.

## Payment and dossier cleanup

Use one prepared snapshot per scenario. Confirmation can create an abonnement and Payment; dossier validation can activate an existing abonnement. Restore the entire isolated snapshot, rather than attempting partial deletion through public endpoints. These operations are disabled by default. Open Stripe TEST sessions require separate expiration in the test dashboard; restoring PostgreSQL does not reset Stripe.

## Interpretation

HTTP checks enforce intended outcomes and are accompanied by content/ownership/state assertions where relevant. PASS of a refusal case alone does not prove the database was unchanged; verify that in the later integration tests. A POST returning an error can still have side effects, hence snapshot cleanup.

The 79 `REF-*` entries have no automated outcome assertions and are not counted among the 51 scenarios. Complete their inputs and expected outcomes before treating an individual manual execution as a test result.
