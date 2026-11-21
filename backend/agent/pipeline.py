"""[HEDI] Orchestrateur : un cycle complet, du ciel jusqu'au Snapshot.

    avions (live ou replay)
      -> météo (cache)              [Dawud : sources/weather.py]
      -> filtre physique            [Dawud : physics/contrails.py]
      -> Jev sur les vols signalés  [Hedi : agent/jev.py]
      -> avis (gabarit -> Granite -> Cloud LLM) [Hedi : agent/writer.py]
      -> Snapshot + Receipt         renvoyé par l'API

Optimisation : garder en mémoire le dernier RiskAssessment par avion et ne le recalculer
que si l'avion change de cellule météo ou de niveau de vol.
"""
from backend.models import Snapshot


def run_cycle(mode: str = "replay", threshold: float = 0.8, replay_index: int = 0) -> Snapshot:
    """Exécute un cycle et remplit le Receipt (compteurs, latence, énergie)."""
    raise NotImplementedError
