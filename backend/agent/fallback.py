"""[HEDI] Plan B sans Jev : règle codée en dur qui prend le relais si l'API Jev tombe
ou si l'accès anticipé bloque (config.USE_JEV = False, ou exception dans jev.decide()).

Même entrée, même sortie que jev.decide(), pour que pipeline.py bascule sans rien changer d'autre.

Règle proposée :
- Parmi climb et descend, garder les options dont le niveau n'est PAS persistant.
- Choisir celle qui a le plus grand net_benefit_co2e_kg, s'il est positif.
- Sinon : MAINTAIN.
- confidence = 1.0 si nuit et RHi > 110 %, sinon 0.6 (donc revue humaine avec le seuil par défaut).
Dans l'interface, afficher clairement "décision : règle de repli" pour rester honnête.
"""
from backend.models import Decision, RiskAssessment


def decide_by_rule(assessments: list[RiskAssessment], threshold: float) -> tuple[list[Decision], dict]:
    raise NotImplementedError
