"""[HEDI] Jev = Système 1 : décision rapide, typée et calibrée pour les vols signalés.

SDK : pip install typesafe-sdk ; clé dans TYPESAFE_API_KEY ; modèle "jev-latest".
Doc : https://docs.typesafe.ai/introduction/quickstart.md

Questions par vol (une question par facteur, comme le recommande la doc) :
- action                  Choice(climb_2000, descend_2000, maintain)
- persistent_warming      Noul  "Ce contrail sera persistant et réchauffant"
- forecast_reliability    Score (faible / moyenne / forte)
- operational_feasibility Score (difficile / possible / facile)

Frugalité : regrouper plusieurs vols signalés dans UN appel si la taille de requête le permet
(un state avec tous les vols, des questions préfixées par icao24). À tester tôt.
"""
from backend.models import Decision, RiskAssessment


def build_state(assessment: RiskAssessment) -> str:
    """Résumé texte/JSON compact du vol : niveau, T et RHi aux 3 niveaux, jour/nuit,
    minutes_in_issr, et pour chaque option : carburant, réchauffement évité, bilan net (déjà calculés).
    Jev est mauvais en calcul : on lui donne les chiffres, il choisit."""
    raise NotImplementedError


def decide(assessments: list[RiskAssessment], threshold: float) -> tuple[list[Decision], dict]:
    """Appelle Jev pour les vols signalés. Renvoie (décisions, usage) où usage = {calls, input_tokens}.

    route = AUTO si confidence >= threshold, sinon HUMAN.
    """
    raise NotImplementedError
