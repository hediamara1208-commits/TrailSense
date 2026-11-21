"""[HEDI] Benchmark : notre cascade contre un agent « tout-LLM » sur les MÊMES vols.

C'est la preuve chiffrée pour le prix Agent Solution.

Protocole :
1. Prendre un cycle enregistré (data/replay/...), limité à BENCHMARK_MAX_FLIGHTS (~20 vols)
   pour que le mode tout-LLM ne coûte pas cher.
2. Mode A, tout-LLM : envoyer chaque avion + son profil météo à un LLM et lui demander
   la décision. Mesurer appels, tokens, Wh et gCO₂ (EcoLogits), coût, latence.
3. Mode B, ContrailWatch : pipeline normal (physique -> Jev -> LLM pour 2-3 avis).
4. Comparer aussi les décisions (accord entre A et B) pour montrer qu'on ne perd pas en qualité.
Sortie : un JSON lu par GET /api/benchmark, affiché dans l'interface.
"""


def run_benchmark(replay_index: int = 0) -> dict:
    raise NotImplementedError
