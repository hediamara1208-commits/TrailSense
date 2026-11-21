# ContrailWatch physical assumptions

Every value is tunable in `backend/config.py`. Anything still **to be checked** is marked ⚠️.

## Data
| Topic | Choice | Why |
|---|---|---|
| Aircraft | OpenSky, FL290-410, \|vertical rate\| ≤ 2.5 m/s | We only advise aircraft in level cruise. |
| Weather | Open-Meteo GFS, levels 350 → 150 hPa | Brackets FL265 to FL450. Linear interpolation in ln(p). |
| Flight level → pressure | ISA standard atmosphere | A FL is a pressure altitude (1013.25 hPa setting). FL350 = 238.4 hPa. |
| Humidity convention | `RH_CONVENTION = "ice"` (capped at 100 %) | First recording: RH = exactly 100 % at −49.5 °C. Over water, that would mean ~155 % over ice, beyond the homogeneous freezing threshold (~145-150 %): unphysical. Confirmed by the overnight distribution: values pile up at 80-100 % and never exceed 100. |

## Formation: Schmidt-Appleman criterion (Schumann, 1996)
- Mixing-line slope G = EI_H2O · cp · p / (ε · Q · (1 − η)), with EI_H2O = 1.23, cp = 1004 J/kg/K, ε = 0.622, Q = 43.2 MJ/kg, **η = 0.35** (modern engines: 0.3 to 0.4).
- Dry threshold T_LM = −46.46 + 9.43 ln(G − 0.053) + 0.720 ln²(G − 0.053) (°C, G in Pa/K) → about −41 °C at 250 hPa.
- The contrail forms if T < T_LM and e_amb ≥ e_sat,water(T_LM) − G (T_LM − T).
- Saturation pressures: Sonntag (1994).

## Persistence
- RHi ≥ **95 %** (`RHI_THRESHOLD`) ⚠️ This is a **tuning choice**: GFS caps humidity at 100 % and underestimates supersaturation, which models are known to represent poorly (pycontrails also applies a humidity correction). The threshold changes how many flights are flagged: say so to the judges.
- Length crossed: **measured along the aircraft heading**, in 25 km steps through the 1° weather grid, while the current level stays supersaturated (max 800 km; stops at the grid edge). Contrail avoided by an option = the km where the current level is supersaturated but the target level is not. Fallback without a grid: **150 km** (`ISSR_TYPICAL_KM`), the mean length of an ice-supersaturated region along flight tracks (Gierens & Spichtinger, 2000). Limits: constant heading, wind and region motion ignored.

## Fuel
- Aircraft type unknown → generic fuel flow of **3,000 kg/h**.
- Extra burn during the deviation: **+1.5 % climbing, +2 % descending** (order of magnitude of the 2023 Google / American Airlines trial: ~2 % on diverted flights).
- **3.16 kg of CO₂ per kg** of kerosene.

## Avoided warming (the most uncertain estimate)
- Values used: **50 kg CO2e/km at night, 15 kg CO2e/km by day** (100-year horizon), with a ÷3 to ×3 range shown.
- Where it comes from (Borella et al., *ACP* 24, 9401-9417, 2024, https://acp.copernicus.org/articles/24/9401/2024/):
  - mean energy forcing (EF) of contrail-forming flights: **~9.6 × 10¹⁰ J per km** (median 2.9 × 10¹⁰, 90th percentile 2.8 × 10¹¹);
  - contrail climate efficacy: **0.37**;
  - CO₂ AGWP100 ≈ 9.2 × 10⁻¹⁴ W m⁻² yr kg⁻¹ (IPCC AR5), i.e. ≈ 1.48 × 10⁹ J per kg of CO₂ over 100 years.
  - → 9.6 × 10¹⁰ × 0.37 / 1.48 × 10⁹ ≈ **24 kg CO2e per km** on average, day and night. Night weighs more (no solar cooling), day less, hence 50 / 15.
  - ✅ Verified in the paper (Sect. 3): "Contrail energy forcing per flown distance ranges from −8.7 × 10¹¹ to 5.0 × 10¹² J km⁻¹, with a mean of 9.6 × 10¹⁰ J km⁻¹ and a median of 2.9 × 10¹⁰ J km⁻¹." In their sample, 55 % of flights form contrails, 80 % of which are warming; warming contrails add 23 times more energy than cooling ones remove.
  - **Conservative assumption**: this mean is per *flown* km (the full length of contrail-forming flights), while we apply it per km *of contrail*. The real warming per km of contrail is therefore higher: our benefit is underestimated, not inflated.
  - Note: the paper gives 1.3 × 10¹⁰ J/km as the mean of warming contrails only, lower than the overall mean, which looks inconsistent (probably a typo). We rely on the overall mean.
- The choice of metric (GWP100, GWP20, ATR…) changes the result a lot: that is the very topic of Borella et al. We use the 100-year horizon, as for CO₂.
- Robustness: for an aircraft at 500 kt, 150 km of supersaturated region = 18 min, i.e. ~13 kg of extra fuel (~42 kg CO₂) versus ~7.5 t CO2e avoided at night. The benefit stays positive even with the factor divided by 100, consistent with Teoh et al. (2020): ~59 % of contrail forcing avoided for ~0.014 % extra fuel.

## What we do not model
Real traffic and air traffic control approval (the tool is a decision aid for the flight dispatcher), wind, aircraft type, the true extent of the supersaturated region, and detailed radiative effects (CoCiP).
