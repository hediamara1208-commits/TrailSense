"""[HEDI] API FastAPI. Lancer : uvicorn backend.api:app --reload

Endpoints :
- GET /api/snapshot?mode=replay|live&threshold=0.8&i=0  -> Snapshot en JSON
- GET /api/benchmark                                    -> résultat de benchmark/all_llm.py
- GET /                                                 -> sert frontend/index.html

Tant que le pipeline n'est pas prêt, /api/snapshot peut renvoyer
data/fixtures/sample_snapshot.json pour que l'interface avance en parallèle.
"""
from fastapi import FastAPI

app = FastAPI(title="ContrailWatch")

# TODO: routes ci-dessus, servir frontend/ en fichiers statiques, CORS si besoin.
