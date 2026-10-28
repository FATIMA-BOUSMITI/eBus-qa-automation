"""Unit checks for write restrictions; these are not browser E2E results."""
import unittest
from business_e2e import BusinessRun


class WriteRestrictions(unittest.TestCase):
    def setUp(self):
        self.run = BusinessRun.__new__(BusinessRun)
        self.run.current = {"id": "BIZ-004"}
        self.run.marker = "QA-E2E-OWNED"
        self.run.owned = {}
        self.run.accounts = {"USER": {"id": 123}}
        self.run.line_ids = {"1"}
        self.run.object_type = "PERTE"
        self.run.baseline = {kind: {} for kind in ("object", "claim", "offer")}

    def test_payment_and_user_updates_are_blocked(self):
        for method, path in (("POST", "/abonnements/subscribe"), ("POST", "/abonnements/confirm"),
                             ("PATCH", "/users/123"), ("DELETE", "/users/123"), ("DELETE", "/lignes/1")):
            with self.subTest(path=path):
                self.assertFalse(self.run.permitted(method, path, {}, {}))

    def test_only_exact_inactive_offer_is_creatable(self):
        body = dict(nom=self.run.marker, actif=False, prix=3.5, dureeMois=1)
        self.assertTrue(self.run.permitted("POST", "/types-abonnement", body, {}))
        for patch in ({"nom": "existing"}, {"actif": True}, {"stripePriceId": "price_real"}, {"prix": 100}):
            with self.subTest(patch=patch):
                self.assertFalse(self.run.permitted("POST", "/types-abonnement", {**body, **patch}, {}))

    def test_existing_id_cannot_be_deleted_even_if_registered_as_owned(self):
        self.run.owned["offer"] = 7
        self.run.baseline["offer"]["7"] = {"id": 7, "nom": self.run.marker}
        self.assertFalse(self.run.permitted("DELETE", "/types-abonnement/7", None, {}))

    def test_owned_id_does_not_allow_another_id(self):
        self.run.owned["offer"] = 7
        self.assertFalse(self.run.permitted("DELETE", "/types-abonnement/8", None, {}))

    def test_negative_cases_never_allow_business_writes(self):
        body = dict(nom=self.run.marker, actif=False, prix=3.5, dureeMois=1)
        for identifier in ("BIZ-005", "BIZ-006", "BIZ-007"):
            self.run.current["id"] = identifier
            self.assertFalse(self.run.permitted("POST", "/types-abonnement", body, {}))

    def test_claim_create_requires_selected_owner_and_existing_line(self):
        self.run.current["id"] = "BIZ-003"
        body = dict(titre=self.run.marker, description=self.run.marker + " description", userId=123, ligneId=1)
        self.assertTrue(self.run.permitted("POST", "/reclamations/new", body, {}))
        self.assertFalse(self.run.permitted("POST", "/reclamations/new", {**body, "userId": 456}, {}))
        self.assertFalse(self.run.permitted("POST", "/reclamations/new", {**body, "ligneId": 456}, {}))

    def test_only_allowed_object_status_transitions(self):
        self.run.current["id"] = "BIZ-001"
        self.run.owned["object"] = 5
        self.run.rows = lambda kind: [{"id": 5, "nom": self.run.marker, "userId": 123}]
        self.assertTrue(self.run.permitted("PUT", "/api/objets/5/statut", None, {"statut": ["DISPONIBLE"]}))
        self.assertFalse(self.run.permitted("PUT", "/api/objets/5/statut", None, {"statut": ["INVALID"]}))
        self.assertFalse(self.run.permitted("PUT", "/api/objets/6/statut", None, {"statut": ["DISPONIBLE"]}))


if __name__ == "__main__":
    unittest.main()
