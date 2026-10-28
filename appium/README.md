# Tests Android sur Redmi — Robot Framework et Appium

Appium pilote l'application Android sur le téléphone réel : les ouvertures d'écran, saisies et clics sont visibles sur le Redmi. L'APK eBus Render utilise le backend distant ; aucun backend local ni Docker n'est nécessaire.

## Prérequis

- Android 12, téléphone et PC sur le même Wi-Fi, écran déverrouillé.
- Android SDK/ADB, Java 17, Node.js, Appium avec le driver UiAutomator2.
- Python et les dépendances de `appium/requirements.txt` installées dans `.tools/mobile-addons`.
- APK Render installé et serveur Appium disponible sur `127.0.0.1:4723`.

Depuis la racine QA, pour préparer les outils du poste :

```powershell
& $pythonExe -m pip install --target .tools/mobile-addons -r appium/requirements.txt
npm.cmd install --prefix .tools/appium appium@3.8.0
$env:APPIUM_HOME = "$PWD\.tools\appium-home"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
& .\.tools\appium\node_modules\.bin\appium.cmd driver install uiautomator2
```

Ces étapes nécessitent une connexion réseau et de l'espace disque ; elles ne reconstruisent pas le frontend automatiquement.

## Connecter le téléphone par Wi-Fi

Activer les options développeur et le débogage sans fil. L'adresse d'association et celle de connexion ont des ports différents ; elles peuvent changer à chaque session. Ne pas réutiliser un ancien code.

```powershell
& .\appium\connect-wifi.ps1 -PairAddress 'IP:PORT_ASSOCIATION' -ConnectAddress 'IP:PORT_CONNEXION'
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices
```

Saisir le code temporaire lorsqu'ADB le demande. La ligne de l'appareil doit être dans l'état `device`. Les codes d'association ne sont ni des identifiants eBus ni des GitHub Secrets permanents.

## Préparer l'application Render

`build-render.ps1` construit une variante distincte, et `install-render.ps1` vérifie le manifeste du build avant installation. L'application originale `com.example.smart_bus` est conservée ; la variante de test utilise `com.example.smart_bus.render`, libellé eBus Render. Consulter les paramètres en tête de ces scripts pour le SDK Flutter et le numéro de série du téléphone.

## Voir les tests s'exécuter

Dans un premier terminal, à la racine QA :

```powershell
$env:APPIUM_HOME = "$PWD\.tools\appium-home"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
& .\.tools\appium\node_modules\.bin\appium.cmd --address 127.0.0.1 --port 4723 --log-level warn
```

Dans un second terminal, avec `$pythonExe` défini :

```powershell
# 20 parcours UI et navigation :
& .\appium\run.ps1 -RemoteInstalled -Serial 'IP:PORT_CONNEXION' -PythonExe $pythonExe
# 3 connexions avec les comptes existants, profil puis déconnexion :
& .\appium\run.ps1 -RemoteInstalled -Authenticated -Serial 'IP:PORT_CONNEXION' -PythonExe $pythonExe
```

La suite authentifiée lit `.tools/mobile-credentials.json` avec les alias `ACCOUNT1`, `ACCOUNT2`, `ACCOUNT3`, chacun contenant `email` et `password`. Ce fichier privé est exclu de Git. Le lanceur Appium actuel n'est pas encore adapté à une exécution GitHub Secrets sans ce fichier.

Fermer le panneau de notifications et éviter de toucher l'écran pendant la suite. Les tests se voient sur le téléphone ; `reports/appium/<date>/report.html` et `log.html` permettent ensuite de consulter le résultat sur PC.

## Résultats et limites

Les vingt parcours UI donnent **19 PASS / 1 FAIL après reprises ciblées**. Le cas MOB-007 reste en échec : le panneau de notifications recouvrait l'application. MOB-017 a vérifié une ligne affichée contre l'API Render. Les trois connexions authentifiées ont donné **3/3 PASS**, avec consultation du profil et déconnexion.

Ces tests ne suppriment pas les comptes ou les lignes existantes. Aucun achat réel n'est validé. Les contrôles `-DryRun` vérifient la structure Robot sans manipuler l'application ; ils ne constituent pas une exécution fonctionnelle. Voir les [preuves UI](../docs/results/render-mobile.json) et [preuves authentifiées](../docs/results/appium-authenticated.json).

Un runner GitHub hébergé n'a pas accès automatiquement au téléphone Wi-Fi du poste. Prévoir ultérieurement un émulateur, un service d'appareils ou un runner dédié pour automatiser le mobile en CI.
