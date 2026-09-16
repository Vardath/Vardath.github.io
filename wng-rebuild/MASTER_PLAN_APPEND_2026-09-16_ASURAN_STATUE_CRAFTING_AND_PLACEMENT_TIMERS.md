# WNG Master Plan Append — Asuran Statue Crafting + Placement-Start Timers

Date: **2026-09-16**  
Design authority: **Vardath**  
Status: **ACTIVE OVERRIDE FOR THE ASURAN STATUE BRANCH.**

This append supersedes earlier wording that made the three trap statues Asuran-worker-only/source-only or started hidden timers at object creation/trade generation.

## 1. Crafting ownership rule

All three Asuran-derived trap statues are now **research-gated technology, not biologically locked manufacture**.

- After the colony completes the appropriate Asuran fabrication research, any faction/pawn that can legitimately use an Art Bench, meets the recipe skill/material requirements, and has access to the research may craft them.
- Do **not** require the worker to be an Asuran xenotype, carry `WNG_NaniteBody`, or belong to the Quiet Lattice.
- Asuran traders may still sell the statues as before.
- The recipes should appear on the ordinary Art Bench and use appropriate high-tech/nanite ingredients rather than generic stone-only sculpture costs.
- Initial research gate: `WNG_PrecursorFabrication`, unless a later explicit Vardath decision introduces a more specific statue-fabrication project.

## 2. Timer-start rule — newest authority

For all three statues, the hidden dangerous cycle **starts when the exact statue is first actually placed/installed on a map**, not when it is manufactured, generated in trader stock, bought, sold, or sitting minified in storage.

### Sleeper / awakening statue
- First placement rolls one hidden 5–60 day awakening deadline.
- Manufacturing/trading/minified storage before first placement carries no active countdown.
- If later minified after the countdown has started, the saved deadline remains attached to that exact statue; it cannot awaken while minified.
- If the deadline passes while minified, it resolves when the same statue is next placed/spawned.

### Dark-feeder statue
- First placement initializes one 5–20 day feeding-cycle target.
- Only time spent installed in sufficiently low light advances the feeding progress.
- Bright light pauses it.
- Minification pauses it while preserving accumulated dark-time progress and the same cycle target.
- After a successful feeding, the installed statue rolls the next 5–20 day cycle as already designed.

### Replicator reliquary statue
- First placement rolls one hidden 5–60 day release deadline.
- Manufacturing/trading/minified storage before first placement does not start the timer.
- If later minified, the existing deadline is preserved but cannot release Replicators while packed.
- If mature while minified, it waits until next placement and then attempts the same transactional five-Drone release.

## 3. Art Bench recipes

Add one recipe per statue to the Art Bench:

1. `WNG_AsuranSleeperStatue` — high-quality lattice sculpture with nanite and spacer fabrication components.
2. `WNG_AsuranFeederStatue` — heavier nanite-bioconversion content because it repeatedly consumes flesh into slurry.
3. `WNG_AsuranReplicatorReliquary` — highest nanite/spacer cost because it contains enough dormant Replicator structure to unfold into five real Drones.

Exact quantities are balance parameters, but all three should require `WNG_AsuranNaniteSlurry`, advanced/spacer components and durable advanced material such as Plasteel. They should require Artistic work at the vanilla Art Bench and `WNG_PrecursorFabrication` research.

## 4. Continuity

D097/D098 remain historical valid checkpoints for the prior behavior. The next checkpoint must intentionally modify the three existing statue Defs and statue comp code to implement this override; it must not silently rewrite the old checkpoint archives.

The three statue identities remain otherwise unchanged:
- sleeper → one hostile human-form Asuran after 5–60 days;
- dark feeder → consumes nearby flesh in darkness after 5–20 days and leaves nanite slurry;
- Replicator reliquary → breaks into exactly five hostile autonomous Replicator Drones after 5–60 days.

Static/API validation remains evidence only until RimWorld live testing confirms Art Bench bill generation, first-placement timer initialization, minify/reinstall persistence and hostile transformations.