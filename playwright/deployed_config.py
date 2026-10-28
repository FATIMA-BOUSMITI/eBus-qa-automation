"""Public target configuration and private credentials for local/Actions runs."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEPLOYED_FRONTEND = "https://ebus-frontend-1an4.onrender.com"
API = "https://ebus-backend-ao2u.onrender.com"
SECRET_NAMES = {
    "USER": ("EBUS_USER_EMAIL", "EBUS_USER_PASSWORD"),
    "ADMIN": ("EBUS_ADMIN_EMAIL", "EBUS_ADMIN_PASSWORD"),
}


def frontend_url():
    value = os.environ.get("EBUS_DEPLOYED_FRONTEND_URL", "http://127.0.0.1:17357").rstrip("/")
    parsed = urlsplit(value)
    if value not in (DEPLOYED_FRONTEND, "http://127.0.0.1:17357", "http://localhost:17357") or parsed.username or parsed.password:
        raise ValueError("Unsupported frontend target; use the known Render URL or local test server")
    if os.environ.get("CI") == "true" and value != DEPLOYED_FRONTEND:
        raise ValueError("Deployed CI must use the Render frontend URL")
    return value


def browser_channel():
    value = os.environ.get("EBUS_BROWSER_CHANNEL", "chrome")
    if value not in ("chrome", "chromium"):
        raise ValueError("Browser channel must be chrome or chromium")
    return None if value == "chromium" else "chrome"


def load_accounts(required_roles=None, credential_path=None):
    required_roles = required_roles or {"USER", "ADMIN"}
    if any(os.environ.get(name) for pair in SECRET_NAMES.values() for name in pair) or os.environ.get("CI") == "true":
        accounts = {}
        for role, (email_name, password_name) in SECRET_NAMES.items():
            email, password = os.environ.get(email_name), os.environ.get(password_name)
            if email and password:
                accounts[role] = {"email": email, "password": password}
            elif role in required_roles or email or password:
                raise ValueError("Missing GitHub Secrets: " + email_name + " / " + password_name)
        if not required_roles <= accounts.keys():
            raise ValueError("Required account secrets are missing")
        return accounts
    path = credential_path or ROOT / ".tools/mobile-credentials.json"
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    try:
        frontend_url()
        browser_channel()
        load_accounts()
    except Exception as error:
        # Configuration errors contain names only, never secret values.
        print("Configuration unavailable (" + type(error).__name__ + "); verify the four required secret names and target URL")
        raise SystemExit(2)
    print("Target and required credentials configured; secret values omitted")
