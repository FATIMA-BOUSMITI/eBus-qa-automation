# Test Strategy

## Objectives and scope

Verify the actual eBus application with independent evidence at service, persistence/API and browser layers. Protect existing users and lines. Detect failures rather than changing assertions to match a defect. No destructive test or load is sent to Render.

Risk priorities: account ownership/authorization, JWT handling, dossier eligibility, payment confirmation, subscription expiration, private documents, input validation and frontend/backend contract gaps. The source inventory has 79 controller method/path mappings; schedules and bus-position endpoints called by Flutter are missing from this backend and are not invented as coverage.

## Layers

| Layer | Tools | Isolation and assertions |
| --- | --- | --- |
| Unit | JUnit 5, Mockito, AssertJ, JaCoCo | Repositories/Stripe mocked; eligibility, expiry, status/payment synchronization, object recovery/deletion rules |
| Integration | Spring Boot Test, MockMvc, PostgreSQL | Separate local DB; real JWT, controller/service/repository, own profile/dossier and object lifecycle |
| API | Postman/Newman, Robot/RequestsLibrary/JSONLibrary | Synthetic QA identities; status, shape, state and ownership expectations |
| Browser | Python, pytest, Playwright, Allure adapter | Real Flutter build and API; independent contexts; source/DOM verified semantics; reads and synthetic login |
| Performance | JMeter | One-user local smoke measured; separate unexecuted progressive/endurance profiles |

Positive and negative tests are intentionally complementary. An HTTP 500 is not accepted as a permission/validation result. Missing runtime prerequisites are BLOCKED; deliberately unselected manual/Stripe cases are SKIPPED. Earlier partial runs and final runs must not be added together as distinct coverage.

## Data policy

The provided Render credentials are not committed, included in seeds, or used in traced local browser tests. QA fixtures use `example.invalid`, dummy external-service keys and local-only URLs. No SQL DELETE/TRUNCATE/DROP operation targets existing QA users or lines. Integration tests roll back only their own new rows and use schema update, not schema reset. The existing QA seed refuses a populated users table.

## Entry/exit criteria

Entry: inspected source, explicit local target, ready backend, appropriate synthetic fixtures, accepted browser selectors, enough disk space. Exit: selected cases executed or individually labeled blocked/skipped; artifacts preserved; failures triaged; data invariants verified; documentation reflects measured results. Passing every regression is not currently possible without application fixes. CI must preserve that failing status rather than hide it.

Remaining gaps: full user/auth unit coverage, transactional UI workflows, signed Stripe TEST payment/webhook fixtures, performance acceptance thresholds, and a verified GitHub Actions run.
