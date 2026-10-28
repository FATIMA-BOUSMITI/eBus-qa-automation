# Phase 2 — live execution results

Date: 2026-10-26 UTC. This report supersedes the initial local-readiness blockage recorded in `phase-2-execution.md`.

## Actual results

| Target | PASS | FAIL | SKIPPED | BLOCKED |
| --- | ---: | ---: | ---: | ---: |
| Local Docker backend + dedicated PostgreSQL, 51 definitions | 25 | 16 | 10 | 0 |
| Deployed Render read-only checks, separate 12-case selection | 11 | 1 | 0 | 0 |

Local report timestamp: `2026-10-26T03:19:26.891Z`. Deployed report timestamp: `2026-10-26T03:17:22.4044006Z`. These selections differ; their totals must not be presented as unique coverage of the same suite.

Evidence is saved in ignored `reports/postman/qa-summary.json`, `qa-<case-ID>.json`, and `deployed-readonly.json`. Reports contain only test identifiers, HTTP status, result and assertion counts. No password, JWT value or raw personal-data response is saved.

## Deployed application

The user requested use of the deployed version. `qa/read-deployed.ps1` authenticated the provided USER account, then executed twelve GET checks against the known Render backend. The following passed: health, buses, lines, tickets, own profile, own dossier, current subscription (HTTP 204), subscription history, cards, activities, and authenticated subscription-type catalogue.

The anonymous subscription-type catalogue returned HTTP **500**, whereas the authenticated request returned **200**. No business-data mutations, negative login attempts, cross-account probes, payments or load tests were executed on Render. Authentication itself was the sole POST operation in this read-only selection.

The deployed build revision was not verified to match the local checkout. Only the explicitly recorded deployed results establish behavior on Render.

## Local isolated execution

The existing Java application compiled successfully with `mvn -B -DskipTests package`. Java tests were **not executed** by that command. Docker ran the JAR unchanged with an external QA profile, a dedicated `ebus_qa` database and synthetic identities. No provided Render password was used in local fixtures.

All 41 selected cases reached the running local backend. Four scenarios requiring real Stripe TEST resources and six ordered manual object-lifecycle scenarios were skipped. The invalid-signature webhook case ran locally with a forged test payload and passed. The other skips were not dependency failures.

Examples of passing behavior include valid login, expired/malformed/missing JWT rejection, own profile and dossier, current/history subscriptions, effective expiration, pending/rejected/inactive subscription eligibility refusal, administrative reads and dossier validation/rejection.

## Failed local cases

| Cases | Actual HTTP | Expected |
| --- | ---: | --- |
| SMK-005 | 500 | Anonymous catalogue returns 200 and an array |
| AUTH-002, AUTH-003 | 500 | Unknown email / wrong password rejected with 401 |
| AUTH-004 | 500 | Empty credentials rejected with 400 or 401 |
| AUTH-008, AUTH-009 | 500 | Authenticated USER denied access with 403 |
| AUTH-010 | 200 | Other user's profile through `/test/user/{id}` denied with 403 |
| ABO-004, ABO-005 | 200 | Other user's subscription and history denied with 403 |
| CARD-002 | 200 | Other user's card route denied with 403 |
| PAY-004 | 500 | Missing subscription parameters rejected with 400 |
| PAY-005 | 500 | Manual ACTIF assignment rejected with 400 or 409 |
| OBJ-002, OBJ-003 | 500 | Anonymous declaration / USER status update denied with 401/403 or 403 |
| OBJ-004 | 500 | Empty declaration rejected with 400 or 422 |
| OBJ-005 | 500 | Unknown line rejected with 400, 404 or 422 |

The sixteen failures group into the defects below; they are not sixteen unrelated bugs. Assertions were not relaxed to make failures pass.

## Defects and triage

### API-BUG-001 — Anonymous subscription catalogue fails

- Confirmed on local and deployed targets.
- Reproduce: GET `/types-abonnement` without Authorization.
- Actual: 500. Authenticated deployed request: 200.
- Expected: the route is explicitly public in SecurityConfig and should handle an anonymous caller.
- Source hypothesis: the service casts the anonymous principal to `User`. This explanation is based on code inspection; the deployed stack trace was not collected.
- Priority: high, because registration/catalogue browsing may depend on it.

### API-BUG-002 — Expected validation/authentication/authorization errors become 500

- Confirmed locally by the twelve failed cases returning 500 above.
- Reproduce using the synthetic local fixture environment and the listed case IDs.
- Expected: appropriate client-error or permission-denied status, rather than a server failure.
- Source hypothesis: the broad global RuntimeException handler covers multiple business and security exception types; missing-parameter conversion also needs review.
- Priority: high. An HTTP 500 for denied access does not itself prove the operation was authorized or that data was exposed.

### API-BUG-003 — Account-isolation rejection absent on four read routes

- Confirmed locally: synthetic USER 2 requested USER 3 resources.
- Actual: 200 for `/test/user/3`, `/abonnements/user/3`, `/abonnements/user/3/historique`, `/cards/user/3`.
- Expected security requirement: 403 when accessing another account's private resources.
- The fixture contains a subscription for USER 3. The card fixture is empty: CARD-002 proves absence of the expected HTTP rejection, not disclosure of an existing card record.
- Source evidence: missing ownership check in the test/card controllers and overly permissive role conditions for subscriptions.
- Priority: critical for ownership enforcement; confirm the product access policy before accepting a fix.
- Not probed on Render.

## Cleanup and remaining work

The two modified synthetic dossiers were restored successfully in one transaction. Both QA containers were stopped, retaining the disposable database for inspection. No production business data was changed. Restart instructions are in `qa/README.md`.

The application business logic remains unchanged. The next phase must retain these failing cases as regression evidence. Remaining manual object scenarios and real Stripe TEST outcomes are not claimed as executed. No Robot Framework, JUnit coverage, integration-test coverage, UI E2E or performance result is established by this phase.
