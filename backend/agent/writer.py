"""[HEDI] Rédaction des avis pour la régulatrice : une cascade, du moins cher au plus cher.

    1. Gabarit (gratuit)            -> tous les vols signalés par défaut
    2. Granite local (IBM, Ollama)  -> les MAX_GRANITE_ADVISORIES avis suivants, sur le portable
    3. Claude (cloud, petit modèle) -> seulement les MAX_CLAUDE_ADVISORIES avis les plus importants
                                       (nuit, forte probabilité de réchauffement, gros bilan net)

Granite : `ollama pull <GRANITE_MODEL>` puis POST {OLLAMA_URL}/api/chat (httpx suffit).
Énergie locale : estimer puissance du portable (W) × durée de l'appel (s) / 3600 -> Wh.
Claude : SDK anthropic ; mesurer chaque appel avec EcoLogits (EcoLogits.init(providers=["anthropic"])).
Si USE_GRANITE = False ou si Ollama ne répond pas : on saute l'étage 2 sans planter.

Exemple d'avis attendu :
"ACA871 au FL360 traverse une couche sursaturée en glace (RHi 118 %). Le FL340 est sec.
Proposition : descendre de 2 000 ft pendant ~12 min. Coût : +38 kg de carburant.
Bilan net estimé : +780 kg CO2e évités. Confiance Jev : 0,91."
"""
from backend.models import Advisory, Decision, RiskAssessment


def template_advisory(decision: Decision, assessment: RiskAssessment) -> Advisory:
    """Avis gratuit à partir d'un gabarit de texte."""
    raise NotImplementedError


def granite_advisory(decision: Decision, assessment: RiskAssessment) -> tuple[Advisory, dict]:
    """Avis rédigé par Granite en local. Renvoie (avis, impacts) avec impacts = {energy_wh, latency_ms}."""
    raise NotImplementedError


def claude_advisory(decision: Decision, assessment: RiskAssessment) -> tuple[Advisory, dict]:
    """Avis rédigé par Claude. Renvoie (avis, impacts) avec impacts = {energy_wh, gco2e, cost_usd}."""
    raise NotImplementedError


def route_writers(decisions: list[Decision], assessments: list[RiskAssessment]) -> dict[str, str]:
    """Décide qui rédige chaque avis : {icao24: "claude" | "granite" | "template"}.

    Classer par importance (nuit, persistent_warming_prob, net_benefit), donner le top
    MAX_CLAUDE_ADVISORIES à Claude, les MAX_GRANITE_ADVISORIES suivants à Granite, le reste au gabarit.
    """
    raise NotImplementedError
