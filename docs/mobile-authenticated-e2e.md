# Parcours Appium avec comptes existants

La suite `appium/tests/authenticated.robot` utilise les trois comptes déjà fournis, chargés depuis `.tools/mobile-credentials.json` (ignoré par Git). Les mots de passe sont lus dans le mot-clé Python et ne sont pas des arguments Robot. Les captures et dumps UI sont désactivés pour ces sessions authentifiées. Ne pas activer les logs Appium de niveau debug : les commandes de saisie peuvent contenir des secrets.

| Cas | Compte | Parcours et assertions |
| --- | --- | --- |
| E2E-AUTH-001 | ACCOUNT1 | Connexion via formulaire réel → accueil authentifié → Profil → adresse du compte sélectionné affichée → déconnexion → écran Bienvenue |
| E2E-AUTH-002 | ACCOUNT2 | Même parcours complet avec le deuxième compte existant |
| E2E-AUTH-003 | ACCOUNT3 | Même parcours complet avec le troisième compte existant |

Le profil et la déconnexion sont accessibles aux utilisateurs et administrateurs. Aucun rôle particulier n'est supposé pour les trois comptes. L'apparition de l'accueil seule ne suffit pas : le profil doit aussi afficher l'adresse attendue. Les tests ne créent ni ne modifient de données métier, ne paient rien et ne suppriment aucun utilisateur ni aucune ligne.

## Exécution visible sur le Redmi

Garder le téléphone déverrouillé sur eBus Render sans ouvrir les notifications. Le serveur Appium local doit être prêt sur le port 4723. Vérifier le port courant avec `adb devices`, puis :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\appium\run.ps1 -RemoteInstalled -Authenticated -Serial 100.95.192.171:45565
```

Si le port Wi-Fi change, remplacer la valeur de `-Serial`. Rapports réels : `reports/appium/<horodatage>/report.html`. Les actions se voient directement sur le téléphone.

Validation des définitions uniquement, sans téléphone ni connexion :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\appium\run.ps1 -Authenticated -DryRun
```

Une validation statique ne prouve pas que les comptes sont acceptés. En cas d'échec avant déconnexion, la session peut rester ouverte : revenir manuellement à l'écran de connexion avant une nouvelle exécution. Aucune réinitialisation des données n'est effectuée.

## Résultat réel vérifié

Exécution sur le Redmi physique, avec eBus Render et le backend distant : **3 tests réussis, 0 échec**, en une seule exécution. Chaque compte a terminé connexion, vérification du profil et déconnexion. Rapport : `reports/appium/20261027-113942/report.html` ; preuve Robot : `reports/appium/20261027-113942/output.xml`. Aucun utilisateur ni aucune ligne supprimé par les scénarios. Ce résultat couvre ces trois sessions authentifiées, pas les achats ou les opérations de gestion.
