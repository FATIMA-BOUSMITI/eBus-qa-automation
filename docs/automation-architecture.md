# Automation Architecture

The existing application remains a Spring MVC/JPA monolith with DTO/mappers and a Flutter BLoC frontend. QA surrounds it rather than replacing business services.

Java unit tests inject Mockito repositories/Stripe and check business decisions and side effects. MockMvc integration tests instantiate the application, authenticate against a real persisted USER and exercise an actual object declaration/deletion. Their database connection is explicitly pinned to a separate local integration DB, and responses are not printed.

The Postman generator checks each scenario's method/path against controller mappings and emits a manual reference catalogue separately from automated coverage. The Newman runner uses per-scenario authentication, prerequisite checks and metadata-only reports. The local orchestrator prepares an expired synthetic JWT, selects matching dossier-state accounts and avoids real Stripe cases.

Robot's Python adapter wraps RequestsLibrary/JSONLibrary without returning tokens or raw login responses to Robot keywords. Resource keywords express reusable contracts; each test has its own session. Logging is suppressed for HTTP internals, while failed assertions retain safe status/field messages.

Playwright uses a fresh context per scenario, activates Flutter semantics and addresses real text/roles. Flutter's editing controller required focusing the editor and using keyboard events for login; the test never substitutes correct credentials into an incorrect API payload. The actual admin login action is `Connexion Admin`. Known compiled Render-origin API calls are forwarded to the dedicated local backend and its genuine response is returned. Other writes and Stripe navigation are blocked. This is transport remapping, not API response mocking.

JMeter uses CSV accounts, HTTP samplers/header managers, JSON JWT/user-ID extraction, status assertions and paced thread groups. Save settings omit bodies and headers. Native Windows execution replaced a Docker tool image corrupted during the earlier disk-full event; the replacement distribution was verified against Apache's SHA-512.

Generated reports are ignored by Git; sanitized summaries and the blank public login screenshot are portfolio-safe. Browser traces may contain synthetic local fixture tokens and must remain private. CI definitions upload short-lived artifacts and preserve regression failures. No external deployment or message/publication is performed by this repository work.
