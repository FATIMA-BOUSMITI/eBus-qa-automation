"""Configuration checks: no network, real secrets, browser or database required."""
import os
import unittest
from unittest.mock import patch

from deployed_config import DEPLOYED_FRONTEND, browser_channel, frontend_url, load_accounts


class DeployedConfiguration(unittest.TestCase):
    def test_ci_requires_deployed_frontend(self):
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            with self.assertRaises(ValueError):
                frontend_url()
        with patch.dict(os.environ, {"CI": "true", "EBUS_DEPLOYED_FRONTEND_URL": DEPLOYED_FRONTEND}, clear=True):
            self.assertEqual(frontend_url(), DEPLOYED_FRONTEND)

    def test_unknown_host_is_rejected_before_credentials(self):
        with patch.dict(os.environ, {"EBUS_DEPLOYED_FRONTEND_URL": "https://example.invalid"}, clear=True):
            with self.assertRaises(ValueError):
                frontend_url()

    def test_ci_does_not_fall_back_to_local_credential_file(self):
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            with self.assertRaises(ValueError):
                load_accounts(credential_path="must-not-be-read.json")

    def test_incomplete_pair_never_falls_back_to_file(self):
        with patch.dict(os.environ, {"EBUS_USER_EMAIL": "synthetic@example.invalid"}, clear=True):
            with self.assertRaises(ValueError):
                load_accounts()

    def test_environment_accounts_and_chromium(self):
        values = {"EBUS_USER_EMAIL": "user@example.invalid", "EBUS_USER_PASSWORD": "synthetic-user",
                  "EBUS_ADMIN_EMAIL": "admin@example.invalid", "EBUS_ADMIN_PASSWORD": "synthetic-admin",
                  "EBUS_BROWSER_CHANNEL": "chromium"}
        with patch.dict(os.environ, values, clear=True):
            self.assertEqual(set(load_accounts()), {"USER", "ADMIN"})
            self.assertIsNone(browser_channel())


if __name__ == "__main__":
    unittest.main()
