# Three-shell attraction / chirality test — preregistration

Date: 2026-09-14
Status: frozen before the 20-shard run

## Question

Test the new Vardath three-shell proposal as geometry rather than mythology: two shells share one handedness and one is reversed, and attraction rather than resistance may supply the turning/alignment that produces repeated gates, local bundling and a temporary axial state.

This is a toy geometric/dynamical test. A positive result means the proposed geometry has the stated mathematical behavior under the declared interaction model; it does not establish a physical force law for the real world.

## One run, 20 shards

One GitHub Actions workflow runs shards 0–19. Each shard samples an independent deterministic parameter batch. The merge uses all 20 shards and reports every declared test, including failures.

## Shell representation

Each shell is a logarithmic spiral sampled on polar rays. For physical polar angle alpha and turn number n, shell i has

`log r = log(a_i) + b_i * t`

with `t = ((alpha - phi_i) mod 2pi) + 2pi n` for clockwise chirality and `t = ((phi_i - alpha) mod 2pi) + 2pi n` for reversed chirality.

Thus chirality changes the winding direction while every shell grows outward with increasing path parameter. Adjacent shells interact; direct inner-to-outer coupling is excluded in v1 so the middle shell is genuinely the interface.

Interaction strength is represented by a scale-free proximity kernel

`P = mean(exp(-|log r_i - log r_j| / sigma))`.

Attraction chooses the relative phase that maximizes P. Repulsion chooses the phase that minimizes P. This intentionally tests geometry/torque and not a claimed fundamental physical potential.

## Frozen parameter ranges

Each shard samples 80 cases (1,600 total):
- turns: 4–8
- pitch b: 0.018–0.075 per radian, with adjacent-shell pitch mismatch up to ±12%
- adjacent radial scale ratio: 1.15–2.10
- proximity width sigma: 0.045–0.12 in log-radius
- phase grid: 24 evenly spaced offsets
- angular sampling: 180 rays

Random seeds are `73013 + shard_id * 100003`.

## Declared tests

### T1 — attraction versus repulsion can turn/alignment-shift the shells
At a random relative phase, estimate the finite-difference gradient of P with respect to phase. Attraction follows +grad(P); repulsion follows -grad(P).

Prediction: nonzero torque/phase tendency should be common, and attraction and repulsion should point in opposite directions. This test can show attraction is capable of turning/alignment; it cannot by itself prove attraction is the real force.

Positive rule: median absolute gradient > 0.01 and >80% of cases have opposite attraction/repulsion directions.

### T2 — mixed chirality is favored by attraction
Compare the attraction-optimized adjacent-pair proximity of same-chirality versus opposite-chirality pairs.

Prediction: opposite chirality has higher optimized proximity in a majority of parameter sets.

Positive rule: median paired ratio `P_opposite / P_same > 1.20` and >65% of cases favor opposite chirality.

### T3 — `same–reverse–same` is the preferred three-shell arrangement
Compare four adjacency patterns:
- `+++` all same
- `+-+` middle reversed
- `++-` outer reversed
- `-++` inner reversed

Triple attraction score is the sum of the two adjacent optimized proximities.

Prediction: `+-+` wins most often because both adjacent interfaces are counter-wound; edge-reversed patterns contain one counter-wound and one co-wound interface.

Positive rule: `+-+` is best in >60% of randomized cases and its median score exceeds the best edge-reversed score by >10%.

### T4 — repulsion does not produce the same preference
Use phase choices that minimize proximity.

Prediction: the strong `+-+` preference should weaken or reverse under repulsion.

Positive rule for attraction-specific behavior: the `+-+` win rate under attraction exceeds its repulsion win rate by >25 percentage points.

### T5 — opposite chirality creates recurring gates
A gate is a local minimum of the nearest adjacent-shell log-radius separation around polar angle. Count gates and measure angular-spacing regularity.

Prediction: opposite-chirality pairs produce more repeated local minima than same-chirality pairs and have lower coefficient of variation in gate spacing.

Positive rule: median opposite gate count >= 2x same-chirality count and median spacing CV is lower.

### T6 — attraction concentrates coupling into temporary throat/bundle zones
For the attraction-optimal phase, compute the fraction of angular rays with separation below one sigma and the concentration ratio `p95(proximity)/mean(proximity)`.

Prediction: counter-wound pairs show localized high-coupling zones rather than uniform overlap — a geometric analogue of temporary throat/bundling.

Positive rule: median concentration ratio >1.5 and greater than same-chirality concentration; median strong-coupling fraction <0.35.

### T7 — attraction changes preferred pitch under an elastic penalty
For one shell, scan pitch multipliers 0.70, 0.85, 1.00, 1.15, 1.30. Optimize phase at each pitch and subtract a fixed quadratic pitch-change penalty. Compare attraction and repulsion optima.

Prediction: attraction more often selects a non-unit pitch (changes turning) than repulsion.

Positive rule: attraction selects a non-unit multiplier at least 15 percentage points more often than repulsion. If not, attraction aligns shells but does not by itself explain spiral pitch in this toy model.

### T8 — 138 / 395 / 792 timing bridge
Take ordered gate radii from opposite-chirality attraction-optimal pairs. Where at least three usable radii exist, normalize three consecutive radii to the first and compare to `[1, 395/138, 792/138]`. Compare against a shuffled/null triplet drawn from the same radial range.

This is deliberately hard to pass because no timing constants enter the geometry.

Positive rule: median relative RMS error <10% and at least 25% lower than the null error. Otherwise the shell geometry does not derive the Archaix timing trio.

### T9 — Fibonacci / ammonite phi bridge
For consecutive gate radii, measure absolute log-ratio error to phi = 1.6180339887 and compare with a within-range null ratio.

Positive rule: median phi error at least 25% lower than null and median raw radius ratio lies within 5% of phi. Otherwise phi is not derived by the geometry.

### T10 — robustness to which handedness is called positive
Repeat all chirality comparisons with every sign flipped. Because handedness labels are arbitrary, results should be invariant.

Positive rule: aggregate metrics differ by <1e-9 except floating-point noise.

## Interpretation rules

- T2/T3/T5/T6 passing would support the geometry `same–reverse–same -> recurring localized gates` inside this toy model.
- T1 passing means attraction can supply an angular tendency; it does not prove a physical attractive field exists.
- T7 failing means attraction may align/bundle the shells without generating their pitch.
- T8 or T9 failing must be reported plainly; no post-hoc retuning of parameter ranges is allowed in v1.
- No mythology is used to score this run.
