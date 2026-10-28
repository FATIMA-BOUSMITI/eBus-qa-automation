# Parcours métier Playwright avec comptes existants

Cette suite distincte utilise Chrome, le frontend web local `http://127.0.0.1:17357` et le vrai backend distant `https://ebus-backend-ao2u.onrender.com`. Les écritures UI atteignent réellement la base distante. Les réponses ne sont pas simulées et ne sont pas redirigées vers le backend QA local. Les comptes USER et ADMIN sont sélectionnés parmi les identifiants déjà fournis, dans `.tools/mobile-credentials.json` ignoré par Git.

| Cas | Parcours | Vérifications attendues |
| --- | --- | --- |
| BIZ-001 | USER déclare un objet perdu → ADMIN le rend disponible → ADMIN le marque récupéré | Enregistrement réel ; état initial EN_ATTENTE ; DISPONIBLE puis RECUPERE en base ; utilisateur retrouve Disponible puis Clôturé après rechargement |
| BIZ-002 | USER déclare un objet trouvé → ADMIN valide | Type TROUVE et état initial EN_ATTENTE persistés ; l'utilisateur voit ensuite Disponible |
| BIZ-003 | USER soumet une réclamation → ADMIN la traite | Réclamation persistée au bon propriétaire ; transition EN_ATTENTE → TRAITEE ; utilisateur voit Traitée sur la réclamation de test |
| BIZ-004 | ADMIN crée une offre d'abonnement inactive → modifie prix/durée → annule une suppression → supprime | Nom unique, prix et durée persistés ; annulation préserve l'offre ; suppression confirmée UI et backend |
| BIZ-005 | USER soumet un formulaire d'objet vide | Erreurs de champ et date obligatoires visibles ; aucune tentative d'écriture métier |
| BIZ-006 | USER soumet une réclamation sans ligne | Erreur de ligne obligatoire ; aucune tentative d'écriture métier |
| BIZ-007 | Invité ouvre Paiement puis annule la connexion | Connexion requise ; retour à l'accueil ; aucune écriture métier |

Les scénarios BIZ-001 à BIZ-004 sont des parcours métier avec persistance. Les trois autres sont des contrôles négatifs dans le navigateur. Les définir ou les compiler ne constitue pas un résultat E2E réussi : consulter les rapports d'exécution réels.

## Exécuter devant soi

Dans PowerShell, depuis la racine du projet :

```powershell
cd C:\Users\fatouma\Desktop\ebus
.\playwright\run-business-e2e.ps1 -List
.\playwright\run-business-e2e.ps1 -Case BIZ-001
```

Pour une réclamation ou une offre :

```powershell
.\playwright\run-business-e2e.ps1 -Case BIZ-003
.\playwright\run-business-e2e.ps1 -Case BIZ-004
```

Pour les sept scénarios :

```powershell
.\playwright\run-business-e2e.ps1
```

Pour ne reprendre que deux cas dans le terminal PowerShell :

```powershell
.\playwright\run-business-e2e.ps1 -Case BIZ-003,BIZ-004
```

Chrome est visible par défaut. Garder ses fenêtres ouvertes et laisser l'automatisation agir. Le mode `-Headless` est disponible. Le serveur frontend doit déjà répondre sur le port 17357. Si nécessaire, le démarrer dans un autre terminal :

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m http.server 17357 --bind 127.0.0.1 --directory C:\Users\fatouma\Downloads\eBus_front\eBus_front\eBus_front\build\web
```

Ce serveur sert le build web existant. Si le code Flutter est modifié, reconstruire le web pour prendre ces modifications en compte ; un `flutter run` sur un autre port ne remplace pas ce serveur.

## Données et paiement

Chaque cas crée son marqueur `QA-E2E-…`. Le garde-fou vérifie le marqueur, le propriétaire, la ligne sélectionnée et les identifiants retournés par les créations. Les écritures sur les identifiants préexistants, les utilisateurs, les lignes, Stripe et les paiements sont bloquées. Les scénarios d'objet/réclamation testent les transitions dans l'UI puis suppriment leurs données temporaires par une API de nettoyage limitée aux créations du cas. Ce nettoyage n'est pas présenté comme une suppression UI testée.

L'offre d'abonnement est créée inactive et sans identifiant de prix Stripe. La suite ne teste pas la souscription payante, la confirmation d'un paiement, l'activation d'un abonnement utilisateur ou un prélèvement. Ces parcours demandent un environnement Stripe TEST et des fixtures dédiées ; aucun faux paiement ni faux webhook n'est utilisé pour les déclarer réussis.

Avant et après chaque cas, les catalogues accessibles d'objets, réclamations et offres sont comparés. Un échec de nettoyage ou une modification d'un enregistrement initial arrête la suite. Les activités de connexion et les journaux du backend peuvent naturellement être ajoutés ; aucune suppression de journal n'est effectuée.

## Rapports

`reports/playwright/business-e2e/<horodatage>/report.html` et `summary.json` contiennent les étapes, les verdicts et les identifiants des créations, sans mots de passe, jetons ou profils. Captures, vidéos et traces de sessions réelles ne sont pas enregistrées. Les exceptions sont résumées par étape et type pour éviter d'afficher les données des requêtes.

Un résultat PASS n'est accepté qu'après assertions UI, vérifications backend et contrôle du nettoyage. Les essais échoués restent conservés. Les contrôles unitaires de protection des écritures, dans `playwright/safety_checks.py`, sont séparés des résultats E2E.

## Résultats vérifiés

Les sept scénarios ont un verdict réel **PASS après reprises ciblées**, sur le backend distant avec les comptes existants. Le passage initial complet a obtenu 5 PASS et 2 FAIL. Le traitement de réclamation a ensuite réussi ; l'offre a réussi après correction de l'attente du bouton Actif et après un délai de connexion Render dépassé pendant les prérequis. Les échecs précédents restent conservés. Il ne s'agit pas d'un seul passage global 7/7.

Le rapport consolidé `reports/playwright/business-e2e/consolidated/report.html` référence le dernier résultat complet de chaque cas et les rapports sources. La preuve exportée se trouve dans `docs/results/playwright-business-e2e.json`. Chaque cas réussi a confirmé le retrait de ses créations temporaires et l'intégrité des enregistrements initiaux dans les catalogues vérifiés. Aucun paiement réel n'a été exécuté. Sept contrôles unitaires des restrictions d'écriture ont également réussi ; ils ne sont pas comptés comme sept parcours E2E supplémentaires.
