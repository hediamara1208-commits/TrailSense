# Pitch: the physics part (Dawud, D6)

Target: **30 seconds**, spoken slowly. One slide: a cross-section of the sky with the aircraft at FL350
inside a blue "ice-supersaturated" layer, and two arrows to FL330 / FL370 (one green, one red).

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
