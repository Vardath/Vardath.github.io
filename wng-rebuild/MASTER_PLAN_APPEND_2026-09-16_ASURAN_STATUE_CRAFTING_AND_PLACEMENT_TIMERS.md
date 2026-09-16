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
- The recipes appear on the ordinary Art Bench and use high-tech/nanite ingredients rather than generic stone-only sculpture costs.
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

The implemented first-balance recipes are:

1. `WNG_AsuranSleeperStatue` — 35 Plasteel, 1 Advanced Component (`ComponentSpacer`), 30 `WNG_AsuranNaniteSlurry`, 100 Silver; Artistic 6; 32,000 work.
2. `WNG_AsuranFeederStatue` — 40 Plasteel, 2 Advanced Components, 50 `WNG_AsuranNaniteSlurry`; Artistic 6; 36,000 work.
3. `WNG_AsuranReplicatorReliquary` — 50 Plasteel, 3 Advanced Components, 70 `WNG_AsuranNaniteSlurry`; Artistic 6; 42,000 work.

All three use the vanilla Art Bench (`TableSculpting`), require `WNG_PrecursorFabrication`, and may be crafted by any suitable pawn/faction after that research.

## 4. Continuity

D097/D098 remain historical valid checkpoints for the prior behavior. D099 intentionally supersedes their timer-start/provenance behavior without rewriting those archives.

The three statue identities remain otherwise unchanged:
- sleeper → one hostile human-form Asuran after 5–60 days;
- dark feeder → consumes nearby flesh in darkness after 5–20 days and leaves nanite slurry;
- Replicator reliquary → breaks into exactly five hostile autonomous Replicator Drones after 5–60 days.

Static/API validation remains evidence only until RimWorld live testing confirms Art Bench bill generation, first-placement timer initialization, minify/reinstall persistence and hostile transformations.

## 5. D099 implementation status — COMPLETE

Implemented as **D099 — Asuran statue crafting + first-placement timers**.

Technical boundary:
- no new mod files;
- two intentional edits only: `Defs/ThingDefs/Things_AsuranTrapStatues.xml` and `Source/WraithNaniteGravtech/Asurans/AsuranTrapStatues.cs`;
- creation/post-load paths no longer initialize hidden statue timers;
- first `PostSpawnSetup` initializes the relevant sleeper/reliquary deadline or feeder cycle;
- all existing serialized state still travels with the exact minified building;
- the Replicator reliquary still stages exactly five real hostile Drones with one shared autonomous domain and rollback on incomplete placement.

Focused static/API contract: **62/62 PASS**. Sealed archive verification: **708/708 byte-identical**.

Restore archive: `WNGv1-CHECKPOINT-20260916-ASURAN-STATUE-CRAFTING-PLACEMENT-TIMERS-COMPLETE.zip`  
SHA-256: `6301942e6ded7e22ef805a936d094a5172b3e8afa390b0f0ebd4b8f0ba2130bc`.

Managed compile, native Def loading, actual Art Bench bill generation, crafted-statue minification, first placement, save/load and hostile execution remain runtime test debt.