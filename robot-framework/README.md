# Tests API — Robot Framework

Deux suites distinctes vérifient l'API eBus : `remote/remote.robot` contient 12 contrôles sur Render ; `tests/api.robot` contient 20 cas pour une API locale isolée. Les ressources Python gèrent les sessions et les assertions. Un HTTP 500 reste un échec.

## Exécuter sur Render, sans Docker

Depuis la racine QA, après l'[installation native](../README.md#installation-native) :

```powershell
& .\qa\run-remote-suites.ps1 -Suite Robot -PythonExe $pythonExe
```

L'API cible est `https://ebus-backend-ao2u.onrender.com`. Aucun frontend n'est nécessaire. Le compte USER existant est lu dans les variables `EBUS_USER_EMAIL` et `EBUS_USER_PASSWORD`, ou dans le fichier privé `.tools/mobile-credentials.json` sur le poste. En CI, les deux variables sont obligatoires : les injecter depuis GitHub Secrets.

La suite contrôle santé, bus, lignes, tickets, types d'abonnement, profil, dossier, abonnement courant, historique, cartes et activités. Elle autorise uniquement GET et POST `/users/login`, sans suppression, achat ou création métier. Le lanceur masque les détails sensibles et produit `reports/robot/remote-<date>/report.html`, `log.html` et `output.xml`.

Dernière preuve distante conservée : **11 PASS / 1 FAIL**. Le cas REM-005 attend HTTP 200 pour les types d'abonnement anonymes et reçoit 500. Ce défaut n'est pas masqué. Voir [le compte rendu](../docs/remote-robot-jmeter.md).

## Exécuter localement

Préparer une API dédiée sur `http://127.0.0.1:18080` et les fixtures décrites dans le [guide local](../qa/README.md), puis :

```powershell
& .\qa\run-native.ps1 -Suite Robot -PythonExe $pythonExe
```

Cette suite utilise des comptes synthétiques et les préconditions locales. Elle ne doit pas être redirigée vers une base réelle : les scénarios locaux ont un périmètre différent des contrôles distants. Les rapports se trouvent dans `reports/robot/`. L'exécution locale antérieure donne **12 PASS / 8 FAIL**, détaillés dans l'[historique](../docs/test-execution.md).

## Alternative Docker pour la suite locale

Après construction de `ebus-qa-automation:local` et préparation de l'API QA avec ses fixtures, lancer depuis la racine `& .\qa\run-suites.ps1 -Suite Robot`. Les étapes complètes sont dans le [guide Docker](../docs/docker.md). La suite distante conserve le lanceur natif décrit plus haut.

## Lire un résultat

Ouvrir `report.html` pour le bilan, puis `log.html` pour le cas concerné. Un problème de disponibilité ou de compte est une précondition bloquante ; une réponse applicative incorrecte est un échec. Ne publier ni mots de passe, ni JWT, ni réponses contenant des informations personnelles dans les artefacts GitHub.
