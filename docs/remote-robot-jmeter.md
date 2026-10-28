# Robot Framework et JMeter sur Render

Exécution explicite et bornée avec les comptes existants, sur `https://ebus-backend-ao2u.onrender.com`. Docker et le backend local ne sont pas requis. Les vingt cas Robot locaux et les profils de charge locaux restent séparés.

```powershell
cd C:\Users\fatouma\Desktop\ebus
.\qa\run-remote-suites.ps1
# Ou indépendamment :
.\qa\run-remote-suites.ps1 -Suite Robot
.\qa\run-remote-suites.ps1 -Suite JMeter
```

Les identifiants sont lus dans `.tools/mobile-credentials.json`, ignoré par Git. Le compte USER est identifié par une connexion réelle ; son identifiant est extrait de la réponse. Aucun identifiant de fixture locale n'est utilisé. Seuls des GET et la connexion POST `/users/login` sont exécutés : aucune suppression, aucun achat et aucune confirmation de paiement.

## Robot Framework

Douze contrôles : santé, catalogues bus/lignes/tickets, types d'abonnement anonymes, profil propre au compte, dossier, abonnement courant (200 ou 204 si absent), historique, cartes, activités et types d'abonnement authentifiés. Les réponses JSON sont contrôlées, ainsi que l'identité du profil et de l'abonnement.

Exécution réelle `remote-20261027-202031` : **11 PASS, 1 FAIL, 0 SKIP**. Le cas REM-005 attend un catalogue anonyme et reçoit HTTP 500 sur `/types-abonnement`. Le cas authentifié REM-012 réussit. Ce défaut n'est pas transformé en succès. Rapport : `reports/robot/remote-20261027-202031/report.html`.

## JMeter

Le plan distant est dérivé séparément du smoke local : HTTPS/443 et hôte Render fixes, un utilisateur, une itération, sept requêtes, pause de 1 seconde entre requêtes, arrêt du thread à la première erreur. Les propriétés `threads`/`duration` des profils locaux ne servent pas à augmenter ce plan. La session utilise uniquement son propre abonnement et son historique.

Les sept mesures HTTP sont santé, bus, lignes, tickets, connexion du compte existant, abonnement courant et historique. Le test accepte 204 pour un abonnement absent. La préparation authentifie le compte avant la mesure ; les requêtes Robot et cette préparation ne font pas partie des sept échantillons JMeter. Aucun corps, mot de passe, jeton ou en-tête d'autorisation n'est enregistré dans le JTL.

Exécution réelle `remote-20261027-202031` : **7 échantillons, 0 erreur**, moyenne **638,57 ms**, minimum 238 ms, maximum 1 616 ms. La fenêtre mesurée est de 13,44 secondes et inclut les pauses. Le débit observé de 0,521 requête/s est donc celui d'un test volontairement espacé. Sept requêtes hétérogènes fournissent une mesure indicative et ne permettent pas de conclure sur la capacité, un SLA ou l'endurance.

Dashboard : `reports/jmeter/remote-20261027-202031/dashboard/index.html`. Données : `samples.jtl`, statistiques : `summary.json`, plan effectif : `remote-smoke.jmx` dans le même dossier.

Le script retourne un statut non nul si l'une des suites échoue. Ici, Robot explique le statut global non nul ; le smoke JMeter est réussi. Les rapports locaux et historiques sont conservés. Un contrôle des artefacts principaux n'a détecté aucun identifiant fourni, mot de passe fourni ou JWT.
