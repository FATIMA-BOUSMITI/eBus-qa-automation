"""Visible real-backend line lifecycle; separate from the read-only local suite."""
import argparse
import html
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
API = "https://ebus-backend-ao2u.onrender.com"
UI = "http://127.0.0.1:17357"


def run(inspect_only=False, headed=True):
    expect.set_options(timeout=60000)
    number = "QA-E2E-" + uuid.uuid4().hex[:12]
    payload = dict(numero=number, startPoint=number + " Depart",
                   endPoint=number + " Arrivee", distance=1.5, stations=[])
    out = ROOT / "reports/playwright/line-lifecycle" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    report = dict(kind="real-backend-line-lifecycle", backend=API, frontend=UI,
                  number=number, mode="inspect" if inspect_only else "execute", steps=[], status="FAIL")
    created = None
    baseline = None
    token = None
    stage = "prerequisites"

    def step(name):
        report["steps"].append(name)
        print("PASS: " + name, flush=True)

    with sync_playwright() as p:
        api = p.request.new_context(base_url=API, timeout=60000, ignore_https_errors=False)
        browser = None
        try:
            accounts = json.loads((ROOT / ".tools/mobile-credentials.json").read_text(encoding="utf-8-sig"))
            account = None
            stage = "identify existing administrator"
            for alias, candidate in accounts.items():
                response = api.post("/users/login", data=candidate, max_redirects=0)
                if response.status != 200:
                    continue
                login = response.json()
                if login.get("user", {}).get("role") == "ADMIN" and login.get("token"):
                    account, token = candidate, login["token"]
                    report["account_alias"] = alias
                    break
            if not account:
                raise RuntimeError("No existing account has an accepted ADMIN session")
            step("Existing administrator identified (credentials omitted)")

            def catalogue():
                response = api.get("/lignes", max_redirects=0)
                if response.status != 200 or not isinstance(response.json(), list):
                    raise RuntimeError("Catalogue unavailable")
                return response.json()

            baseline = {str(row["id"]): row for row in catalogue()}
            if any(row.get("numero") == number for row in baseline.values()):
                raise RuntimeError("Unique number collision")
            report["initial_line_count"] = len(baseline)
            browser = p.chromium.launch(channel="chrome", headless=not headed, slow_mo=650)
            context = browser.new_context(viewport={"width": 1440, "height": 1100}, service_workers="block")
            page = context.new_page()
            page.set_default_timeout(30000)
            def label(value):
                return page.get_by_text(value, exact=True).or_(page.get_by_label(value, exact=True))
            def test_line():
                # Flutter merges number, title and itinerary into one aria-label.
                return page.get_by_label(re.compile(r"(?:^|\n)Ligne " + re.escape(number) + r"(?:\n|$)"))

            def transport(route):
                nonlocal created
                request = route.request
                parsed = urlsplit(request.url)
                path, method = parsed.path, request.method
                body = request.post_data_json if method == "POST" else None
                if method == "POST" and path == "/users/login":
                    report["ui_login_matches_selected_account"] = isinstance(body, dict) and all(body.get(key) == value for key, value in account.items())
                permitted = method in ("GET", "HEAD", "OPTIONS") or (method == "POST" and path == "/users/login")
                if not inspect_only and method == "POST" and path == "/lignes/new" and created is None:
                    permitted = isinstance(body, dict) and all(body.get(key) == value for key, value in payload.items())
                if not inspect_only and method == "DELETE" and created is not None and path == f"/lignes/{created}":
                    rows = catalogue()
                    permitted = any(str(row["id"]) == str(created) and row.get("numero") == number for row in rows)
                    permitted = permitted and str(created) not in baseline
                if not permitted:
                    route.abort("blockedbyclient")
                    return
                response = route.fetch(max_redirects=0, timeout=60000)
                if method == "POST" and path == "/lignes/new" and response.ok:
                    row = response.json()
                    if row.get("numero") != number or str(row.get("id")) in baseline or row.get("id") is None:
                        raise RuntimeError("Unsafe creation response")
                    created = row["id"]
                    report["created_id"] = created
                route.fulfill(response=response, headers={**response.headers, "access-control-allow-origin": "*"})

            # No other service receives writes. The API route forwards real responses unchanged.
            page.route("**/*", lambda route: route.continue_() if route.request.method in ("GET", "HEAD", "OPTIONS") else route.abort("blockedbyclient"))
            def safe_transport(route):
                try:
                    transport(route)
                except Exception:
                    # Playwright event-handler exceptions otherwise print request
                    # headers (including JWTs). Never let them escape the callback.
                    report.setdefault("transport_failures", 0)
                    report["transport_failures"] += 1
                    try:
                        route.abort("failed")
                    except Exception:
                        pass
            page.route(API + "/**", safe_transport)
            stage = "open frontend and enable Flutter semantics"
            page.goto(UI, wait_until="domcontentloaded", timeout=60000)
            semantics = page.locator("flt-semantics-placeholder")
            semantics.wait_for(state="attached", timeout=90000)
            semantics.evaluate("element => element.click()")
            expect(page.get_by_text("Bienvenue sur eBus", exact=False)).to_be_visible(timeout=90000)
            page.get_by_text("Accès administrateur", exact=True).click()
            stage = "administrator UI login"
            email = page.get_by_role("textbox").first
            email.click()
            email.press_sequentially(account["email"])
            password = page.locator('input[type="password"]')
            password.click()
            password.press_sequentially(account["password"])
            with page.expect_response(lambda r: urlsplit(r.url).path == "/users/login" and r.request.method == "POST", timeout=60000) as login_response:
                page.get_by_text("Connexion Admin", exact=True).last.click()
            if login_response.value.status != 200:
                report["ui_login_http_status"] = login_response.value.status
                raise RuntimeError("UI login rejected")
            stage = "open line management"
            page.get_by_text("Gestion des lignes", exact=True).click()
            expect(page.get_by_role("textbox").first).to_be_visible()
            # Wait for the catalogue response and Flutter semantics text, not
            # the transient editable field retained during route animation.
            expect(label("Gestion des lignes")).to_be_visible(timeout=60000)
            step("Administrator logged in through UI; real line catalogue opened")
            # Only button labels/roles, no page dumps, account data, tokens or traces.
            if inspect_only:
                report["buttons"] = page.get_by_role("button").evaluate_all(
                    "items => items.map(e=>({label:e.getAttribute('aria-label'),text:e.innerText,tag:e.tagName}))")
                report["line_headings"] = page.get_by_text(re.compile("ligne", re.I)).all_text_contents()
                report["line_aria_labels"] = page.locator('[aria-label]').evaluate_all("items => items.map(e=>e.getAttribute('aria-label')).filter(s=>/ligne/i.test(s))")
                page.screenshot(path=str(out / "catalogue.png"))
                (out / "inspection.json").write_text(json.dumps(report["buttons"], ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps({"line_headings": report["line_headings"], "line_aria_labels": report["line_aria_labels"], "button_count": len(report["buttons"])}, ensure_ascii=True), flush=True)
                report["status"] = "INSPECTED"
                return 0

            stage = "open create form"
            # Runtime-accepted management toolbar: back then add icon button.
            page.get_by_role("button").nth(1).click()
            expect(label("Nouvelle ligne")).to_be_visible()
            fields = page.get_by_role("textbox")
            for index, value in enumerate((number, payload["startPoint"], payload["endPoint"], "1.5")):
                field = fields.nth(index)
                field.click()
                field.press_sequentially(value)
            stage = "create line through UI"
            with page.expect_response(lambda r: urlsplit(r.url).path == "/lignes/new" and r.request.method == "POST", timeout=60000) as creation:
                page.get_by_text(re.compile(r"^(Creer|Créer) la ligne$")).click()
            if creation.value.status not in (200, 201) or created is None:
                raise RuntimeError("Creation not confirmed by API")
            rows = catalogue()
            row = next((row for row in rows if str(row["id"]) == str(created)), None)
            if not row or any(row.get(key) != value for key, value in payload.items()):
                raise RuntimeError("Persisted line differs from submitted values")
            step("Unique line persisted in real backend with expected fields")
            stage = "verify created line in UI"
            expect(label("Nouvelle ligne")).to_have_count(0)
            search = page.get_by_role("textbox").first
            search.click()
            search.press_sequentially(number)
            expect(search).to_have_value(number)
            expect(test_line()).to_be_visible()
            step("Unique line created through UI and verified in backend catalogue and UI")
            stage = "delete only the created line through UI"
            # Search is unique; refuse deletion unless exactly this line is visible.
            expect(test_line()).to_have_count(1)
            page.get_by_role("button").nth(2).click()
            expect(label("Supprimer la ligne")).to_be_visible()
            with page.expect_response(lambda r: urlsplit(r.url).path == f"/lignes/{created}" and r.request.method == "DELETE", timeout=60000) as deletion:
                page.get_by_text("Supprimer", exact=True).click()
            if deletion.value.status not in (200, 204):
                raise RuntimeError("Deletion rejected")
            expect(test_line()).to_have_count(0)
            remaining = {str(row["id"]): row for row in catalogue()}
            if str(created) in remaining or any(row.get("numero") == number for row in remaining.values()):
                raise RuntimeError("Deleted line still persisted")
            if any(remaining.get(key) != value for key, value in baseline.items()):
                raise RuntimeError("Existing catalogue changed during the run")
            report["existing_lines_unchanged"] = True
            step("Created line deleted through UI; absence confirmed in UI and backend; existing lines unchanged")
            report["status"] = "PASS"
            return 0
        except Exception as error:
            # Never persist exception messages: selectors/network errors can include secrets.
            report["failed_stage"] = stage
            report["error_type"] = type(error).__name__
            if stage == "verify created line in UI":
                try:
                    report["matching_test_labels"] = page.get_by_text(re.compile(re.escape(number))).all_text_contents()
                    report["search_value_matches"] = page.get_by_role("textbox").first.input_value() == number
                    report["management_visible"] = page.get_by_text("Gestion des lignes", exact=True).is_visible()
                except Exception:
                    pass
            print(f"FAIL: {stage} ({type(error).__name__}); sensitive details omitted", flush=True)
            return 1
        finally:
            if baseline is not None and not inspect_only and token:
                try:
                    # Recover only a unique row absent from the baseline if response was interrupted.
                    matches = [row for row in catalogue() if row.get("numero") == number and str(row["id"]) not in baseline]
                    if len(matches) == 1 and all(matches[0].get(k) == v for k, v in payload.items()):
                        target = matches[0]["id"]
                        result = api.delete(f"/lignes/{target}", headers={"Authorization": "Bearer " + token}, max_redirects=0)
                        report["fallback_cleanup"] = result.status in (200, 204)
                        # Cleanup never converts a failed UI scenario into PASS.
                    final_rows = {str(row["id"]): row for row in catalogue()}
                    report["test_line_absent_after_cleanup"] = not any(row.get("numero") == number for row in final_rows.values())
                    report["existing_lines_unchanged_after_cleanup"] = all(final_rows.get(key) == value for key, value in baseline.items())
                    report["final_line_count"] = len(final_rows)
                except Exception:
                    report["cleanup_requires_attention"] = True
            if browser:
                try:
                    context.unroute_all(behavior="ignoreErrors")
                    browser.close()
                except Exception:
                    report["browser_close_warning"] = True
            try:
                api.dispose()
            except Exception:
                report["api_close_warning"] = True
            (out / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            (out / "report.html").write_text(
                '<!doctype html><html lang="fr"><meta charset="utf-8"><title>eBus — Ligne E2E</title>'
                '<body><h1>Ligne E2E : ' + html.escape(report["status"]) + '</h1><pre>'
                + html.escape(json.dumps(report, ensure_ascii=False, indent=2)) + '</pre></body></html>', encoding="utf-8")
            print("Report: " + str(out / "summary.json"), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true", help="Login and inspect catalogue controls; no line writes")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    sys.exit(run(args.inspect, not args.headless))
