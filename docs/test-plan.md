# Plan de test eBus

L'objectif est de vérifier les parcours de transport et la cohérence API/UI avec des résultats traçables. Le système comprend Flutter Web/Android, Spring Boot, PostgreSQL, JWT et Stripe. Les dépôts et cibles sont recensés dans le [README principal](../README.md).

## Couches de vérification

| Couche | Outil | Périmètre |
| --- | --- | --- |
| Services Java | JUnit / Mockito / JaCoCo | Abonnements et objets perdus, sans base |
| Contexte/API Java | Spring Boot / MockMvc | Base PostgreSQL locale dédiée |
| API fonctionnelle | Robot, Postman/Newman | Contrats, authentification, cas négatifs |
| Navigateur | Playwright | Navigation, droits, cycles ligne/objet/réclamation/offre |
| Android | Robot / Appium | UI et comptes existants sur téléphone réel |
| Performance | JMeter | Smoke limité ; profils de charge à valider séparément |

## Environnements et données

Les suites locales utilisent une API QA sur `18080`, un frontend sur `17357` et des fixtures synthétiques dans une base isolée. Les tests Java d'intégration utilisent un PostgreSQL séparé sur `55433`. Installer les services nativement ; Docker ne fait pas partie des prérequis d'exécution retenus.

Sur Render, Robot/JMeter restent en lecture et connexion. Les scripts E2E dédiés peuvent créer et retirer uniquement leurs propres données temporaires, avec les comptes existants. Les utilisateurs, lignes et autres enregistrements préexistants sont conservés. Les fixtures locales ne sont jamais importées dans la base réelle.

## Critères et preuves

Une assertion réussit sur un résultat observé, pas sur la simple présence d'un fichier de test. Les erreurs HTTP et écarts métier restent des échecs. Distinguer une précondition indisponible d'un défaut applicatif, et conserver l'historique des reprises ciblées. Les preuves expurgées sont dans [results](results) ; les rapports complets restent locaux dans `reports/`.

La petite mesure JMeter distante ne démontre pas la capacité en charge. Un paiement Stripe réussi n'a pas été validé. Les parcours métier Playwright vérifiés utilisent le frontend local connecté à Render ; la future CI sur le frontend déployé reste à exécuter. Le pipeline d'images et GitHub Actions reste une étape distincte.

## Exécution

Utiliser les guides [QA natif](../qa/README.md), [Robot](../robot-framework/README.md), [JMeter](../jmeter/README.md), [Playwright](../playwright/README.md), [Appium](../appium/README.md) et [Postman](../postman/README.md). L'[historique](test-execution.md) conserve les exécutions antérieures et leurs limites ; il ne remplace pas les commandes actuelles des guides.
