"""Twenty source-backed user journeys; no API mocks, production logins or payments."""
import re
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


@pytest.mark.smoke
def test_e2e_01_login_screen(app):
    app.visible('Connexion')
    app.visible('Email')
    app.visible('Mot de passe')
    app.visible('Se Connecter')


def test_e2e_02_password_is_masked(app):
    field = app.page.locator('input[type="password"]')
    field.fill('Synthetic4927')
    expect(field).to_have_attribute('type', 'password')


def test_e2e_03_open_registration(app):
    app.click("S'inscrire")
    app.visible('Nom*')
    app.visible('Prénom*')


def test_e2e_04_registration_rejects_empty_names(app):
    app.click("S'inscrire")
    app.click('Suivant')
    app.visible('Nom obligatoire')
    app.visible('Prénom obligatoire')


def test_e2e_05_registration_advances_after_names(app):
    app.click("S'inscrire")
    fields = app.page.get_by_role('textbox')
    fields.nth(0).fill('Synthetic')
    fields.nth(1).fill('QA')
    app.click('Suivant')
    app.visible('Précédent')


def test_e2e_06_registration_previous_preserves_names(app):
    app.click("S'inscrire")
    app.page.get_by_role('textbox').nth(0).fill('Synthetic')
    app.page.get_by_role('textbox').nth(1).fill('QA')
    app.click('Suivant')
    app.click('Précédent')
    # Flutter paints the retained controller text before hydrating the editing input.
    # Focus the actual editor before reading its DOM value (confirmed by screenshot).
    name = app.page.get_by_role('textbox').nth(0)
    name.click()
    expect(name).to_have_value('Synthetic')


def test_e2e_07_open_password_recovery(app):
    app.click('Mot de passe oublié ?')
    app.visible('Envoyer le code')
    app.visible('Retour à la connexion')


def test_e2e_08_return_from_recovery(app):
    app.click('Mot de passe oublié ?')
    app.click('Retour à la connexion')
    app.visible('Bienvenue sur eBus')


def test_e2e_09_admin_login_navigation(app):
    app.click('Accès administrateur')
    app.visible('Connexion Admin')
    expect(app.page.locator('input[type="password"]')).to_be_visible()


def test_e2e_10_registration_return_to_login(app):
    app.click("S'inscrire")
    app.click('Se connecter')
    app.visible('Bienvenue sur eBus')


def test_e2e_11_guest_home(app):
    app.guest()
    app.visible('Objets perdus')
    app.visible('Réclamations')


def test_e2e_12_guest_line_navigation(app):
    app.guest()
    app.click('Lignes')
    app.visible('Lignes de bus')


def test_e2e_13_guest_lost_objects_navigation(app):
    app.guest()
    app.click('Objets perdus')
    expect(app.page.get_by_role('textbox').first).to_be_visible()


def test_e2e_14_guest_claims_navigation(app):
    app.guest()
    app.click('Réclamations')
    app.visible('Réclamations')


def test_e2e_15_guest_payment_requires_login(app):
    app.guest()
    app.click('Paiement')
    app.visible('Connexion requise')


def test_e2e_16_guest_can_cancel_auth_dialog(app):
    app.guest()
    app.click('Paiement')
    app.click('Annuler')
    app.visible('Lignes')


@pytest.mark.auth
def test_e2e_17_user_login_reaches_home(app):
    app.login()
    app.visible('Lignes')
    app.visible('Objets perdus')


@pytest.mark.auth
def test_e2e_18_user_can_open_lines(app):
    app.login()
    app.click('Lignes')
    app.visible('Lignes de bus')


@pytest.mark.auth
def test_e2e_19_user_can_open_lost_objects(app):
    app.login()
    app.click('Objets perdus')
    expect(app.page.get_by_role('textbox').first).to_be_visible()


@pytest.mark.auth
def test_e2e_20_admin_login_reaches_admin_home(app):
    app.click('Accès administrateur')
    app.login('admin')
    expect(app.page.get_by_text(re.compile('Dossiers|Gestion des dossiers')).first).to_be_visible()
