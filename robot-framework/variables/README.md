# Variables des suites API

La suite locale utilise `EBUS_API_URL=http://127.0.0.1:18080`, une API QA dédiée et les identités synthétiques de `qa/seed.sql`. Ne pas lui fournir de comptes réels.

La suite distante séparée lit `EBUS_USER_EMAIL` et `EBUS_USER_PASSWORD`, ou le fichier privé du poste hors CI. Voir le [guide Robot](../README.md).
