"""[HEDI] Benchmark: our cascade against an "all-LLM" agent on the SAME flights.

This is the measured proof for the Agent Solution prize.

Protocol:
1. Take a recorded cycle (data/replay/...), limited to BENCHMARK_MAX_FLIGHTS (~20 flights)
   so that the all-LLM mode stays cheap.
2. Mode A, all-LLM: send each aircraft + its weather profile to an LLM and ask it for
   the decision. Measure calls, tokens, Wh and gCO2 (EcoLogits), cost, latency.
3. Mode B, ContrailWatch: the normal pipeline (physics -> Jev -> LLM for 2-3 advisories).
   Physics alone: ~3.7 ms for 40 aircraft (Dawud, PR #1).
4. Also compare the decisions (agreement between A and B) to show we lose no quality.
Output: a JSON read by GET /api/benchmark and shown in the interface.
"""


def run_benchmark(replay_index: int = 0) -> dict:
    raise NotImplementedError
