# Phase 2 verification record

Date: 2026-10-26 UTC.

**Historical initial verification.** The local readiness issue below was subsequently resolved. See [the live results](phase-2-live-results.md) for the completed local execution and deployed read-only checks.

## Delivered

- 51 source-backed Postman scenario definitions with JavaScript assertions.
- 79 disabled manual endpoint templates, extracted from the actual Java controllers.
- Secret-free local environment and synthetic authentication examples.
- Scenario prerequisites, fixture matrix, cleanup instructions and API contracts.
- Newman 6.2.1 installed; package lockfile generated.
- Reproducible generator, static validator and sanitized Newman runner.

No backend or frontend application file was modified. No application was started, no database was provisioned or changed, and no production or Stripe API request was sent by this phase.

## Executed checks

| Check | Actual result |
| --- | --- |
| Collection generation | PASS: 51 scenarios and 79 reference templates |
| Postman SDK parsing and structural checks | PASS |
| JavaScript syntax compilation | PASS: 181 scripts |
| Scenario/controller method and path matching | PASS: 51 scenarios |
| Local-origin acceptance / remote-origin rejection checks | PASS: 51 scenario guards |
| Template secret checks and unique scenario IDs | PASS |
| Local readiness preflight for default public smoke selection | BLOCKED: `/api/health` at localhost:8080 did not satisfy the readiness check within 5 seconds |
| Application assertions through Newman | NOT EXECUTED: readiness gate stopped the run |

Static validation timestamp: `2026-10-26T02:59:28.694Z`. Smoke preflight timestamp: `2026-10-26T02:58:06.868Z`. The last generator change added an opt-in Checkout scenario; it did not change the five smoke cases selected in the recorded preflight.

The recorded smoke selection has **PASS 0 / FAIL 0 / SKIPPED 0 / BLOCKED 5**. The other **46 scenario definitions were not selected or executed**. The 79 manual templates are excluded from test-result counts. A static PASS does not mean application behavior passed.

Machine-readable evidence is generated locally at `reports/postman/validation.json` and `reports/postman/execution.json`; these paths are ignored by Git. The smoke process reported blockage. The runner sets exit code 2 for that condition; the Windows execution host surfaced exit code 1 during this session, so the JSON status is the recorded evidence.

## Known limits and next execution

The static validator uses the Postman Collection SDK and targeted checks, not exhaustive validation against the remote JSON Schema. No application defect is marked runtime-confirmed here.

To obtain live results, first start an isolated backend with disposable PostgreSQL and test-only services, then rerun `npm.cmd run postman:run`. Supply dedicated accounts and fixture IDs for authenticated folders. Database and Stripe TEST setup are not inferred from the existing machine environment.

The manual object lifecycle must be run through Postman and cleaned up even if intermediate assertions fail. The Newman runner deliberately refuses that ordered manual folder to prevent a create-only execution when cleanup prerequisites are unavailable.

There is no measured coverage percentage, load result, successful payment or E2E claim. Phase 3 has not been started.
