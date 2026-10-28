"""Real browser USER/ADMIN workflows. No production payment or existing-row writes."""
import argparse
import html
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright
from deployed_config import API, browser_channel, frontend_url, load_accounts

ROOT = Path(__file__).resolve().parents[1]
UI = frontend_url()
RESOURCES = {
    "object": ("/api/objets/admin/all", "/api/objets/declaration", "/api/objets", "nom"),
    "claim": ("/reclamations/all", "/reclamations/new", "/reclamations", "titre"),
    "offer": ("/types-abonnement", "/types-abonnement", "/types-abonnement", "nom"),
}


def label(page, value, exact=True):
    return page.get_by_text(value, exact=exact).or_(page.get_by_label(value, exact=exact))


def input_value(page, index, value):
    field = page.get_by_role("textbox").nth(index)
    field.click()
    field.fill("")
    field.press_sequentially(str(value))


def enable_semantics(page):
    page.locator("flt-semantics-placeholder, flt-semantics[aria-label]").first.wait_for(state="attached", timeout=90000)
    placeholder = page.locator("flt-semantics-placeholder")
    if placeholder.count():
        placeholder.evaluate("element => element.click()")


def multipart_fields(request):
    content_type = request.headers.get("content-type", "")
    raw = request.post_data_buffer or b""
    message = BytesParser(policy=policy.default).parsebytes(
        ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + raw)
    return {part.get_param("name", header="content-disposition"): part.get_content()
            for part in message.iter_parts() if part.get_filename() is None}


class BusinessRun:
    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, value):
        self._stage = value
        if getattr(self, "current", None):
            print("STEP: " + self.current["id"] + " " + value, flush=True)

    def __init__(self, playwright, headed):
        expect.set_options(timeout=60000)
        self.api = playwright.request.new_context(base_url=API, timeout=60000)
        self.browser = None
        self.accounts = {}
        self.headed = headed
        self.stage = "prerequisites"
        self.cases = []
        self.contexts = []
        self.current = None
        self.baseline = {}
        self.owned = {}
        self.marker = None
        self.preflight = {}
        self.required_roles = {"USER", "ADMIN"}

    def authenticate_accounts(self):
        accounts = load_accounts(self.required_roles)
        for alias, credential in reversed(list(accounts.items())):
            try:
                response = self.api.post("/users/login", data=credential, max_redirects=0)
            except Exception as error:
                self.preflight[alias] = type(error).__name__
                continue
            self.preflight[alias] = response.status
            if response.status != 200:
                continue
            data = response.json()
            role = data.get("user", {}).get("role")
            if role in ("USER", "ADMIN") and role not in self.accounts and data.get("token"):
                self.accounts[role] = dict(alias=alias, credential=credential, token=data["token"], id=data["user"]["id"])
            if self.required_roles <= self.accounts.keys():
                break
        if not self.required_roles <= self.accounts.keys():
            raise RuntimeError("Existing USER and ADMIN accounts are required")
        print("CHECK: Required existing accounts verified; secrets omitted", flush=True)
        self.browser = self._playwright.chromium.launch(channel=browser_channel(), headless=not self.headed, slow_mo=450)

    def rows(self, kind):
        response = self.api.get(RESOURCES[kind][0], headers={"Authorization": "Bearer " + self.accounts["ADMIN"]["token"]}, max_redirects=0)
        if response.status != 200 or not isinstance(response.json(), list):
            raise RuntimeError("Real catalogue unavailable")
        return response.json()

    def owned_row(self, kind):
        identifier = self.owned.get(kind)
        if identifier is None or str(identifier) in self.baseline[kind]:
            return None
        field = RESOURCES[kind][3]
        return next((row for row in self.rows(kind) if row["id"] == identifier and row.get(field) == self.marker
                     and (kind == "offer" or row.get("userId") == self.accounts["USER"]["id"])), None)

    def permitted(self, method, path, body, query):
        if method in ("GET", "HEAD", "OPTIONS") or (method == "POST" and path == "/users/login"):
            return True
        if self.current["id"] in ("BIZ-005", "BIZ-006", "BIZ-007"):
            return False
        for kind, (_, create, prefix, field) in RESOURCES.items():
            if method == "POST" and path == create and kind not in self.owned:
                if not isinstance(body, dict) or body.get(field) != self.marker:
                    return False
                if kind == "offer":
                    return (self.current["id"] == "BIZ-004" and body.get("actif") is False
                            and body.get("prix") == 3.5 and body.get("dureeMois") == 1
                            and not body.get("stripePriceId"))
                if str(body.get("userId")) != str(self.accounts["USER"]["id"]):
                    return False
                if str(body.get("ligneId")) not in self.line_ids or body.get("description") != self.marker + " description":
                    return False
                if kind == "object":
                    return self.current["id"] in ("BIZ-001", "BIZ-002") and body.get("type") == self.object_type and body.get("statut") == "EN_ATTENTE"
                return self.current["id"] == "BIZ-003"
            identifier = self.owned.get(kind)
            if identifier is None or not path.startswith(prefix + "/" + str(identifier)):
                continue
            if not self.owned_row(kind):
                return False
            if method == "DELETE" and path == f"{prefix}/{identifier}":
                return True
            if kind == "object" and method == "PUT" and path == f"{prefix}/{identifier}/statut":
                return query.get("statut") in (["DISPONIBLE"], ["RECUPERE"])
            if kind == "claim" and method == "PATCH" and path == f"{prefix}/{identifier}":
                return body == {"status": "TRAITEE"}
            if kind == "offer" and method == "PUT" and path == f"{prefix}/{identifier}":
                return body.get("nom") == self.marker and body.get("actif") is False and body.get("prix") == 4.5 and body.get("dureeMois") == 2 and not body.get("stripePriceId")
        return False

    def route(self, route):
        try:
            request = route.request
            parsed = urlsplit(request.url)
            method = request.method
            body = None
            if method in ("POST", "PUT", "PATCH"):
                if "multipart/form-data" in request.headers.get("content-type", ""):
                    body = multipart_fields(request)
                elif request.post_data:
                    body = request.post_data_json
            if not self.permitted(method, parsed.path, body, parse_qs(parsed.query)):
                self.current.setdefault("blocked_writes", []).append(method + " " + parsed.path)
                route.abort("blockedbyclient")
                return
            if method not in ("GET", "HEAD", "OPTIONS") and parsed.path != "/users/login":
                self.current["business_write_attempts"] += 1
            response = route.fetch(max_redirects=0, timeout=60000)
            for kind, (_, create, _, field) in RESOURCES.items():
                if method == "POST" and parsed.path == create and response.ok:
                    row = response.json()
                    if row.get(field) != self.marker or row.get("id") is None or str(row["id"]) in self.baseline[kind]:
                        raise RuntimeError("Creation response did not identify a new owned row")
                    self.owned[kind] = row["id"]
                    self.current.setdefault("created", {})[kind] = row["id"]
            route.fulfill(response=response, headers={**response.headers, "access-control-allow-origin": "*"})
        except Exception:
            # Callback errors must never print authorization headers or typed secrets.
            self.current["transport_errors"] = self.current.get("transport_errors", 0) + 1
            try:
                route.abort("failed")
            except Exception:
                pass

    def page(self, role):
        context = self.browser.new_context(viewport={"width": 1440, "height": 1100}, service_workers="block")
        self.contexts.append(context)
        page = context.new_page()
        page.set_default_timeout(60000)
        page.route("**/*", lambda route: route.continue_() if route.request.method in ("GET", "HEAD", "OPTIONS") else route.abort("blockedbyclient"))
        page.route(API + "/**", self.route)
        page.goto(UI, wait_until="domcontentloaded", timeout=60000)
        enable_semantics(page)
        expect(label(page, "Bienvenue sur eBus", exact=False)).to_be_visible(timeout=90000)
        if role == "GUEST":
            label(page, "Continuer en tant qu'invité").click()
            expect(label(page, "Accès rapide")).to_be_visible()
            return page
        self.stage = "UI login " + role
        if role == "ADMIN":
            label(page, "Accès administrateur").click()
        credential = self.accounts[role]["credential"]
        input_value(page, 0, credential["email"])
        password = page.locator('input[type="password"]')
        password.click()
        password.press_sequentially(credential["password"])
        with page.expect_response(lambda r: urlsplit(r.url).path == "/users/login" and r.request.method == "POST", timeout=60000) as login:
            label(page, "Connexion Admin" if role == "ADMIN" else "Se Connecter").last.click()
        if login.value.status != 200 or login.value.json().get("user", {}).get("id") != self.accounts[role]["id"]:
            raise RuntimeError("UI session does not match the selected existing account")
        expect(label(page, "Gestion rapide" if role == "ADMIN" else "Accès rapide")).to_be_visible()
        return page

    def fresh_home(self, page, role):
        # Named Flutter routes change the URL fragment. Reloading that fragment
        # would reopen the detail/list route instead of the authenticated home.
        # A fresh root document preserves this actor's storage and reloads data.
        page.goto(UI + "/?e2e_refresh=" + uuid.uuid4().hex[:8], wait_until="domcontentloaded")
        enable_semantics(page)
        expect(label(page, "Gestion rapide" if role == "ADMIN" else "Accès rapide")).to_be_visible(timeout=90000)

    def step(self, name):
        self.current["steps"].append(name)
        print("PASS: " + self.current["id"] + " " + name, flush=True)

    def newest(self, page, objects=False):
        page.get_by_role("button").nth(1).click()
        label(page, "Plus récents" if objects else "Plus récentes").click()

    def marker_card(self, page):
        # A search textbox also exposes its typed value in semantics. Never click
        # that editor when the intended target is a record's merged card label.
        selector = ('[aria-label*="' + self.marker + '"]:not(input):not(textarea)'
                    ':not([role="textbox"]):not(:has(input)):not(:has(textarea))')
        return page.get_by_text(self.marker, exact=True).or_(page.locator(selector))

    def open_objects(self, page, admin=False):
        label(page, "Objets perdus").click()
        if admin:
            expect(label(page, "Gestion Objets Perdus")).to_be_visible()
            self.newest(page, objects=True)
        else:
            expect(page.get_by_role("textbox").first).to_be_visible()
            input_value(page, 0, self.marker)

    def assert_row(self, kind, **expected):
        row = self.owned_row(kind)
        if row is None or any(row.get(key) != value for key, value in expected.items()):
            raise AssertionError("Persisted test record has an unexpected state")

    def object_flow(self, found=False, validation=False):
        self.object_type = "TROUVE" if found else "PERTE"
        user = self.page("USER")
        self.stage = "object declaration form"
        self.open_objects(user)
        # Search must be cleared before declaring; it is not persisted after returning.
        input_value(user, 0, "")
        self.stage = "open declaration form"
        label(user, "Déclarer").click()
        expect(label(user, "Déclarer un objet perdu")).to_be_visible()
        if validation:
            self.stage = "submit empty object form"
            label(user, "VALIDER").click()
            self.stage = "required object date error"
            expect(label(user, "Date requise", exact=False).first).to_be_visible()
            expect(label(user, "Champ requis", exact=False).first).to_be_visible()
            if self.current["business_write_attempts"] or self.current.get("blocked_writes"):
                raise AssertionError("Invalid form attempted a backend write")
            self.step("Required object fields rejected before any write")
            return
        if found:
            label(user, "J'ai trouvé").click()
        input_value(user, 0, self.marker)
        label(user, "Sélectionner la ligne").click()
        label(user, "Ligne " + self.line_number).last.click()
        user.get_by_role("textbox").nth(1).click()
        label(user, re.compile(r"^(OK|Confirmer)$")).last.click()
        # Date is readonly textbox index 1; description and contact follow it.
        input_value(user, 2, self.marker + " description")
        input_value(user, 3, "0600000000")
        self.stage = "create object via UI"
        with user.expect_response(lambda r: urlsplit(r.url).path == RESOURCES["object"][1] and r.request.method == "POST", timeout=60000) as response:
            label(user, "VALIDER").click()
        if response.value.status not in (200, 201):
            raise AssertionError("Object declaration rejected")
        self.assert_row("object", type=self.object_type, statut="EN_ATTENTE")
        self.step("Object created via UI and verified in real backend as EN_ATTENTE")
        self.stage = "reload USER and open created object"
        self.fresh_home(user, "USER")
        self.open_objects(user)
        expect(self.marker_card(user).first).to_be_visible()
        self.marker_card(user).first.click()
        self.stage = "USER sees initial object status"
        expect(label(user, "En attente", exact=False).first).to_be_visible()
        self.step("USER declaration persisted and displayed as En attente")
        admin = self.page("ADMIN")
        self.stage = "administrator validates only the new object"
        self.open_objects(admin, admin=True)
        self.marker_card(admin).first.click()
        label(admin, "VALIDER & RENDRE DISPONIBLE").click()
        with admin.expect_response(lambda r: r.request.method == "PUT" and urlsplit(r.url).path == f'/api/objets/{self.owned["object"]}/statut', timeout=60000) as updated:
            label(admin, "Confirmer").click()
        if updated.value.status != 200:
            raise AssertionError("Admin object transition rejected")
        self.assert_row("object", statut="DISPONIBLE")
        self.fresh_home(user, "USER")
        self.open_objects(user)
        self.marker_card(user).first.click()
        expect(label(user, "Disponible", exact=False).first).to_be_visible()
        self.step("ADMIN made object Disponible; USER sees the new persisted status")
        if not found:
            # Reopen details from fresh data; the app caches the original detail DTO.
            self.fresh_home(admin, "ADMIN")
            self.open_objects(admin, admin=True)
            self.marker_card(admin).first.click()
            self.stage = "administrator completes recovery"
            label(admin, "MARQUER COMME RÉCUPÉRÉ").click()
            with admin.expect_response(lambda r: r.request.method == "PUT" and urlsplit(r.url).path == f'/api/objets/{self.owned["object"]}/statut', timeout=60000) as recovered:
                label(admin, "Confirmer").click()
            if recovered.value.status != 200:
                raise AssertionError("Recovery transition rejected")
            self.assert_row("object", statut="RECUPERE")
            self.fresh_home(user, "USER")
            self.open_objects(user)
            self.marker_card(user).first.click()
            expect(label(user, "Clôturé", exact=False).first).to_be_visible()
            self.step("ADMIN marked recovered; USER sees Cloture (RECUPERE) after reload")

    def claim_flow(self, validation=False):
        user = self.page("USER")
        self.stage = "new claim form"
        label(user, "Réclamations").click()
        # FAB is the last button after back and sort on the list screen.
        user.get_by_role("button").last.click()
        expect(label(user, "Nouvelle réclamation")).to_be_visible()
        if validation:
            label(user, "Soumettre la réclamation").click()
            expect(label(user, "Veuillez sélectionner une ligne")).to_be_visible()
            if self.current["business_write_attempts"] or self.current.get("blocked_writes"):
                raise AssertionError("Missing-line claim attempted a backend write")
            self.step("Claim without a line rejected before any backend write")
            return
        input_value(user, 0, self.marker)
        input_value(user, 1, self.marker + " description")
        label(user, "Sélectionner une ligne").click()
        label(user, self.line_number).last.click()
        self.stage = "submit claim through UI"
        with user.expect_response(lambda r: urlsplit(r.url).path == "/reclamations/new" and r.request.method == "POST", timeout=60000) as created:
            label(user, "Soumettre la réclamation").click()
        if created.value.status not in (200, 201):
            raise AssertionError("Claim creation rejected")
        self.assert_row("claim", status="EN_ATTENTE")
        self.fresh_home(user, "USER")
        label(user, "Réclamations").click()
        self.newest(user)
        expect(self.marker_card(user).first).to_be_visible()
        self.step("USER claim persisted and displayed in the catalogue")
        admin = self.page("ADMIN")
        self.stage = "administrator processes claim"
        label(admin, "Réclamations").click()
        self.newest(admin)
        title = self.marker_card(admin).first
        expect(title).to_be_visible()
        # Restrict the dropdown to the nearest semantics container holding this title.
        card = title.locator("xpath=ancestor::flt-semantics[.//*[@role='button' or @role='combobox']][1]")
        pending = re.compile("En attente", re.I)
        card.get_by_role("button", name=pending).or_(card.get_by_role("combobox", name=pending)).first.click()
        with admin.expect_response(lambda r: r.request.method == "PATCH" and urlsplit(r.url).path == f'/reclamations/{self.owned["claim"]}', timeout=60000) as updated:
            label(admin, "Traitée").last.click()
        if updated.value.status != 200:
            raise AssertionError("Claim processing rejected")
        self.assert_row("claim", status="TRAITEE")
        self.fresh_home(user, "USER")
        label(user, "Réclamations").click()
        self.newest(user)
        title = self.marker_card(user).first
        expect(title).to_be_visible()
        # Check status on the same card, never another user's claim.
        card = title.locator("xpath=ancestor::flt-semantics[contains(@aria-label,'Traitée') or .//*[contains(@aria-label,'Traitée')]][1]")
        expect(card).to_be_visible()
        self.step("ADMIN set Traitee; USER sees Traitee on their own test claim")

    def offer_flow(self):
        admin = self.page("ADMIN")
        self.stage = "open offer management"
        navigation = re.compile(r"^Gestion(?:$|\n|,|\s+(?:Tab|Onglet))", re.I)
        admin.get_by_role("tab", name=navigation).or_(admin.get_by_role("button", name=navigation)).last.click()
        expect(label(admin, "Gestion des Offres")).to_be_visible()
        self.stage = "open subscription offer form"
        # Exclude named bottom-navigation buttons (including Profil).
        icons = admin.get_by_role("button", name="", exact=True)
        icons.last.click()
        expect(label(admin, "Nouvel Abonnement")).to_be_visible()
        self.stage = "fill inactive offer form"
        input_value(admin, 0, self.marker)
        input_value(admin, 1, "3.5")
        input_value(admin, 2, "1")
        active = admin.get_by_role("switch")
        expect(active).to_be_checked()
        active.click()
        # Flutter commits semantics on the next frame; atomic uncheck() can
        # inspect the old aria-checked state before that frame is rendered.
        expect(active).not_to_be_checked()
        self.stage = "create inactive subscription offer via UI"
        with admin.expect_response(lambda r: r.request.method == "POST" and urlsplit(r.url).path == "/types-abonnement", timeout=60000) as response:
            label(admin, "Valider").click()
        if response.value.status not in (200, 201):
            raise AssertionError("Offer creation rejected")
        self.assert_row("offer", prix=3.5, dureeMois=1, actif=False)
        # Toolbar search narrows the UI before any edit or delete icon is used.
        self.stage = "filter new subscription offer"
        icons.first.click()
        input_value(admin, 0, self.marker)
        formatted = self.marker[0] + self.marker[1:].lower()
        card_label = label(admin, re.compile(re.escape(formatted)))
        expect(card_label.first).to_be_visible()
        self.step("Inactive subscription offer created through UI and persisted with expected price/duration")
        self.stage = "edit only the new offer"
        # Search/clear button, edit, delete, and add FAB. Guard blocks all other IDs.
        icons.nth(1).click()
        expect(label(admin, "Modifier l'Abonnement")).to_be_visible()
        # Search input remains behind the modal; locate only modal textboxes.
        fields = admin.get_by_role("textbox")
        for index, value in ((-2, "4.5"), (-1, "2")):
            fields.nth(index).click()
            fields.nth(index).fill("")
            fields.nth(index).press_sequentially(value)
        with admin.expect_response(lambda r: r.request.method == "PUT" and urlsplit(r.url).path == f'/types-abonnement/{self.owned["offer"]}', timeout=60000) as updated:
            label(admin, "Valider").click()
        if updated.value.status != 200:
            raise AssertionError("Offer update rejected")
        self.assert_row("offer", prix=4.5, dureeMois=2, actif=False)
        self.step("New offer price and duration updated and verified in real backend")
        self.stage = "cancel offer deletion"
        icons.nth(2).click()
        expect(label(admin, "Confirmation")).to_be_visible()
        label(admin, "Annuler").click()
        self.assert_row("offer", prix=4.5)
        self.step("Cancel deletion preserves the new offer")
        self.stage = "delete only the new offer through UI"
        icons.nth(2).click()
        with admin.expect_response(lambda r: r.request.method == "DELETE" and urlsplit(r.url).path == f'/types-abonnement/{self.owned["offer"]}', timeout=60000) as deleted:
            label(admin, "Supprimer").click()
        if deleted.value.status not in (200, 204):
            raise AssertionError("Offer deletion rejected")
        expect(card_label).to_have_count(0)
        if self.owned_row("offer") is not None:
            raise AssertionError("Offer remains persisted")
        self.step("New offer deleted through UI and absent from UI/backend; no payment created")

    def guest_flow(self):
        guest = self.page("GUEST")
        self.stage = "guest payment access"
        label(guest, "Paiement").click()
        expect(label(guest, "Connexion requise")).to_be_visible()
        label(guest, "Annuler").click()
        expect(label(guest, "Accès rapide")).to_be_visible()
        if self.current["business_write_attempts"] or self.current.get("blocked_writes"):
            raise AssertionError("Guest flow attempted a write")
        self.step("Guest payment access requires login; cancel restores home without any write")

    def cleanup(self):
        for kind in RESOURCES:
            field = RESOURCES[kind][3]
            # Recover an interrupted create response only by this run's unique marker + owner.
            matches = [row for row in self.rows(kind) if row.get(field) == self.marker and str(row["id"]) not in self.baseline[kind]
                       and (kind == "offer" or row.get("userId") == self.accounts["USER"]["id"])]
            for row in matches:
                self.owned[kind] = row["id"]
                if not self.owned_row(kind):
                    raise RuntimeError("Cleanup ownership check failed")
                response = self.api.delete(RESOURCES[kind][2] + "/" + str(row["id"]), headers={"Authorization": "Bearer " + self.accounts["ADMIN"]["token"]}, max_redirects=0)
                if response.status not in (200, 204):
                    raise RuntimeError("Cleanup request failed")
            final = {str(row["id"]): row for row in self.rows(kind)}
            if any(row.get(field) == self.marker for row in final.values()):
                raise RuntimeError("Temporary record remains")
            if any(final.get(identifier) != row for identifier, row in self.baseline[kind].items()):
                raise RuntimeError("Pre-existing record changed during the test")
        self.current["temporary_records_removed"] = True
        self.current["existing_records_unchanged"] = True

    def case(self, identifier, title, action):
        self.marker = "QA-E2E-" + uuid.uuid4().hex[:12].upper()
        self.owned = {}
        self.baseline = {}
        self.current = dict(id=identifier, title=title, marker=self.marker, status="FAIL", steps=[], business_write_attempts=0)
        self.cases.append(self.current)
        print("RUN: " + identifier + " " + title, flush=True)
        try:
            self.stage = "snapshot existing catalogues"
            self.baseline = {kind: {str(row["id"]): row for row in self.rows(kind)} for kind in RESOURCES}
            action()
            self.current["status"] = "PASS"
        except Exception as error:
            self.current.update(failed_stage=self.stage, error_type=type(error).__name__)
            for hint in ("strict mode violation", "Not a checkbox or radio button", "did not change its state", "Target page, context or browser has been closed"):
                if hint.lower() in str(error).lower():
                    self.current["error_hint"] = hint
                    break
            # Record only predefined validation labels, never arbitrary DOM text.
            if self.contexts:
                try:
                    page = self.contexts[-1].pages[-1]
                    self.current["validation_labels_visible"] = {text: label(page, text, exact=False).first.is_visible()
                        for text in ("Déclarer", "VALIDER", "Choisissez une ligne", "Date requise", "Champ requis", "Sélectionner la ligne")}
                except Exception:
                    pass
            print(f"FAIL: {identifier} at {self.stage} ({type(error).__name__}); sensitive details omitted", flush=True)
        finally:
            for context in self.contexts:
                try:
                    context.unroute_all(behavior="ignoreErrors")
                    context.close()
                except Exception:
                    pass
            self.contexts = []
            try:
                if len(self.baseline) == len(RESOURCES):
                    self.cleanup()
                else:
                    self.current["cleanup_not_needed"] = True
            except Exception:
                self.current["status"] = "FAIL"
                self.current["cleanup_or_preservation_requires_attention"] = True
            print(identifier + ": " + self.current["status"], flush=True)


CASES = {
    "BIZ-001": ("Objet perdu: USER declaration, ADMIN disponible/recupere, USER follows state", lambda r: r.object_flow()),
    "BIZ-002": ("Objet trouve: USER declaration, ADMIN validates, USER follows state", lambda r: r.object_flow(found=True)),
    "BIZ-003": ("Reclamation: USER submits, ADMIN treats, USER sees updated status", lambda r: r.claim_flow()),
    "BIZ-004": ("Offre abonnement: create inactive, edit, cancel deletion, delete", lambda r: r.offer_flow()),
    "BIZ-005": ("Object mandatory fields: no backend write", lambda r: r.object_flow(validation=True)),
    "BIZ-006": ("Claim without line: no backend write", lambda r: r.claim_flow(validation=True)),
    "BIZ-007": ("Guest payment requires login and cancellation returns home", lambda r: r.guest_flow()),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=["all", *CASES], action="append")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.list:
        for identifier, (title, _) in CASES.items():
            print(identifier + ": " + title)
        return 0
    output = ROOT / "reports/playwright/business-e2e" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True, exist_ok=True)
    selected = args.case or ["all"]
    planned = [identifier for identifier in CASES if "all" in selected or identifier in selected]
    report = dict(backend=API, frontend=UI, kind="real-browser-business-e2e", payment_tested=False,
                  planned_cases=planned, cases=[])
    with sync_playwright() as playwright:
        runner = BusinessRun(playwright, not args.headless)
        runner._playwright = playwright
        if set(planned) <= {"BIZ-004", "BIZ-007"}:
            runner.required_roles = {"ADMIN"}
        try:
            runner.authenticate_accounts()
            response = runner.api.get("/lignes", max_redirects=0)
            lines = response.json()
            if response.status != 200 or not isinstance(lines, list) or not lines:
                raise RuntimeError("Existing line fixture missing")
            runner.line_ids = {str(row["id"]) for row in lines}
            runner.line_number = str(lines[0]["numero"])
            for identifier, (title, action) in CASES.items():
                if identifier in planned:
                    runner.case(identifier, title, lambda action=action: action(runner))
                    if runner.current.get("cleanup_or_preservation_requires_attention"):
                        break
        except Exception as error:
            report["prerequisite_error_type"] = type(error).__name__
            print("BLOCKED: prerequisites unavailable; details omitted", flush=True)
        finally:
            report["cases"] = runner.cases
            report["preflight"] = runner.preflight
            report["passed"] = sum(case["status"] == "PASS" for case in runner.cases)
            report["failed"] = sum(case["status"] != "PASS" for case in runner.cases)
            report["not_executed"] = [identifier for identifier in planned if identifier not in {case["id"] for case in runner.cases}]
            report["status"] = "PASS" if runner.cases and report["failed"] == 0 and not report["not_executed"] and "prerequisite_error_type" not in report else "FAIL"
            if not runner.cases and "prerequisite_error_type" in report:
                report["status"] = "BLOCKED"
            try:
                if runner.browser:
                    runner.browser.close()
                runner.api.dispose()
            except Exception:
                pass
            text = json.dumps(report, ensure_ascii=False, indent=2)
            (output / "summary.json").write_text(text, encoding="utf-8")
            (output / "report.html").write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><title>eBus Business E2E</title><h1>'
                + report["status"] + '</h1><pre>' + html.escape(text) + '</pre></html>', encoding="utf-8")
            print("Report: " + str(output / "report.html"), flush=True)
    return 0 if report["status"] == "PASS" else (2 if report["status"] == "BLOCKED" else 1)


if __name__ == "__main__":
    sys.exit(main())
