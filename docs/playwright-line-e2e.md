# Ligne : création, vérification et suppression sur la vraie base

Ce scénario est distinct des vingt tests locaux de navigation. Il ouvre le frontend Flutter web local dans Chrome et laisse ses requêtes atteindre le backend distant `https://ebus-backend-ao2u.onrender.com`. Les réponses viennent du serveur réel, sans données simulées. Il n'utilise pas le transfert vers le backend QA sur le port 18080.

Les comptes déjà fournis sont lus depuis `.tools/mobile-credentials.json`, ignoré par Git. Le test sélectionne un compte dont le backend confirme le rôle ADMIN, puis se connecte par le formulaire de l'interface. Aucun mot de passe ou jeton n'est imprimé. Les traces, vidéos et captures contenant des comptes réels sont désactivées.

## Parcours

1. Lire le catalogue initial et choisir un numéro unique `QA-E2E-...` absent de ce catalogue.
2. Se connecter dans Chrome et ouvrir Gestion des lignes.
3. Ajouter une ligne via le formulaire, sans stations ni affectations de bus.
4. Vérifier la réponse réelle de création, l'identifiant, les champs persistés dans le catalogue backend et l'affichage de la ligne dans l'interface.
5. Rechercher uniquement cette ligne, la supprimer via l'interface et confirmer la suppression.
6. Vérifier sa disparition dans l'interface et dans le catalogue backend ; vérifier que les lignes initiales sont inchangées.

Le garde-fou réseau bloque les écritures autres que la connexion, la création du contenu exact généré et la suppression de l'identifiant créé pendant ce passage. Une suppression d'identifiant présent dans le catalogue initial est refusée. En cas d'échec UI après création, un nettoyage API est limité à la ligne portant ce numéro unique, absente du catalogue initial et dont les champs correspondent exactement au test. Un nettoyage API ne transforme jamais un échec UI en réussite E2E.

## Commandes PowerShell

Depuis `C:\Users\fatouma\Desktop\ebus`, inspection sans écriture de ligne :

```powershell
.\playwright\run-line-lifecycle.ps1 -Inspect
```

Exécution complète, Chrome visible :

```powershell
.\playwright\run-line-lifecycle.ps1
```

Le script démarre le serveur web local si nécessaire. Le backend local QA n'est pas requis. L'ordinateur doit accéder au backend distant et Chrome doit être installé. La suite utilise les dépendances déjà installées dans `.tools/qa-addons`.

Rapports sans secrets : `reports/playwright/line-lifecycle/<horodatage>/summary.json` et `report.html`. `status=PASS` prouve le parcours complet ; `INSPECTED` confirme uniquement l'inspection. Un échec conserve l'étape et le type d'erreur. Si `cleanup_requires_attention` est vrai ou `test_line_absent_after_cleanup` est faux, traiter la ligne portant le numéro exact indiqué avant une nouvelle exécution.

## Exécution vérifiée

Le passage `20261027-182352` est **PASS** : connexion administrateur existant, création via formulaire, vérification des champs persistés et de la présence dans l'interface, suppression via dialogue UI, puis absence vérifiée dans l'interface et le catalogue backend. Ligne de test `QA-E2E-242f18fad3c2`, identifiant 27, supprimée. Le catalogue contenait 19 lignes avant et après ; les 19 lignes initiales sont inchangées.

Les essais précédents échoués lors de l'adaptation des sélecteurs sont conservés séparément. Leur nettoyage API n'est pas présenté comme une suppression UI réussie. Le résultat final est celui d'un seul parcours complet, sans fusionner les étapes de plusieurs essais.
