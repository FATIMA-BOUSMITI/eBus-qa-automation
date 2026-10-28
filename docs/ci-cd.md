# Préparer GitHub Actions

Le pipeline reste à créer et à valider sur GitHub. Les anciens YAML sont conservés dans [ci-templates](ci-templates) pour référence, hors du dossier actif `.github/workflows`. Aucun résultat local n'est présenté comme une exécution GitHub réussie.

## Dépôts et code testé

Le backend est dans [ikraammel/eBus_backend](https://github.com/ikraammel/eBus_backend), le frontend dans [ikraammel/eBus_frontend](https://github.com/ikraammel/eBus_frontend). Le dossier QA local possède son propre dépôt, sans remote encore configuré. Un workflow ne récupère pas automatiquement les deux autres dépôts : prévoir un checkout de chacun à une référence précise si la construction de leurs images en dépend.

Le projet Flutter est imbriqué dans le dépôt frontend ; repérer le `pubspec.yaml` pour définir le contexte de build. Il n'y a pas encore de Dockerfile frontend validé dans cette préparation. Le clone backend du workspace est indépendant du dépôt QA et n'est pas embarqué comme sous-module implicite.

## Séparer build et tests

1. Récupérer les sources voulues et construire les images. Cette étape peut utiliser Docker sans imposer Docker aux tests.
2. Choisir ce que les tests vérifient : une instance déjà déployée, ou une instance issue des nouvelles images.
3. Pour Render, attendre le déploiement et la disponibilité avant les tests. Le backend expose `/api/health`. Une réponse saine ne garantit pas à elle seule que le commit construit est déployé.
4. Installer nativement Python, Java/JMeter et Chromium sur le runner pour les suites concernées.
5. Exécuter les suites, conserver leur code de sortie et publier seulement des artefacts expurgés.

Tester les URLs Render après un build valide l'état des services accessibles à cet instant ; cela ne prouve pas que les images fraîchement construites ont été exécutées. Les tests backend d'intégration exigent séparément PostgreSQL dédié et les tests locaux exigent leurs fixtures.

## Secrets et variables

| Configuration | Emplacement prévu | Consommateur actuel |
| --- | --- | --- |
| `EBUS_USER_EMAIL`, `EBUS_USER_PASSWORD` | GitHub Secrets | Robot distant, JMeter distant, Playwright métier |
| `EBUS_ADMIN_EMAIL`, `EBUS_ADMIN_PASSWORD` | GitHub Secrets | Playwright métier |
| `EBUS_DEPLOYED_FRONTEND_URL` | Variable publique du job | Configuration Playwright métier |
| `EBUS_BROWSER_CHANNEL=chromium` | Variable publique du job | Playwright métier |

Injecter les secrets dans l'environnement du job, jamais dans le YAML, le JMX ou un fichier commité. La configuration refuse le repli vers le fichier privé local en CI pour les consommateurs indiqués. Le scénario ligne et Appium utilisent encore le fichier privé du poste : ils demandent une adaptation avant leur intégration GitHub.

Les environnements de contribution non fiables ne doivent pas recevoir les identifiants réels. Éviter toute journalisation de mots de passe, JWT ou réponses personnelles. Les traces navigateur et rapports complets peuvent contenir des données de session ; choisir explicitement les artefacts publiés.

## Déclenchement et déploiement

Le futur bloc `on` déterminera le comportement : `pull_request` teste avant fusion, `push` filtré sur la branche principale teste après la fusion ou un push direct, `workflow_dispatch` permet un lancement manuel. Un push sur une autre branche n'exécute un workflow que si ses filtres le permettent. Les dépôts distants n'activent pas automatiquement le workflow du dépôt QA.

Le push et le merge ne sont pas effectués par cette préparation. Le premier pipeline pourra rester manuel le temps de vérifier les secrets, la disponibilité Render et les rapports, puis évoluer vers des déclenchements automatiques.
