"""[HEDI] LLM = Système 2 : rédiger l'avis pour la régulatrice, seulement quand ça vaut le coût.

Règle : le LLM n'écrit que les MAX_LLM_ADVISORIES avis les plus importants
(nuit, forte probabilité de réchauffement, forte confiance). Les autres utilisent un gabarit.
Mesurer chaque appel avec EcoLogits (pip install ecologits ; EcoLogits.init(providers=["anthropic"])).

Exemple d'avis attendu :
"ACA871 au FL360 traverse une couche sursaturée en glace (RHi 118 %). Le FL340 est sec.
Proposition : descendre de 2 000 ft pendant ~12 min. Coût : +38 kg de carburant.
Confiance Jev : 0,91."
"""
from backend.models import Advisory, Decision, RiskAssessment


def template_advisory(decision: Decision, assessment: RiskAssessment) -> Advisory:
    """Avis gratuit à partir d'un gabarit de texte."""
    raise NotImplementedError


def llm_advisory(decision: Decision, assessment: RiskAssessment) -> tuple[Advisory, dict]:
    """Avis rédigé par le LLM. Renvoie (avis, impacts) avec impacts = {energy_wh, gco2e, cost_usd}."""
    raise NotImplementedError


def rank_for_llm(decisions: list[Decision]) -> list[Decision]:
    """Choisit les vols qui méritent un avis rédigé par le LLM."""
    raise NotImplementedError
