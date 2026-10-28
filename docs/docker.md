# Exécuter les tests avec Docker

Docker est une alternative aux outils natifs. Les fichiers existants permettent de démarrer une API QA et PostgreSQL isolés, puis d'exécuter Robot Framework, Playwright et JMeter dans des conteneurs. Les commandes ci-dessous sont prévues pour PowerShell et Docker Desktop avec des conteneurs Linux.

## Construire les deux images de test

Depuis la racine du dépôt QA :

```powershell
docker version
docker compose version
docker build -f qa/Dockerfile.automation -t ebus-qa-automation:local .
docker build -f jmeter/Dockerfile -t ebus-qa-jmeter:local .
```

`ebus-qa-automation:local` contient Python, Robot Framework, pytest, Playwright et Chromium. `ebus-qa-jmeter:local` contient Java et JMeter 5.6.3. **Ce sont des images d'outils de test**, distinctes des futures images applicatives frontend/backend. Leur construction ne lance aucune suite. Le `.dockerignore` exclut les outils privés, les rapports et les fichiers locaux de secrets du contexte de build.

## Démarrer une API et une base QA locales

Le clone indépendant `eBus_backend` doit être disponible au chemin indiqué. Maven et Java 17 sont nécessaires sur le poste pour produire le JAR utilisé par Compose :

```powershell
mvn.cmd -f .\eBus_backend\pom.xml -DskipTests package
docker compose -f qa/compose.yaml up -d postgres backend
docker compose -f qa/compose.yaml ps
```

Compose monte le JAR, configure une base `ebus_qa` dédiée et expose l'API sur `http://127.0.0.1:18080`. Les mots de passe présents dans cette configuration sont synthétiques et réservés à QA ; aucun secret Render n'est nécessaire. Le service utilise des clés mail/Stripe factices.

Attendre que `http://127.0.0.1:18080/api/health` réponde et que le backend ait créé ses tables. Sur une **nouvelle base QA vide uniquement**, charger les fixtures :

```powershell
docker compose -f qa/compose.yaml exec -T postgres psql -U ebus_qa -d ebus_qa -f /qa/seed.sql
```

Le script refuse une base contenant déjà des utilisateurs. Ne pas contourner ce contrôle et ne jamais le diriger vers Render. Les volumes persistent après un arrêt : ne pas réimporter les fixtures à chaque lancement.

## Robot Framework

```powershell
& .\qa\run-suites.ps1 -Suite Robot
```

Les vingt cas locaux utilisent l'API QA via `host.docker.internal:18080`, les comptes synthétiques et les fixtures. Les rapports sont écrits sur le poste dans `reports/robot/`. Cette commande ne lance pas la suite distante Render.

## Playwright

Préparer un build Flutter Web contenant l'origine API Render attendue, comme décrit dans le [guide Playwright](../playwright/README.md). Le lanceur sert ce build depuis un conteneur nommé `ebus-qa-ui`, puis exécute les vingt parcours locaux dans Chromium sans interface graphique :

```powershell
& .\qa\run-suites.ps1 -Suite Playwright -FrontendBuildPath 'C:\Users\fatouma\Downloads\eBus_front\eBus_front\eBus_front\build\web'
```

Les requêtes API du build sont redirigées vers le backend QA local réel ; les écritures métier restent bloquées. Les rapports, captures et traces sont enregistrés dans `reports/playwright/`. Pour voir les actions dans une fenêtre Chrome sur le poste, utiliser plutôt le lanceur natif avec `--headed`. Les scripts métier distants et Appium conservent leurs procédures séparées.

## JMeter

```powershell
& .\qa\run-suites.ps1 -Suite JMeter
```

Le smoke local utilise `ebus-qa-jmeter:local` et l'API QA sur le port `18080`. Il vérifie sept échantillons et produit `reports/jmeter/smoke-<date>/dashboard/index.html`. Il ne lance pas de charge sur Render. Pour le smoke distant limité, suivre le [guide JMeter](../jmeter/README.md).

## Arrêter sans effacer les données

```powershell
docker compose -f qa/compose.yaml stop
# Si le serveur Flutter Docker a été démarré :
docker stop ebus-qa-ui
```

Ces commandes conservent les volumes QA. Si les ports `18080` ou `17357` sont déjà utilisés par des serveurs natifs, arrêter ceux-ci avant de démarrer les services Docker correspondants.

## GitHub Actions et validation

Le futur pipeline pourra construire ces images et choisir des tests natifs ou conteneurisés. Les images applicatives frontend/backend demandent leurs propres sources et contextes de build. Sur un runner Linux, `host.docker.internal` exige une adaptation réseau ; les lanceurs Windows présentés ici ne constituent donc pas encore un workflow CI portable.

Les secrets réels doivent venir de GitHub Secrets et être injectés à l'exécution, jamais intégrés dans une image. La documentation et la configuration Compose ont été vérifiées ; cette mise à jour ne revendique aucune nouvelle construction d'image ni exécution fonctionnelle dans Docker.
