import re
from urllib.parse import urlsplit
from playwright.sync_api import expect


class EBusApp:
    """Verified source text; runtime selector inspection is required before acceptance."""
    def __init__(self, page):
        self.page = page

    def text(self, value):
        return self.page.get_by_text(value, exact=True)

    def click(self, value):
        self.text(value).last.click()

    def visible(self, value):
        expect(self.text(value).last).to_be_visible()

    def login(self, identity='user'):
        # Keyboard events reach Flutter's editing controller after focus hydration.
        email = self.page.get_by_role('textbox').nth(0)
        email.click()
        email.press_sequentially(f'qa-{identity}@example.invalid')
        password = self.page.locator('input[type="password"]')
        password.click()
        password.press_sequentially('LocalQa4927!')
        with self.page.expect_response(lambda response: urlsplit(response.url).path=='/users/login' and response.request.method=='POST', timeout=30000) as login:
            self.click('Connexion Admin' if identity=='admin' else 'Se Connecter')
        if login.value.status != 200:
            raise AssertionError(f'Login HTTP {login.value.status}; payload and response omitted')

    def guest(self):
        self.click("Continuer en tant qu'invité")
        self.visible('Lignes')
