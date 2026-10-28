# eBus — QA Automation Portfolio

Suite professionnelle d'assurance qualité automatisée pour **eBus**, une application de gestion du transport public composée d'un frontend Flutter et d'une API Java / Spring Boot. Ce dépôt rassemble les tests de parcours web, API, mobile et performance, ainsi que leur documentation technique.

> Les résultats publiés sont des preuves d'exécutions datées. Ils ne sont jamais présentés comme une garantie de l'état courant de l'environnement déployé.

## Produits testés

| Composant | Technologies | Dépôt | Environnement déployé |
| --- | --- | --- | --- |
| Backend | Java 17, Spring Boot, PostgreSQL, JWT, Stripe | [eBus_backend](https://github.com/ikraammel/eBus_backend) | [API Render](https://ebus-backend-ao2u.onrender.com) |
| Frontend | Flutter Web / Android | [eBus_frontend](https://github.com/ikraammel/eBus_frontend) | [Web Render](https://ebus-frontend-1an4.onrender.com/) |
| Qualité | Playwright, Robot Framework, Appium, JMeter | Ce dépôt | Voir la stratégie ci-dessous |

## Objectifs QA

- Valider les API, les rôles USER / ADMIN et les règles métier critiques.
- Couvrir les parcours E2E : objets perdus et trouvés, réclamations, lignes et abonnements.
- Exécuter des contrôles de performance non destructifs.
- Produire des rapports exploitables et préserver les anomalies connues.
- Protéger les données existantes : les données créées par un test sont identifiées et nettoyées par le scénario lorsque cela est possible.

## Structure

```text
eBus-qa-automation/
├── playwright/        # Tests E2E Web et parcours métier
├── robot-framework/   # Tests API Robot Framework
├── jmeter/            # Smoke, charge progressive et endurance
├── appium/            # Tests Android locaux avec Robot / Appium
├── docs/              # Plan, stratégie, cas de test, résultats et architecture
├── README.md
└── .gitignore
```

## Stratégie d'exécution

| Catégorie | Outil | Exécution | Finalité |
| --- | --- | --- | --- |
| Tests unitaires et intégration backend | JUnit, MockMvc, JaCoCo | CI du dépôt backend | Fiabilité du code Java |
| Tests API | Robot Framework | CI du dépôt QA | Contrats API et authentification |
| Tests Web E2E | Playwright | CI du dépôt QA | Parcours utilisateur / administrateur |
| Performance smoke | JMeter | CI du dépôt QA | Régression de performance limitée |
| Charge progressive | JMeter | Local uniquement | Caractérisation de la montée en charge |
| Endurance | JMeter | Local uniquement | Stabilité dans la durée |
| Tests Android | Appium + Robot Framework | **Local uniquement** | Validation sur émulateur ou téléphone réel |

**Appium ne doit jamais être ajouté à GitHub Actions.** Il nécessite un appareil Android réel ou un émulateur et reste volontairement hors CI/CD.

## Prérequis locaux

- Java 17+ pour JMeter.
- Python 3.11+ pour Robot Framework et les scripts Playwright.
- Google Chrome / Chromium pour les tests web.
- Node.js 20+ lorsque les dépendances JavaScript sont requises.
- Android SDK, ADB et Appium uniquement pour les tests mobiles.

Créer un environnement Python isolé :

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\playwright\requirements.txt
python -m pip install -r .\robot-framework\requirements.txt
python -m playwright install chromium
```

## Configuration sécurisée

Les identifiants ne sont jamais versionnés. Configurez les comptes de test uniquement dans les variables d'environnement locales ou les GitHub Actions Secrets :

```text
EBUS_USER_EMAIL
EBUS_USER_PASSWORD
EBUS_ADMIN_EMAIL
EBUS_ADMIN_PASSWORD
EBUS_DEPLOYED_FRONTEND_URL
EBUS_DEPLOYED_BACKEND_URL
```

Ne placez jamais dans ce dépôt : clé Stripe, secret JWT, URL PostgreSQL, mot de passe de base de données, rapport contenant des données personnelles, ni fichier `.env` réel.

## Lancer les suites

### Robot Framework — API

```powershell
robot --outputdir reports\robot robot-framework\tests
```

Consulter [robot-framework/README.md](robot-framework/README.md) avant une exécution sur l'environnement distant.

### Playwright — Web E2E

```powershell
python playwright\business_e2e.py --case all --headless
```

Les scénarios E2E qui créent des données métier utilisent des marqueurs de test et préservent les données préexistantes. Voir [playwright/README.md](playwright/README.md).

### JMeter — performance

```powershell
.\jmeter\run-smoke.ps1
```

Les plans `progressive.jmx` et `endurance.jmx` sont réservés à une exécution locale contrôlée. Voir [jmeter/README.md](jmeter/README.md).

### Appium — Android local uniquement

```powershell
.\appium\run.ps1 -RemoteInstalled -Authenticated -Serial '<ADB_SERIAL>'
```

Voir [appium/README.md](appium/README.md) pour la connexion ADB Wi-Fi, les capacités Android et les rapports Robot Framework.

## Couverture métier

Les suites couvrent notamment :

- authentification et séparation des rôles USER / ADMIN ;
- catalogue des lignes et cycle de vie d'une ligne ;
- déclaration et suivi d'objets perdus ou trouvés ;
- création, traitement et suivi d'une réclamation ;
- validation des champs obligatoires et absence d'écriture lors d'une erreur client ;
- accès invité et paiement nécessitant une authentification ;
- gestion d'offres d'abonnement ;
- vérifications API, santé, profil, cartes, historique et activités.

## Résultats observés

Les derniers résultats analysés doivent être lus avec leurs rapports associés :

| Suite | Résultat observé | Interprétation |
| --- | --- | --- |
| Playwright métier BIZ-001 à BIZ-007 | 4 PASS / 3 FAIL | BIZ-003, BIZ-005, BIZ-006 et BIZ-007 ont réussi. BIZ-001, BIZ-002 et BIZ-004 échouent à la création UI ; anomalies conservées pour correction. |
| Robot Framework API distant | 11 PASS / 1 FAIL | L'endpoint anonyme des types d'abonnement renvoie HTTP 500 ; anomalie à suivre. |
| JMeter smoke distant | 7 échantillons / 0 erreur | Indicateur smoke uniquement ; ce n'est pas une preuve de capacité en charge. |
| Appium Android | Exécutions locales documentées | Hors CI/CD ; résultats à rattacher au rapport local correspondant. |

Les rapports générés sont volontairement ignorés par Git. Les synthèses non sensibles et les anomalies sont documentées dans `docs/`.

## CI/CD

Le dépôt QA est prévu pour exécuter Robot Framework API, Playwright Web et JMeter Smoke via GitHub Actions. La configuration CI doit utiliser exclusivement des secrets GitHub et cibler les versions déployées du frontend et du backend.

Flux cible :

```text
Push backend ou frontend
        │
        ├── CI propre au dépôt applicatif : build, tests unitaires, déploiement
        │
        └── Déclenchement QA après déploiement réussi
                 │
                 ├── Robot Framework API
                 ├── Playwright Web E2E
                 └── JMeter Smoke

Appium Android : exécution locale uniquement
```



## Documentation

- [Plan de test](docs/test-plan.md)
- [Stratégie de test](docs/test-strategy.md)
- [Cas de test API](docs/test-cases-api.md)
- [Architecture d'automatisation](docs/automation-architecture.md)
- [Exécution des tests](docs/test-execution.md)
- [Performance](docs/performance-report.md)
- [CI/CD](docs/ci-cd.md)
- [Portfolio](docs/portfolio.md)

## Auteur

**Fatima Bousmiti**  
QA Automation Engineer — conception des scénarios, automatisation Web/API/mobile, performance, rapports et intégration CI/CD.  
Contact : [fatimabousmiti9@gmail.com](mailto:fatimabousmiti9@gmail.com)
