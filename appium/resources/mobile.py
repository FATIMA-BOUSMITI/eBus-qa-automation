"""Real UiAutomator2 adapter. Source-backed selectors await Android validation."""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from robot.api.deco import keyword, library


@library(scope="SUITE", auto_keywords=False)
class Mobile:
    def __init__(self):
        self.driver = None
        self.package = "com.example.smart_bus"
        self.api_url = None
        self.sensitive_session = os.environ.get("MOBILE_AUTHENTICATED") == "1"
        self.account_email = None

    @keyword
    def open_mobile(self):
        from appium import webdriver
        from appium.options.android import UiAutomator2Options
        manifest = Path(os.environ["MOBILE_BUILD_MANIFEST"])
        build = json.loads(manifest.read_text(encoding="utf-8-sig"))
        apk = Path(build["apk"])
        remote = os.environ.get("MOBILE_TARGET") == "render-readonly"
        expected = "https://ebus-backend-ao2u.onrender.com" if remote else "http://127.0.0.1:18080"
        if build["api_url"] != expected:
            raise AssertionError("APK backend does not match the explicitly selected test target")
        self.api_url = expected
        self.package = build.get("package", "com.example.smart_bus")
        if remote and self.package != "com.example.smart_bus.render":
            raise AssertionError("Remote UI tests require the isolated eBus Render application")
        if hashlib.sha256(apk.read_bytes()).hexdigest().lower() != build["sha256"].lower():
            raise AssertionError("APK differs from the recorded QA build; rebuild it")
        server = os.environ.get("APPIUM_URL", "http://127.0.0.1:4723")
        if urlsplit(server).hostname not in ("127.0.0.1", "localhost"):
            raise AssertionError("Use a local Appium server")
        options = UiAutomator2Options().load_capabilities({
            "platformName": "Android", "appium:automationName": "UiAutomator2",
            "appium:udid": os.environ["ANDROID_SERIAL"],
            "appium:deviceName": "eBus QA Android", "appium:app": str(apk),
            "appium:appPackage": self.package,
            "appium:appActivity": "com.example.smart_bus.MainActivity",
            "appium:appWaitActivity": "com.example.smart_bus.MainActivity",
            "appium:noReset": True, "appium:fullReset": False,
            "appium:forceAppLaunch": True,
            "appium:newCommandTimeout": 120,
            "appium:adbExecTimeout": 60000,
            "appium:appWaitDuration": 120000,
            "appium:settings[enableMultiWindows]": False,
            "appium:settings[waitForIdleTimeout]": 0,
        })
        self.driver = webdriver.Remote(server, options=options)
        self._text("Bienvenue sur eBus", timeout=90)

    @keyword
    def close_mobile(self):
        if self.driver:
            try:
                # Restart only the process between cases; never clear storage.
                self.driver.terminate_app(self.package)
            finally:
                self.driver.quit()
                self.driver = None

    def _ensure_foreground(self):
        if self.driver.current_package != self.package:
            raise AssertionError("Keep eBus Render in the foreground while Appium controls the phone")

    def _text(self, text, timeout=20):
        from selenium.common.exceptions import StaleElementReferenceException
        from selenium.webdriver.support.ui import WebDriverWait
        # Flutter semantics may expose content-desc, text, or a merged label.
        quoted = json.dumps(text, ensure_ascii=False)
        selector = (f'new UiSelector().text({quoted})',
                    f'new UiSelector().description({quoted})',
                    f'new UiSelector().descriptionContains({quoted})')
        def locate(driver):
            for value in selector:
                matches = driver.find_elements("-android uiautomator", value)
                for item in matches:
                    if item.is_displayed():
                        return item
            return False
        return WebDriverWait(self.driver, timeout, ignored_exceptions=(StaleElementReferenceException,)).until(locate,
            message=f"Android semantics missing/element not visible: {text}")

    @keyword
    def mobile_text_should_be_visible(self, text):
        self._text(text)

    @keyword
    def tap_mobile_text(self, text):
        self._ensure_foreground()
        from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
        # A bounded native scroll handles small Android viewports.
        try:
            item = self._text(text)
        except TimeoutException:
            quoted = json.dumps(text, ensure_ascii=False)
            self.driver.find_element("-android uiautomator",
                'new UiScrollable(new UiSelector().scrollable(true)).setMaxSearchSwipes(3)'
                f'.scrollIntoView(new UiSelector().descriptionContains({quoted}))')
            item = self._text(text)
        self._ensure_foreground()
        if item.get_attribute("package") != self.package:
            raise AssertionError("An Android overlay covers eBus; restore the application before testing")
        try:
            item.click()
        except StaleElementReferenceException:
            # A Flutter rebuild invalidated the node before the click executed.
            self._text(text).click()

    def _field(self, index):
        from selenium.webdriver.support.ui import WebDriverWait
        def locate(driver):
            fields = driver.find_elements("class name", "android.widget.EditText")
            return fields[int(index)] if len(fields) > int(index) else False
        return WebDriverWait(self.driver, 15).until(locate,
            message=f"Editable Android field {index} unavailable")

    @keyword
    def enter_mobile_field(self, index, value):
        self._ensure_foreground()
        field = self._field(index)
        if field.get_attribute("package") != self.package:
            raise AssertionError("Cannot enter test text outside the eBus application")
        field.click()
        field.clear()
        field.send_keys(value)
        self._hide_keyboard()

    def _hide_keyboard(self):
        self._ensure_foreground()
        from selenium.common.exceptions import WebDriverException
        from selenium.webdriver.support.ui import WebDriverWait
        for attempt in range(2):
            if not self.driver.is_keyboard_shown():
                return
            try:
                self.driver.hide_keyboard()
                break
            except WebDriverException as error:
                # Appium snapshots canCloseKeyboard before the opening animation
                # ends. Retry once to refresh that state; keep all other failures.
                if "keyboard cannot be hidden" not in str(error).lower() or attempt == 1:
                    raise
        WebDriverWait(self.driver, 5).until(lambda driver: not driver.is_keyboard_shown(),
                                          message="Android software keyboard remains visible")

    @keyword
    def mobile_field_should_equal(self, index, expected):
        self._ensure_foreground()
        field = self._field(index)
        if field.get_attribute("package") != self.package:
            raise AssertionError("An Android overlay covers the expected eBus field")
        field.click()
        if field.text != expected:
            raise AssertionError("Field value was not preserved")
        self._hide_keyboard()

    @keyword
    def mobile_password_should_be_masked(self):
        if str(self._field(1).get_attribute("password")).lower() != "true":
            raise AssertionError("Android password field must be masked")

    @keyword
    def mobile_back(self):
        self._ensure_foreground()
        self.driver.back()

    @keyword
    def mobile_lines_should_match_api(self):
        from urllib.request import urlopen
        # Read only the public catalogue; never send credentials or mutate rows.
        with urlopen(self.api_url + "/lignes", timeout=45) as response:
            if response.status != 200:
                raise AssertionError("Public lines API did not return HTTP 200")
            rows = json.load(response)
        if isinstance(rows, dict):
            rows = next((rows[key] for key in ("lignes", "data", "content", "items", "results")
                         if isinstance(rows.get(key), list)), [])
        if not isinstance(rows, list):
            raise AssertionError("Unexpected public lines response shape")
        numbers = [str(row["numero"]) for row in rows if isinstance(row, dict) and "numero" in row]
        if not numbers:
            raise AssertionError("No line returned by the selected backend")
        # The actual Flutter view sorts numeric line numbers, invalid numbers first.
        first = sorted(numbers, key=lambda value: int(value) if value.lstrip("+-").isdigit() else 0)[0]
        self._text("Ligne " + first, timeout=60)

    @keyword
    def mobile_failure_evidence(self):
        from robot.libraries.BuiltIn import BuiltIn
        if self.sensitive_session:
            BuiltIn().log("Authenticated session: screenshots and UI dumps omitted to protect account data")
            return
        if not self.driver or BuiltIn().get_variable_value("${TEST STATUS}") != "FAIL":
            return
        # No real credentials are entered by this suite. Artifacts remain ignored.
        name = BuiltIn().get_variable_value("${TEST NAME}").split()[0]
        out = Path(BuiltIn().get_variable_value("${OUTPUT DIR}"))
        try:
            import xml.etree.ElementTree as ET
            source = self.driver.page_source
            if not any(node.get("package") == self.package for node in ET.fromstring(source).iter()):
                BuiltIn().log("eBus is covered by another Android window; unrelated screen capture omitted", "WARN")
                return
            self.driver.save_screenshot(str(out / f"{name}.png"))
            (out / f"{name}.xml").write_text(source, encoding="utf-8")
        except Exception:
            BuiltIn().log("Could not capture Android failure evidence", "WARN")

    @keyword
    def login_existing_mobile_account(self, account):
        """Read secrets internally: Robot receives only an account alias."""
        self.sensitive_session = True
        from selenium.webdriver.support.ui import WebDriverWait
        prefix = "EBUS_" + account.upper()
        email = os.environ.get(prefix + "_EMAIL")
        password = os.environ.get(prefix + "_PASSWORD")
        if not email or not password:
            raise AssertionError(f"Missing credentials for {account}; load the ignored credentials file")
        try:
            self.enter_mobile_field(0, email)
            self.enter_mobile_field(1, password)
            self.tap_mobile_text("Se Connecter")
            def authenticated(driver):
                for label in ("Accès rapide", "Gestion rapide"):
                    quoted = json.dumps(label, ensure_ascii=False)
                    if driver.find_elements("-android uiautomator",
                            f'new UiSelector().descriptionContains({quoted})'):
                        return True
                    if driver.find_elements("-android uiautomator",
                            f'new UiSelector().text({quoted})'):
                        return True
                return False
            WebDriverWait(self.driver, 90).until(authenticated)
            self.account_email = email
        except Exception:
            # Selenium errors may contain typed values: expose a sanitized failure.
            raise AssertionError(f"Authentication journey failed for {account}; no credentials recorded") from None

    @keyword
    def mobile_profile_should_match_account(self):
        try:
            self.tap_mobile_text("Profil")
            self._text(self.account_email, timeout=30)
        except Exception:
            raise AssertionError("Authenticated profile does not display the selected account email") from None

    @keyword
    def logout_mobile_account(self):
        self.tap_mobile_text("Se déconnecter")
        self._text("Bienvenue sur eBus", timeout=30)
        self.account_email = None
