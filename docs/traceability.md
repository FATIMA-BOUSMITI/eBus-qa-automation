# Requirements Traceability Matrix

These requirements are derived from the inspected implementation and the user's QA goals. Ownership-denial expectations are explicit security requirements, not assumptions that the current application implements them correctly.

| Requirement | Automated evidence | Limits |
| --- | --- | --- |
| Public availability/catalogues | SMK-001–005; ROB-001–005; Java health; JMeter first four samplers | Anonymous offer catalogue is a known failure |
| Valid login/JWT | AUTH-001, AUTH-005–007; ROB-006; Java real-JWT integration; browser 17–20 | No real production token in traced suites |
| Invalid credentials | AUTH-002–004; ROB-016 data rows | Existing 500 handling fails intended 400/401 contract |
| Own profile/dossier | USR-001, DOS-001; ROB-006–007; Java integration | No profile mutation UI workflow |
| Cross-account protection | AUTH-008–010, ABO-004–005, CARD-002; ROB-011–015 | Failures documented; not probed on Render |
| Dossier eligibility | PAY-001–003; ROB-017–019; Mockito parameterized eligibility cases | Real Checkout TEST fixture absent |
| Expiration | ABO-003; ROB-008; JUnit past/today/future/null date cases | Effective DTO state is distinct from persisted status |
| Payment-gated activation | PAY-005; Mockito no-manual-ACTIF test; STR-004 forged signature | Successful Stripe payment/concurrent idempotency not claimed |
| Object lifecycle/recovery | OBJ-001–011 definitions; ROB-020; Mockito recovery tests; actual Java declaration/delete integration | Manual Postman ordered lifecycle skipped; UI CRUD absent |
| Registration UX | Browser 03–06, 10 | Navigation/step validation only; no submitted account |
| Password recovery UX | Browser 07–08 | No email, code verification or password update |
| Guest navigation/permissions | Browser 11–16 | Read/navigation subset |
| Authenticated navigation | Browser 17–20 | Real local API, no mocked responses |
| Controlled performance | Seven JMeter smoke samples | No capacity/endurance conclusion |
| CI execution/reporting | Workflow definitions and local helper scripts | GitHub run not yet performed; UI build supplied explicitly |

Per-case API prerequisites, input data, expected statuses and cleanup are in `postman/fixtures/scenarios.json`. Robot cases/resources and the browser scenario table provide executable steps and expected outcomes for their corresponding IDs. Real defect reproduction and observed statuses are in `phase-2-live-results.md`.
