# Architecture de ContrailWatch

## En une phrase
Un agent IA frugal qui aide les régulateurs de vol à éviter les traînées de condensation réchauffantes : il trouve en quelques millisecondes les rares vols concernés et propose ±2 000 ft, avec beaucoup moins de calcul qu'un agent classique (ratio mesuré par notre benchmark).

## Le flux (un cycle)
```
 OpenSky (avions)            Open-Meteo GFS (T, humidité 300→200 hPa)
        │                              │  cache par cellule 0,5° × 1 h, 1 appel groupé par cycle
        └──────────────┬───────────────┘
                       ▼
        physics/contrails.assess()       ← GRATUIT, déterministe
        SAC + RHi > 100 % au FL, FL+20, FL-20
                       │  seulement les vols "flagged"
                       ▼
        agent/jev.decide()               ← SYSTÈME 1 : rapide, calibré, appels groupés
        (plan B : agent/fallback.py si Jev indisponible)
        action + confiance → AUTO (≥ seuil) ou HUMAN (< seuil)
                       │  seulement les 2-3 plus importants
                       ▼
        agent/writer.llm_advisory()      ← SYSTÈME 2 : cher, rare (sinon gabarit)
                       │
                       ▼
        Snapshot + Receipt  →  api.py  →  frontend (carte Leaflet)
```

## Qui possède quoi
| Dossier / fichier | Propriétaire | Rôle |
|---|---|---|
| `backend/models.py` | **les deux** | Contrats de données. Toute modification se décide à deux. |
| `backend/config.py` | les deux | Paramètres (zone, niveaux, seuil, cache) |
| `backend/sources/opensky.py` | Dawud | Avions en direct |
| `backend/sources/weather.py` | Dawud | Profil météo + cache |
| `backend/sources/recorder.py` | Dawud | Enregistrer / rejouer le ciel (avions /5 min, météo /1 h) |
| `backend/physics/contrails.py` | Dawud | SAC, RHi, risque par niveau, jour/nuit |
| `backend/physics/fuel.py` | Dawud | Pénalité carburant, CO₂ |
| `backend/agent/jev.py` | Hedi | Décision Jev, seuil d'autonomie |
| `backend/agent/fallback.py` | Hedi | Plan B sans Jev (règle codée) |
| `backend/agent/writer.py` | Hedi | Avis LLM ou gabarit, mesure EcoLogits |
| `backend/agent/pipeline.py` | Hedi | Orchestration d'un cycle, Receipt |
| `backend/benchmark/all_llm.py` | Hedi | Comparaison avec un agent tout-LLM (~20 vols) |
| `backend/api.py` | Hedi | FastAPI |
| `frontend/` | Hedi | Carte, fiche vol, curseur, reçu |
| `data/fixtures/sample_snapshot.json` | les deux | Exemple fictif pour avancer en parallèle |

## Les points de contact entre Hedi et Dawud
1. `assess(aircraft, profile) -> RiskAssessment` : Dawud le produit, Hedi le consomme dans `pipeline.py` et `jev.py`.
2. `fetch_aircraft()`, `get_profile()`, `load_replay()` : appelés par `pipeline.py`.
3. Le JSON du `Snapshot` : produit par le backend, lu par le frontend. Le fichier `sample_snapshot.json` en est l'exemple.

Tant qu'un module n'est pas prêt, l'autre utilise le fichier exemple. Personne n'attend personne.

## Lancer le projet
```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # remplir les clés
uvicorn backend.api:app --reload                      # puis ouvrir http://localhost:8000
```

## Hypothèses à documenter (docs/hypotheses.md)
- Convention de l'humidité Open-Meteo (par rapport à l'eau ou à la glace).
- Rendement propulsif η utilisé dans le critère SAC.
- Formule de la pénalité carburant.
- Pourquoi la nuit compte plus (le contrail ne fait que piéger la chaleur).
