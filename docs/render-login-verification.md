# Render login verification

Date: 2026-10-26 UTC.

The user supplied three accounts and explicitly requested testing them. Only successful-credential login requests were sent to `POST https://ebus-backend-ao2u.onrender.com/users/login`. No write scenarios, payment requests, load tests or cross-account checks were executed.

| Account | HTTP status | JWT returned | Role returned |
| --- | --- | --- | --- |
| ACCOUNT1 | 200 | Yes | USER |
| ACCOUNT2 | 200 | Yes | USER |
| ACCOUNT3 | 200 | Yes | ADMIN |

Result: **PASS 3 / FAIL 0 / BLOCKED 0** for these login checks only. The initial network-restricted attempts could not reach the service. With network access, the first account initially timed out; its retry returned HTTP 200 after the other two accounts had succeeded. The timeout does not establish an application defect or invalid credentials.

Passwords, JWT values and raw responses are intentionally excluded. The local-only Postman collection and runner have not been changed to allow production execution. These direct login checks do not establish that the rest of the Postman suite passed, nor that Render is an isolated test environment.
