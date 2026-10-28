"""Synthetic local fixtures only. Never return/log JWTs or raw login responses."""
import json
import os
import time
from urllib.parse import urlparse
from robot.api.deco import keyword, library
from RequestsLibrary import RequestsLibrary
from JSONLibrary import JSONLibrary


@library(scope="TEST", auto_keywords=False)
class ApiLibrary:
    def __init__(self):
        self.http = RequestsLibrary()
        self.json = JSONLibrary()
        self.response = None

    @keyword
    def connect_to_local_api(self, identity="anonymous"):
        base = os.getenv("EBUS_API_URL", "http://host.docker.internal:18080")
        parsed = urlparse(base)
        if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "host.docker.internal"} or parsed.port != 18080:
            raise AssertionError("BLOCKED: only the dedicated local QA API on port 18080 is allowed")
        self.http.create_session("qa", base, timeout=10, debug=0)
        if identity != "anonymous":
            identities = {"user": "qa-user", "admin": "qa-admin", "pending": "qa-pending", "rejected": "qa-rejected"}
            if identity not in identities:
                raise AssertionError("Unknown synthetic identity")
            response = self.http.post_on_session("qa", "/users/login", json={"email": identities[identity] + "@example.invalid", "password": "LocalQa4927!"}, expected_status="any")
            if response.status_code != 200:
                raise AssertionError("BLOCKED: synthetic fixture login failed")
            token = response.json().get("token")
            if not token:
                raise AssertionError("BLOCKED: login returned no token")
            self.http.update_session("qa", headers={"Authorization": "Bearer " + token})

    @keyword
    def request_api(self, method, path, payload="", encoding="json"):
        kwargs = {"expected_status": "any", "allow_redirects": False}
        if payload:
            kwargs["data" if encoding == "form" else "json"] = json.loads(payload)
        elif encoding == "form":
            kwargs["data"] = {}
        self.response = getattr(self.http, method.lower() + "_on_session")("qa", path, **kwargs)

    @keyword
    def response_status_should_be(self, *statuses):
        expected = [int(s) for s in statuses]
        actual = self.response.status_code
        if actual not in expected:
            raise AssertionError(f"HTTP {actual}; expected one of {expected}")

    @keyword
    def response_should_be_array(self):
        body = self.response.json()
        self.json.get_value_from_json(body, "$")
        if not isinstance(body, list):
            raise AssertionError("Expected a JSON array")

    @keyword
    def response_field_should_be(self, field, expected):
        if str(self.response.json().get(field)) != str(expected):
            raise AssertionError(f"Unexpected value for {field}; response omitted")

    @keyword
    def response_text_should_be(self, expected):
        if self.response.text != expected:
            raise AssertionError("Unexpected response text; body omitted")

    @keyword
    def close_api_session(self):
        self.http.delete_all_sessions()
