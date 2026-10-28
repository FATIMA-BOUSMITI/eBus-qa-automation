# Fixtures et nettoyage

La suite locale attend les cinq comptes et abonnements synthétiques de `qa/seed.sql`, dans une base vide dédiée. `qa/restore.sql` rétablit les transitions de ces fixtures locales uniquement : ne jamais l'exécuter sur Render ou sur une base réelle.

ROB-016 contient trois cas négatifs de connexion. Chaque test ouvre sa session et s'authentifie indépendamment si nécessaire. La suite consulte les données et vérifie des refus attendus avant paiement ou mutation ; examiner les effets éventuels d'un refus incorrect dans la base QA. La fermeture de session n'annule pas une éventuelle écriture serveur.

La suite distante utilise les comptes existants, sans importer de fixture et sans supprimer d'utilisateur ou de ligne.
