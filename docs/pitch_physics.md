# Pitch: the physics part (Dawud, D6)

Target: **30 seconds**, spoken slowly. One slide: a cross-section of the sky with the aircraft at FL350
inside a blue "ice-supersaturated" layer, and two arrows to FL330 / FL370 (one green, one red).

## The slide (for the deck, D6 final)
**Image:** `docs/figures/cross_section.png` (full width).

**Title:** Contrails need cold air **and** ice-supersaturated air. Step out of the layer.

**Three lines under the image:**
1. **Form + persist:** Schmidt-Appleman criterion + RHi ≥ 95 % on GFS weather, at the current level and ±2,000 ft. 37 ms for 451 aircraft.
2. **Night matters most:** Europe, same morning: night cycle 14 flights → ≈ 83 t CO2e avoided; day cycle 22 flights → ≈ 42 t.
3. **Honest about uncertainty:** threshold 95 % (3 flights; 6 at 90 %), CO2e shown with a ÷3 to ×3 range.

**Speaker cue (example from the demo):** RUK54ST at FL370: 225 km of supersaturated air ahead. Climbing to FL390 costs 13 kg of fuel
(41 kg CO₂) and avoids ≈ 3.3 t CO2e.

## The 30-second script

> "A contrail needs two things.
> First, it has to **form**: the hot, humid exhaust mixes with cold air and condenses.
> That's the Schmidt-Appleman criterion, and above roughly minus 40 degrees it simply can't happen.
> Second, it has to **persist**: the air must be **supersaturated with respect to ice**.
> If it isn't, the trail vanishes in seconds. If it is, it spreads into cirrus for hours, and at night it only traps heat.
> These layers are thin, often just a couple of thousand feet.
> So moving **2,000 feet up or down**, which keeps the aircraft on a legal level for its direction,
> is often enough to get out. We check both options along the aircraft's actual track,
> and only recommend the one where the warming avoided is far larger than the CO₂ of the extra fuel."

(~30 s at a calm pace. Key words to stress: *form*, *persist*, *2,000 feet*, *net benefit*.)

## One-liners to keep in your pocket
- **Scale:** contrail cirrus is the largest single term of aviation's net effective radiative forcing,
  larger than aviation's CO₂ (Lee et al., 2021). 
- **Few flights matter:** in Japanese airspace, ~2 % of flights caused ~80 % of the contrail warming (Teoh et al., 2020).
- **It works in practice:** flights that followed the forecasts cut contrails by 54 % for ~2 % more fuel on those flights
  (Google / American Airlines trial, 2023).

## Jury questions: 2-3 sentence answers

**1. "Are your forecasts reliable?"**
Not perfectly, and we say so. Weather models capture ice-supersaturated layers poorly: GFS caps humidity at 100 %,
so we use a 95 % threshold and show a confidence level instead of a yes/no. Because a deviation costs only a few
kilograms of fuel, a false alarm is cheap, while a missed contrail is expensive.

**2. "What about air traffic control?"**
TrailSense doesn't move aircraft. It's a decision aid for the airline dispatcher, who requests the new level from ATC
like any other level change. A ±2,000 ft shift keeps the east/west level parity of RVSM airspace, so the proposed level is one
the flight could actually be cleared to.

**3. "Where does your CO2e number come from?"**
From Borella et al. (ACP, 2024): a mean contrail energy forcing of 9.6 × 10¹⁰ J per flown km, a contrail efficacy of 0.37,
converted with the 100-year warming potential of CO₂, which gives ~24 kg CO2e per km. We use 50 at night and 15 by day,
and show a ×3 range. The number is conservative: the paper's mean is per *flown* km, we apply it per km *of contrail*.

**4. "Why not just cut CO₂?"**
We should, but that takes decades: new aircraft, sustainable fuels. Contrail avoidance works tomorrow, with today's aircraft,
on a handful of flights, and contrail warming disappears within hours once you stop creating them. It's the fastest
climate lever aviation has.

**5. "How much does it cost airlines?"**
Very little. Only a few percent of flights need a deviation, and each one burns about 1.5 to 2 % more fuel for the
15 to 20 minutes it spends off its optimal level. In our real recording, a 75 km deviation costs about 4 kg of fuel
for about 3.75 t of CO2e avoided at night. Teoh et al. estimate ~59 % of contrail forcing avoided for ~0.014 % more fuel
across the fleet.

## Backup questions
- **"Why at night?"** By day, a contrail also reflects sunlight, which partly offsets its warming. At night it only traps
  outgoing heat, so night contrails warm the most. Our model weighs them ~3× more.
- **"Why climb rather than descend?"** We compute both. Colder air higher up can make contrails *more* likely,
  so sometimes descending is the right answer. The physics decides, not a fixed rule.
- **"What if the target level is also supersaturated?"** Then the warming avoided is zero, the net benefit is negative,
  and the agent recommends staying put. We never move a flight just to move the contrail.
- **"What don't you model?"** Wind, the exact aircraft type, real traffic, and detailed radiative transfer (CoCiP).
  All our assumptions are listed in `docs/hypotheses.md`.

## Threshold sensitivity (W5, measured on the whole east_canada recording)
`python -m backend.physics.scan --sweep`, 59 cycles, 1,231 aircraft positions:

| RHi threshold | flagged positions | unique flights | net CO2e avoided |
|---|---|---|---|
| 90 % | 9 | 6 | 47 t |
| 92.5 % | 6 | 3 | 39 t |
| **95 % (ours)** | **4** | **3** | **10 t** |
| 97.5 % | 4 | 3 | 10 t |
| 100 % | 0 | 0 | 0 |

**"How sensitive is your result to the threshold?"**
The *count* is sensitive: going from 95 % to 90 % doubles the flagged flights (3 → 6). But in every case it is under 1 %
of aircraft, so the core message holds: a handful of flights matters. 100 % flags nothing because GFS caps humidity at
100 %, which is exactly why a threshold below 100 is needed. We picked 95 %, the conservative end: it gives the smallest
claimed benefit, and Jev's low forecast-reliability score sends these borderline cases to a human.

## More physics questions (Sat afternoon)

**"Why not over the North Atlantic, where most long-haul traffic is?"**
We tried. Our free aircraft source, OpenSky, relies on ground receivers, so it sees almost nothing over the ocean.
In a real deployment the dispatcher already has every flight plan and position (satellite ADS-B),
so the same physics runs on oceanic tracks unchanged.

**"Your CO2e factor is uncertain by ×3. Doesn't that kill the result?"**
No, because the cost side is tiny. RUK54ST avoids ≈ 3.3 t CO2e for 41 kg of CO₂ from extra fuel: even divided by 3,
the benefit is 25 times the cost; it would take a factor ~80 error to flip the sign. The uncertainty changes *how much*
we gain, rarely *whether* we gain. That's why we show a range, not a single number.

**"GFS caps humidity at 100 %. How can you detect supersaturation?"**
We can't see *how* supersaturated the air is, only that it is at or near saturation over ice. So we flag RHi ≥ 95 %
and treat it as a candidate, not a certainty. Jev's low forecast-reliability score on these cases sends them to a human.
Better humidity data (e.g. ERA5 with a humidity correction, or on-board sensors) would plug straight in.

**"Why does the day cycle have more flagged flights but less benefit?"**
By day a contrail also reflects sunlight, which partly offsets its warming, so we count 15 kg CO2e per km instead of 50 at night.
More flights flagged, half the climate gain: the night flights are the ones worth moving first.

**"Some 'dry' target levels are at 94 % RHi. Isn't that borderline?"**
Yes, and we don't hide it: at a lower threshold the target would count as humid too, and the option would disappear.
That's exactly the threshold-sensitivity table above (90 %: benefit changes). These are the cases where the agent's
confidence is lower and a human reviews the decision.

**"Why do some flagged flights get no recommendation?"**
When the levels above and below are also supersaturated, moving only burns fuel without avoiding the contrail.
The code then decides "maintain" on its own, without even calling Jev: in the Europe cycles, 4 of 14 at night and 5 of 22 by day.

## GFS vs ECMWF (Sat afternoon, `python -m backend.physics.compare_models europe 1`)
Europe cycle 1795243469 (06:44 UTC), 9 flagged aircraft + 77 grid points, 344 values below −40 °C:

| Model | ≥ 95 % | = 100 % | > 100 % | max |
|---|---|---|---|---|
| GFS | 21 | 15 | 0 | 100 % |
| ECMWF IFS | 22 | 19 | 0 | 100 % |

- **Both public feeds cap RH at 100 %**, so switching model does not reveal how supersaturated the air is.
- Same overall humidity (same convention: RH over ice), but **they disagree on where**: at the 9 aircraft GFS flags,
  ECMWF gives 51-93 %. Ice-supersaturated layers are thin and models place them differently.

**"Did you try another weather model?"**
Yes, ECMWF, the best global model. It is capped at 100 % too, and at the exact aircraft positions it often disagrees with GFS.
That's the honest state of the art: humidity at cruise altitude is the weakest link of every contrail forecast. It's why the agent
gives low forecast-reliability scores and sends these cases to a human. The next step is to require both models to agree
before acting automatically, which turns model disagreement into a confidence signal.
