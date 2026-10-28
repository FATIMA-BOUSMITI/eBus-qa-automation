# eBus API testing — Phase 2

## Scope and evidence

The collection is generated from the local Spring controllers, DTOs, services and security configuration. It contains **51 executable scenarios**, plus **79 disabled manual endpoint templates**. Templates are an inventory, not automated coverage. No `/horaires` or bus-position REST endpoint was invented.

The backend application and its configuration have not been changed. Do not start it with the current environment unless `DB_URL` points to an isolated disposable PostgreSQL database: Hibernate uses `ddl-auto: update`.

## Files

| File | Purpose |
| --- | --- |
| `postman/ebus.postman_collection.json` | Importable Postman v2.1 collection, request guards and JavaScript assertions |
| `postman/local.postman_environment.json` | Local URL and empty credentials/fixture identifiers; safe to commit |
| `postman/endpoint-inventory.json` | Every controller mapping, HTTP method, source filename and line |
| `postman/fixtures/scenarios.json` | Scenario IDs, prerequisites, expected status, mutation flags and cleanup |
| `postman/fixtures/auth-negative.json` | Synthetic negative authentication examples; documentation data, not automatically iterated |
| `postman/scripts/generate.cjs` | Rebuild collection and inventories from verified scenarios and controller annotations |
| `postman/scripts/validate.cjs` | Check SDK parsing, script syntax, origin guards, unique IDs and controller mapping |
| `postman/scripts/run.cjs` | Run Newman with prerequisite checks and metadata-only reporting |
| `package.json`, `package-lock.json` | Pinned Newman dependency and reproducible installation |
| `.gitignore` | Exclude dependencies, local environments and generated execution reports |
| `docs/test-cases-api.md` | Coverage, manual execution order and expected outcomes |
| `docs/phase-2-execution.md` | Actual verification evidence and limits |

## Isolated environment prerequisites

Use Java 17, Maven, Node.js 22, an isolated PostgreSQL instance and a dedicated test JWT secret. The backend variable names verified in `application.yaml` are `DB_URL`, `DB_USERNAME`, `DB_PASSWORD`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `JWT_SECRET`. Use an email sink and Stripe TEST keys/prices only. An email sink also needs a test configuration overriding the hardcoded SMTP host/port; it is not provisioned by this phase. The collection never asks for a Stripe secret key.

The existing application does not provide a QA seed/reset endpoint. Prepare fixtures in the disposable database through your controlled test setup. Do not insert synthetic records into production. Automatic DB provisioning belongs to the later integration-test phase.

| Fixture | Required state |
| --- | --- |
| `userEmail`, `userPassword` | Dedicated USER account with a dossier |
| `adminEmail`, `adminPassword` | Dedicated ADMIN account |
| `otherUserId` | A different existing USER; never the authenticated account |
| `userId` | Existing account for anonymous/invalid JWT checks |
| `typeId` | Active test offer with a Stripe test price |
| `inactiveTypeId` | Inactive offer; authenticated account must be eligible otherwise |
| `ligneId` | Existing disposable test line |
| `abonnementId` | Disposable subscription for activation refusal |
| `expiredAbonnementId` | Persisted ACTIF subscription ending before today |
| `pendingUserId` / `rejectedUserId` | Account matching the login used for PAY-001 / PAY-002 |
| `dossierId` / `rejectedDossierId` | Separate disposable dossiers for transitions |
| `expiredJwt` | Expired token signed by the isolated backend's JWT key |
| `paidSessionId`, `unpaidSessionId`, `expiredSessionId` | Stripe TEST sessions belonging to the login account; unpaid fixture must be open, expired fixture expired and unpaid |

Use separate local environments for pending, rejected and eligible accounts. Run PAY-001 and PAY-002 separately with the matching account; these fixtures must not be substituted with another user's ID. Each authenticated scenario performs its own prerequisite login. JWTs stay in request-local variables, never in the committed environment.

## Manual Postman execution

1. Import the collection and environment; select the local environment.
2. Keep `baseUrl` at `http://localhost:8080` or `http://127.0.0.1:<port>`. All requests reject other origins.
3. Confirm independently that the local backend uses the disposable database. A loopback URL alone cannot prove database isolation.
4. Run `01 - Public smoke`. Expected health response: HTTP 200, plain text `UP`.
5. Enter credentials and fixture IDs as local values. Do not export populated environments or share the Postman console: it can contain credentials and tokens even without explicit logging.
6. Run authentication and authenticated-read folders. Security tests assert the intended rejection; HTTP 500 is not an acceptable substitute.
7. For write scenarios, set `allowMutations=true` only in the disposable environment. Use individual requests where fixtures differ.
8. Enable `allowStripeTest=true` only after confirming the backend secret and every Stripe session/price are TEST resources. This flag is an operator attestation, not automatic verification of the backend secret.
9. Keep `99 - Endpoint reference` disabled. Its requests are templates without complete query/body/auth setup. Copy an individual template, complete it from the controller and DTO, and explicitly set `runReferenceCatalog=true` only for that manual request.
10. Restore the database snapshot after dossier/payment cases. Always clean up the object lifecycle, including after intermediate failures.

Mutating folders must not be selected as an unattended full-collection run: the manual object lifecycle intentionally shares a created ID. Other automated scenarios use prepared fixtures and independent logins.

## Newman commands (PowerShell, repository root)

```powershell
npm.cmd ci --ignore-scripts --no-audit --no-fund
npm.cmd run postman:generate
npm.cmd run postman:validate
npm.cmd run postman:run
```

Default execution selects only `01 - Public smoke`. Supply secrets through your process environment or a local secret manager; never place literal passwords or JWTs in shared shell history. Variables `EBUS_USER_EMAIL`, `EBUS_USER_PASSWORD`, `EBUS_ADMIN_EMAIL`, `EBUS_ADMIN_PASSWORD`, `EBUS_EXPIRED_JWT` map to credentials. Other variables use uppercase snake case: `EBUS_OTHER_USER_ID`, `EBUS_TYPE_ID`, `EBUS_ALLOW_MUTATIONS`, `EBUS_ALLOW_STRIPE_TEST`, etc. `EBUS_BASE_URL` overrides the local origin.

```powershell
npm.cmd run postman:run -- --folder "02 - Authentication and authorization"
npm.cmd run postman:run -- --folder "03 - Authenticated reads"
npm.cmd run postman:run -- --folder "04 - Subscription eligibility (isolated fixtures)" --id PAY-001
npm.cmd run postman:run -- --folder "05 - Stripe TEST sessions only" --id STR-001
```

The runner checks `/api/health` before Newman execution. An unreachable backend produces BLOCKED, not PASS. Exit codes: `0` all selected scenarios passed, `1` assertion/runtime failure, `2` configuration/readiness/fixture blockage. An ID with no response is BLOCKED unless a runtime failure is recorded. Missing prerequisites are reported before sending the request.

Reports are generated under ignored `reports/postman/`: `validation.json` for static checks and `execution.json` for the last selected run. Each run replaces the previous execution file; archive its sanitized contents before another run when needed. Reports contain test IDs, statuses and assertion counts, without request/response bodies, credentials, JWTs or Newman error objects. Raw Newman JSON/HTML exports are deliberately not enabled because they can contain secrets. Do not add verbose reporters in CI without redaction.

## Request contracts

See `endpoint-inventory.json` for the exhaustive 79 method/path/source entries.

| Route | Actual input contract |
| --- | --- |
| `POST /users/login` | JSON `email`, `password`; response `token`, `user` |
| `POST /users/register` | Multipart `user` containing JSON; `photo`, `carteScolaire`, `attestationScolaire`, `cinPhoto`. Service currently requires all four files |
| `PATCH /users/update/{id}` | JSON fields from `UserUpdateDto` |
| `GET /users/me/dossier` | Query parameter `id`; response field is `statusDossier`, not `status` |
| `PATCH /users/update-avatar/{id}` | Multipart file part `photo` |
| `PATCH /users/resubmit-dossier/{userId}` | Multipart `cinPhoto`, `carteScolaire`, `attestationScolaire`, `photo` |
| Password-reset POST routes | JSON maps: forgot=`email`; verify=`email`,`code`; reset=`token`,`newPassword` |
| `PATCH /users/change-password` | JSON `userId`, `oldPassword`, `newPassword` |
| `POST /abonnements/subscribe` | Query `userId`, `typeId`; returns plain text Checkout URL |
| `POST /abonnements/confirm` | Query `sessionId`; plain text `EN_ATTENTE` or `ACTIF` |
| `PATCH /abonnements/{id}/status` | Query `status`: `EN_ATTENTE`, `ACTIF`, `REFUSE`, `EXPIRE`; manual ACTIF is forbidden by service |
| Dossier rejection | JSON `rejectionReason` |
| `POST /api/objets/declaration` | Multipart text fields `nom`, `description`, `ligneId`, `contact`, `type`, `statut`, `userId`, `dateDeclaration`, `busId`; optional image part `image` |
| `PUT /api/objets/{id}/statut` | Query `statut`: `EN_ATTENTE`, `DISPONIBLE`, `EN_ATTENTE_RECUPERATION`, `RECUPERE` |
| Object announcement type | `PERTE` or `TROUVE` |
| `POST /stripe/webhook` | Raw JSON and `Stripe-Signature`; real positive events require a signed TEST fixture |
| `/bus` writes | JSON `numero`, `etat`, `immatriculation`, `ligneId` |
| `/lignes` writes | JSON `numero`, `distance`, `startPoint`, `endPoint`, `stations` |
| Station writes | JSON `nom`, `ordre`, `direction`, `position` from `StationOrdreDto` |
| Ticket creation | JSON `prix`, `typeTicket` |
| Reclamation writes | JSON `titre`, `description`, `status`, `date`, `userId`, `ligneId` |
| Card writes | JSON metadata from `BankCardDto`; no real PAN/CVC test data |
| `PUT /role/{userId}` | Query `roleName` |

## Expected defects and limits

The collection intentionally does not accept 500 for invalid login, invalid object fields, invalid status, or manual subscription activation. It checks a desired client-error/security contract and may expose the global exception-handler issue identified in phase 1. Anonymous `/types-abonnement` is included as a smoke requirement because it is permitted by SecurityConfig, while its service casts the principal to User; its expected 200 may fail.

Cross-account rejection is an explicit proposed security requirement. Public lost-object catalogue visibility is recorded as implemented, pending the product decision. A failing assertion must be triaged against that requirement, not automatically called an execution-confirmed vulnerability.

Positive registration, password-reset email delivery, full bus/line/ticket/card CRUD, signed positive webhooks, and concurrent payment idempotency are manual inventory or future coverage, not automated achievements of this phase. No performance testing or production request is authorized by these assets.
