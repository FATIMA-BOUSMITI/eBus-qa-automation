"""Existing-account Render checks; never emit credentials, tokens or response bodies."""
import json
import os
from pathlib import Path
import requests
from robot.api.deco import keyword, library

BASE = "https://ebus-backend-ao2u.onrender.com"
ROOT = Path(__file__).resolve().parents[2]


@library(scope="SUITE", auto_keywords=False)
class RemoteApi:
    def __init__(self):
        self.http = requests.Session()
        self.token = None
        self.user_id = None
        self.account_alias = None

    def fetch(self, method, path, authenticated=False, payload=None):
        if method != "GET" and not (method == "POST" and path == "/users/login"):
            raise AssertionError("Remote checks permit only reads and login")
        try:
            return self.http.request(method, BASE + path, json=payload,
                headers={"Authorization": "Bearer " + self.token} if authenticated else {},
                timeout=(10, 60), allow_redirects=False)
        except Exception:
            raise AssertionError("BLOCKED: remote transport unavailable; sensitive details omitted") from None

    @staticmethod
    def body(response):
        try:
            return response.json()
        except Exception:
            raise AssertionError("Invalid JSON response; body omitted") from None

    @keyword
    def open_remote_session(self):
        email = os.environ.get("EBUS_USER_EMAIL")
        password = os.environ.get("EBUS_USER_PASSWORD")
        if email or password or os.environ.get("CI") == "true":
            if not email or not password:
                raise AssertionError("Missing EBUS_USER_EMAIL / EBUS_USER_PASSWORD")
            accounts = {"USER": {"email": email, "password": password}}
        else:
            accounts = json.loads((ROOT / ".tools/mobile-credentials.json").read_text(encoding="utf-8-sig"))
        for alias, credential in accounts.items():
            response = self.fetch("POST", "/users/login", payload=credential)
            if response.status_code != 200:
                continue
            data = self.body(response)
            if data.get("user", {}).get("role") == "USER" and data.get("token"):
                self.token, self.user_id, self.account_alias = data["token"], data["user"]["id"], alias
                return
        raise AssertionError("BLOCKED: no existing USER account authenticated")

    @keyword
    def check_remote(self, name):
        checks = {
            "health": ("/api/health", False, "health"),
            "bus": ("/bus", False, "array"),
            "lines": ("/lignes", False, "array"),
            "tickets": ("/tickets", False, "array"),
            "anonymous-types": ("/types-abonnement", False, "array"),
            "profile": (f"/users/{self.user_id}", True, "owner"),
            "dossier": (f"/users/me/dossier?id={self.user_id}", True, "dossier"),
            "subscription": (f"/abonnements/user/{self.user_id}", True, "subscription"),
            "history": (f"/abonnements/user/{self.user_id}/historique", True, "array"),
            "cards": (f"/cards/user/{self.user_id}", True, "array"),
            "activities": (f"/activities/{self.user_id}", True, "array"),
            "authenticated-types": ("/types-abonnement", True, "array"),
        }
        path, auth, shape = checks[name]
        response = self.fetch("GET", path, auth)
        if shape == "subscription" and response.status_code == 204:
            return
        if response.status_code != 200:
            raise AssertionError(f"HTTP {response.status_code}; expected 200" + (" or 204" if shape == "subscription" else ""))
        if shape == "health":
            if response.text.strip() != "UP":
                raise AssertionError("Health response must be UP")
            return
        body = self.body(response)
        if shape == "array" and not isinstance(body, list):
            raise AssertionError("Expected JSON array")
        if shape == "owner" and (body.get("id") != self.user_id or "password" in body):
            raise AssertionError("Profile identity/privacy check failed; body omitted")
        if shape == "dossier" and body.get("statusDossier") not in ("VALIDE", "EN_ATTENTE", "REJETE"):
            raise AssertionError("Invalid dossier state")
        if shape == "subscription" and (body.get("userId") != self.user_id or body.get("status") not in ("ACTIF", "EXPIRE", "EN_ATTENTE", "ANNULE")):
            raise AssertionError("Subscription identity/state mismatch")

    @keyword
    def close_remote_session(self):
        self.http.close()
        self.token = None
