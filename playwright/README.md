# Tests navigateur et E2E — Playwright Python

Playwright pilote Chrome/Chromium et l'interface Flutter Web réelle. Les sélecteurs utilisent les textes et la sémantique Flutter observés. Trois ensembles distincts existent ; choisir leur environnement avant l'exécution.

| Ensemble | Interface | API | Données |
| --- | --- | --- | --- |
| `tests/test_journeys.py` : 20 parcours | Build Flutter servi localement | API QA locale `18080` | Fixtures synthétiques ; écritures métier bloquées |
| `line_lifecycle.py` : cycle d'une ligne | Front local `17357` | Render | ADMIN existant, ligne temporaire |
| `business_e2e.py` : 7 cas métier | Front local `17357` par défaut | Render | USER/ADMIN existants, créations temporaires |

## Installation et frontend local

Installer les dépendances via le [guide principal](../README.md#installation-native). Chrome doit être présent pour les commandes locales par défaut. Le frontend et le backend restent dans leurs dépôts source respectifs.

Depuis le dossier qui contient `pubspec.yaml` :

```powershell
cd C:\Users\fatouma\Downloads\eBus_front\eBus_front\eBus_front
flutter pub get
flutter build web --dart-define=API_BASE_URL=https://ebus-backend-ao2u.onrender.com
```

Pour les scripts E2E, servir ce build dans un terminal séparé :

```powershell
cd C:\Users\fatouma\Downloads\eBus_front\eBus_front\eBus_front\build\web
py -3 -m http.server 17357 --bind 127.0.0.1
```

Ouvrir `http://127.0.0.1:17357` et vérifier que l'application charge. Les scripts métier ne démarrent pas le serveur à votre place. Le lanceur des vingt parcours locaux peut, lui, démarrer le serveur du build configuré et redirige les appels du domaine API Render vers le backend QA local.

## Vingt parcours locaux, visibles

Depuis la racine QA, avec l'API locale et les fixtures prêtes :

```powershell
& .\qa\run-native.ps1 -Suite Playwright -PythonExe $pythonExe -PytestArgs @('--headed','--slowmo','1000')
```

Les parcours couvrent connexion, navigation, inscription partielle, récupération de mot de passe, mode invité, contrôles d'accès et consultation authentifiée. Ils ont donné **20/20 PASS**. Il ne s'agit pas de vingt transactions métier complètes. Les requêtes d'écriture métier et Firebase sont bloquées dans ce périmètre ; l'API locale fournit de vraies réponses, sans remplacement par de fausses données.

## Cycles métier sur la base distante

```powershell
& .\playwright\run-line-lifecycle.ps1 -PythonExe $pythonExe
& .\playwright\run-business-e2e.ps1 -PythonExe $pythonExe
# Un seul cas :
& .\playwright\run-business-e2e.ps1 -Case BIZ-001 -PythonExe $pythonExe
```

Le scénario ligne crée une ligne, vérifie sa présence, la supprime puis confirme sa disparition. Les sept autres cas couvrent objet perdu et évolution de son état par l'ADMIN, objet retrouvé, réclamation traitée, offre d'abonnement inactive et validations négatives. Les [scénarios détaillés](../docs/playwright-business-e2e.md) décrivent les actions et limites ; le [cycle ligne](../docs/playwright-line-e2e.md) documente ses garde-fous.

Les scripts nettoient uniquement les données qu'ils ont créées, identifiées par marqueurs et identifiants. Ils ne suppriment pas les lignes ou utilisateurs préexistants. Aucun achat Stripe réel n'est effectué. Un abonnement payé n'est donc pas validé de bout en bout par ces cas.

Les comptes restent dans `.tools/mobile-credentials.json`. Le script métier accepte également les quatre variables `EBUS_USER_EMAIL`, `EBUS_USER_PASSWORD`, `EBUS_ADMIN_EMAIL`, `EBUS_ADMIN_PASSWORD`. Le scénario ligne conserve sa lecture du fichier privé local.

## Préparation du frontend déployé pour la future CI

`deployed_config.py` permet au script métier de choisir le frontend Render avec `EBUS_DEPLOYED_FRONTEND_URL=https://ebus-frontend-1an4.onrender.com` et le navigateur embarqué avec `EBUS_BROWSER_CHANNEL=chromium`. En CI, les quatre variables de compte remplacent obligatoirement le fichier privé. Le lanceur PowerShell métier vérifie encore le frontend local : pour une future CI distante, appeler directement le script Python après installation de Chromium.

Cette configuration est préparée ; une exécution GitHub sur le frontend déployé reste à valider. Les sept succès métier conservés concernent le **frontend local relié à l'API distante**, après reprises ciblées, pas une validation de la dernière version Web déployée.

## Alternative Docker pour les vingt parcours locaux

L'image `ebus-qa-automation:local` fournit Chromium et les dépendances Python. Après préparation de l'API QA et du build Flutter, utiliser `& .\qa\run-suites.ps1 -Suite Playwright -FrontendBuildPath 'CHEMIN_DU_BUILD_WEB'`. Le [guide Docker](../docs/docker.md) détaille la construction des images et les services nécessaires. Le navigateur s'exécute sans fenêtre dans le conteneur ; l'exécution visible reste disponible en mode natif.

## Rapports et diagnostic

Les rapports sont générés sous `reports/playwright/` : bilan, captures, traces selon la suite et résultats Allure pour pytest. La génération d'un rapport HTML Allure exige son CLI. Les traces peuvent contenir des données de session ; les garder privées. Les preuves résumées et expurgées sont dans [docs/results](../docs/results).

En cas de page vide, vérifier d'abord l'URL du frontend, le port et le build servi. En cas d'absence de données, vérifier ensuite la cible API et la connexion du compte. Un démarrage lent de Render n'est pas une preuve de mauvais identifiants.
