> Historique des exécutions. Pour les commandes actuelles sans Docker, consulter le [README principal](../README.md) et les guides de chaque outil. Les difficultés anciennes décrites ci-dessous ne représentent pas nécessairement l’état courant du poste.

# Final test execution record

Date: 2026-10-26 UTC. Sanitized machine-readable evidence: [results/verified.json](results/verified.json). Earlier partial/debug runs are not added to final counts.

| Suite | PASS | FAIL | SKIPPED | Notes |
| --- | ---: | ---: | ---: | --- |
| Java unit | 41 | 0 | 0 | Mockito repositories/Stripe, no real DB |
| Java context/integration | 5 | 0 | 0 | Separate PostgreSQL, real JWT, MockMvc and persistence |
| Robot API | 12 | 8 | 0 | Known application errors/ownership defects reproduced |
| Playwright final complete selection | 20 | 0 | 0 | Real local Flutter/API, no mocked responses; 319.89 s |
| JMeter local one-user smoke | 7 samples | 0 | 0 | Seven measured HTTP requests, not seven independent business workflows |
| Historical Newman selection | 25 | 16 | 10 | Earlier recorded run; distinct from Robot |

## Backend and preservation

The final Java run targeted `C:\Users\fatouma\Downloads\eBus_back\eBus_back`, the backend explicitly identified by the user. It passed all 46 tests with schema mode `update`. Validated tests/JaCoCo also exist in the workspace backend copy. The actual API runtime was packaged from the Downloads backend and connected only to the dedicated QA PostgreSQL database.

A final read-only QA check returned **users=5, lines=1**. No existing QA user or line was deleted. Java integration tests roll back only their own newly created fixture rows; their object deletion targets the object created inside that test. No production account/line deletion or schema reset was executed by these final suites.

The follow-up read-only fingerprint check also matched all five original fixture ID/email identities and the original line ID/number. Counts are read from the database by `qa/check_preservation.py`, not inferred from test PASS totals.

## Robot failures

ROB-005, ROB-011–016 and ROB-020 failed. Observations match the previously documented anonymous catalogue error, incorrect 500 statuses for rejected requests, and missing cross-account rejection. ROB-016 contains three failed credential rows but counts as one Robot case, so there are eight failed cases, not ten. Detailed safe status messages are in `reports/robot/report.html`, `log.html`, `output.xml`.

## Browser diagnosis and final acceptance

An initial six-case preflight had five passes and one false failure: the registration text was visibly preserved in the screenshot but Flutter's inactive editor proxy exposed an empty DOM value. Focusing the editor before reading it corrected the test without changing the app.

A subsequent full run had 17 passes and three failures. Two were incorrect test assumptions about the administrator action label (actual source/DOM label: `Connexion Admin`). A safe trace inspection proved the third request contained the expected synthetic email but the wrong password after direct DOM filling. Keyboard events after focus delivered the intended value to Flutter's controller. The test did not replace or mock the API payload to force success.

The five affected/related authentication cases then passed. The final consolidated run executed all **20 cases and passed all 20**. The scope includes smoke, step validation, navigation, guest permission dialogs and four authenticated E2E journeys; it does not establish completed transactional registration/payment/UI CRUD coverage.

The public Render UI inspection timed out waiting for the login screen. It is a separate unaccepted observation, not a local suite failure and not a deployed UI PASS. Earlier successful deployed login/API-read records remain in their own reports.

## Java coverage and privacy

Measured per-class line counts/percentages from final JaCoCo are copied into `results/verified.json`. They are combined unit/integration measurements for the named classes. No claim is made of 80% coverage for every service or the complete application.

HTTP DEBUG output was explicitly disabled in integration configuration; final Surefire reports were checked for JWT output patterns. No raw production credential or token is part of the committed evidence. Browser traces may contain synthetic local fixture values and remain in ignored local artifacts.

## Android Appium preparation

The separate [Android suite](../appium/README.md) contains 20 Robot/Appium UI journeys. Appium 3.8.0 and UiAutomator2 8.7.1 are installed; Doctor reports zero required fixes. Python compilation, PowerShell parsing and Robot dry-run validated the implementation. These are static/preparation results, not Android functional PASS results.

The initial preparation lacked Flutter and a connected device; see [historical preparation evidence](results/appium-preparation.json). Flutter 3.47.8 / Dart 3.13.7 is now installed, and a separate Render-targeted APK was compiled, installed and launched on the Android 12 Redmi. The original app is preserved. Runtime logs show the Render health URL, and the user confirmed data loads.

The first real Appium attempt (MOB-001) failed during setup: Android rejected the UiAutomator2 server installation because internal storage was insufficient (516 MB free). No functional test body ran and no mobile PASS is claimed. The user must free phone storage before retrying. See [current mobile evidence](results/render-mobile.json). No database mutations or app storage resets were performed.

## Performance and CI results

See `performance-report.md`: seven samples, zero failures, mean 311.71 ms, nearest-rank P90/P95/P99 604 ms. No load/capacity or SLA conclusion follows from that small sample.

GitHub workflows are implemented but not run remotely. Progressive/endurance, successful Stripe TEST payments and full registration/payment browser workflows remain unexecuted. The separate real-backend line lifecycle and seven business scenarios are now verified below. Allure result JSON exists; an Allure HTML rendering is not claimed. These limits remain visible in the README and portfolio wording.

## Real-backend business E2E

The separate [business suite](playwright-business-e2e.md) has seven real browser cases using existing USER/ADMIN credentials against Render. The initial complete run had 5 PASS / 2 FAIL. Targeted reruns validated the remaining claim-processing and inactive-offer cases. Current per-case consolidated outcome: **7 PASS / 0 FAIL after reruns**, not one single complete passing run. Earlier locator failures and a prerequisite connection timeout remain in the history.

USER/ADMIN object status tracking, claim processing and offer creation/edit/cancel-delete/delete were verified through the UI and actual backend responses. Each passing case verified removal of its temporary records and preservation of existing records in the checked catalogues. Actual subscription purchase/activation and Stripe payments remain outside this result. Evidence: `results/playwright-business-e2e.json`; local report: `reports/playwright/business-e2e/consolidated/report.html` from the project root.
