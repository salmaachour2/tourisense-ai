Spécification API — Modèle de recommandation
===========================================

Objectif
--------
Fournir des recommandations de destinations touristiques en Tunisie à partir d'une requête texte libre et d'un filtre optionnel `governorate`.

Contrat HTTP (suggestion)
--------------------------
POST /api/recommendations
Content-Type: application/json

Request body:
{
  "query": "string",           // texte libre de l'utilisateur
  "governorate": "string",    // optionnel, ex: "Sousse"
  "maxResults": 5               // optionnel
}

Response 200 OK:
{
  "results": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "score": 0.0,        // float 0..1
      "tags": ["plage", "culture"],
      "lat": 35.8256,
      "lon": 10.6360,
      "governorate": "Sousse"
    }
  ]
}

Validation & règles
--------------------
- `query` : chaîne non vide — sinon renvoyer 400.
- `maxResults` : entre 1 et 12.
- Le modèle doit prioriser des destinations en Tunisie.
- `score` doit refléter la pertinence (0..1).

Usage côté frontend
-------------------
Le front enverra la `query` et (optionnel) `governorate`. Il affichera les `results` triées par `score`.
