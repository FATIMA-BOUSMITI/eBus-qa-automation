# Tests de performance — Apache JMeter

Les plans JMeter mesurent les réponses de l'API eBus avec des assertions HTTP et des pauses entre requêtes. Ils s'exécutent avec **Java 17 et JMeter 5.6.3 installés nativement**. Aucun frontend et aucun conteneur ne sont nécessaires pour le smoke distant.

## Installation

Depuis la racine QA, après avoir défini `$pythonExe` comme dans le [README principal](../README.md#installation-native) :

```powershell
& .\qa\install-native.ps1 -PythonExe $pythonExe -WithJMeter
```

Le lanceur attend JMeter dans `.tools/apache-jmeter-5.6.3`. Vérifier que `java -version` fonctionne avant l'exécution.

## Smoke sur le backend déployé

```powershell
& .\qa\run-remote-suites.ps1 -Suite JMeter -PythonExe $pythonExe
```

Le script prépare un plan séparé, limité à **1 utilisateur, 1 itération, 7 requêtes**, sur `https://ebus-backend-ao2u.onrender.com`. Il utilise un compte USER existant via `EBUS_USER_EMAIL` / `EBUS_USER_PASSWORD`, ou le fichier privé local `.tools/mobile-credentials.json`. Les valeurs ne sont pas écrites dans le JMX généré. En CI, utiliser les variables issues de GitHub Secrets.

Le plan effectue une connexion puis des consultations authentifiées ; il ne crée ni paiement, ni utilisateur, ni ligne. Les préparatifs de connexion sont distincts des sept échantillons mesurés. Une pause de 1 seconde sépare les requêtes. Aucun test de charge massif n'est lancé sur Render par cette commande.

Les fichiers produits sous `reports/jmeter/remote-<date>/` comprennent `samples.jtl`, `jmeter.log`, le JMX généré et `dashboard/index.html`. Le lanceur vérifie la présence des sept échantillons et l'absence d'erreur. Ouvrir le dashboard dans le navigateur pour voir temps de réponse, percentiles et taux d'erreur.

Dernière mesure conservée : **7 échantillons, 0 erreur, moyenne 638,57 ms, minimum 238 ms, maximum 1 616 ms**, durée mesurée 13,44 s. Ce petit échantillon n'établit ni SLA ni capacité maximale. La [preuve complète](../docs/results/remote-suites.json) conserve le contexte.

## Smoke local

Préparer l'API et les données isolées selon le [guide local](../qa/README.md), puis :

```powershell
& .\qa\run-native.ps1 -Suite JMeter -PythonExe $pythonExe
```

La cible locale est `127.0.0.1:18080`. Le plan `smoke.jmx` et ses fixtures sont distincts du plan distant généré. L'ancienne mesure locale était de 7 échantillons sans erreur, moyenne 311,71 ms ; elle n'est pas directement comparable à Render.

## Alternative Docker pour le smoke local

Construire `ebus-qa-jmeter:local`, préparer l'API QA et ses fixtures, puis lancer depuis la racine `& .\qa\run-suites.ps1 -Suite JMeter`. Le [guide Docker](../docs/docker.md) décrit les prérequis, commandes et rapports. Le smoke distant Render reste disponible avec le lanceur natif.

## Voir le plan dans l'interface JMeter

```powershell
& .\.tools\apache-jmeter-5.6.3\bin\jmeter.bat -t .\jmeter\smoke.jmx
```

Cette commande ouvre **le plan local** pour comprendre ses groupes, requêtes et assertions. Le bouton de lancement utilise les paramètres de ce plan ; il ne configure pas automatiquement le backend distant. Utiliser le lanceur distant ci-dessus pour la cible Render. Réaliser les mesures avec le mode non graphique du lanceur pour réduire le coût de l'interface.

Les autres plans du dossier servent à préparer des profils progressifs et d'endurance. Leur présence ne signifie pas qu'ils ont été exécutés. Avant tout test de charge, choisir une infrastructure dédiée, des données isolées, des seuils et une fenêtre d'exécution autorisée.
