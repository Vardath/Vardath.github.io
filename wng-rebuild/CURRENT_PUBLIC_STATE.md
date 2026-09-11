# WNG — CURRENT PUBLIC STATE

Updated: **2026-09-11**  
Author/final design authority: **Vardath**

# PURPOSE

This is the **mutable live-state supplement** to `CANONICAL_RECOVERY_LEDGER.md`.

The canonical ledger preserves the one-time history reconstruction and its original implementation snapshot. It is intentionally not rewritten to pretend later work existed at ledger creation. This file records what the public rebuild actually contains **now**.

Mandatory recovery rule after a context reset:

1. read `STANDING_RULES.md`;
2. read all of `CANONICAL_RECOVERY_LEDGER.md`;
3. read **this file**;
4. read `WNG_IMPLEMENTATION_CHECKLIST.md`;
5. fetch current public mod `main` and compare it with the HEAD below;
6. if `main` advanced, inspect those commits/files before coding and update this file;
7. then read the active subsystem contract(s) and `PLAN_EXECUTION_PROTOCOL.md`.

Current public `main` always beats stale checkpoint prose.

---

# CURRENT MOD HEAD

Repository: `Vardath/Wraith-Nanite-Gravtech-1.6`

**`f2becbde25bf58e5e026d5ee5270ce8c5d08f2c3` — `feat: add true Ha'tak orbital bombardment`**

Recent Goa'uld/Ha'tak state-changing commits after the canonical-ledger snapshot include:

- `647fa984a6383a7fa85ec753c5393294f45fe728` — Ha'tak heavy plasma battery;
- `0ce8830238eb5844208084dc5f4565b9aaa7333c` — real Ha'tak Death Glider fighter;
- `ef04575fb88ed6300b7c681c32971eec0c98d253` — exact System-Lord/Jaffa Death Glider strikes;
- `9c78be450aebedbc94b6e279bbd761c91bc63baf` — landed hostile System-Lord Ha'tak carrier site;
- `f2becbde25bf58e5e026d5ee5270ce8c5d08f2c3` — true cross-map/orbital Ha'tak bombardment and full-RimWorld-DLC dependency correction.

The old ledger statement that the Ha'tak family was not implemented is historical snapshot state only.

---

# GLOBAL RIMWORLD CONTENT REQUIREMENT

Vardath explicitly requires WNG 1.6 to depend on the **complete RimWorld DLC set**:

- Royalty;
- Ideology;
- Biotech;
- Anomaly;
- Odyssey.

WNG does not have to force every subsystem to use every DLC, but the rebuild may use the most appropriate native mechanic from any of them. `About/About.xml` now declares all five DLCs as hard dependencies.

Third-party Stargate ecosystem mods remain optional unless Vardath changes that:
- CatCraft Stargates!;
- ONAC;
- RimGate - Jaffa, Kree! (Biotech).

---

# CURRENT BROAD IMPLEMENTATION STATE

## Block Replicators

Current public source/Defs contain the fresh block-Replicator ecology: hierarchy and genuine split/recombine behavior, specialist roles, cumulative material/adaptation state, assimilation and physical map-cell consumption, regeneration/EMP suppression, retaliation, dangerous loose blocks, containment, population limits, salvage/matter economy and Child's Toy foundations.

Required later branches remain the human-form/Asuran sovereign layer, Queen story/capture layer, richer player sovereignty/control and mixed human-form + block threats.

## Wraith

Current public source/Defs contain Wraith xenotype/castes/factions; Life Force, Drain Life, regeneration and hibernation; strategic faction hunger; Mature-Hive feeding ecology/retaliation; exact captivity/rescue foundations; living-tech bootstrap; stun staff; native-boardable Dart/scout/cruiser craft; and the Odyssey-native Wraith gravship family with living-hull regeneration.

Ordinary Drain Life, strategic faction hunger, Mature-Hive local feeding and Mature-Hive retaliation remain separate systems.

## Asuran / Ancient-derived

Current public source/Defs contain Asuran Nanite Reserve/fabrication/workshop foundations and an Odyssey-native Asuran gravship family with themed native GravEngine/hull/substructure, nanite-sludge fuel family, power/fuel networks, shield and supporting Odyssey equivalents. Puddle Jumper remains a real native-boardable shuttle.

Human-form Replicator/Asuran infiltration, Neural Interface, exact Queen and sovereign/capture layer remain required and unfinished.

## Stargate / shuttle integration

Current WNG shuttles use the complete native RimWorld/Odyssey player-shuttle stack wherever applicable. CatCraft Stargates! owns its network/dial/direction/iris/receive-buffer mechanics. WNG integrates around it.

Al'kesh remains implemented and required.

## Goa'uld / Ha'tak — CURRENT

The Ha'tak family is now a substantial Odyssey-native gravship branch. Current public content includes:

- `WNG_GoauldGravships` research;
- Goa'uld engine seed converting into Odyssey's exact native `GravEngine` with `Goauld` runtime theme;
- Goa'uld native gravship substructure;
- hull seed converting into exact native `GravshipHull` with Goa'uld runtime theme;
- pel'tac using native `CompPilotConsole` behavior;
- ONAC liquid-Naquadria tanks and fuel network;
- directional native gravship thrusters;
- gravitic field projector;
- native Odyssey energy shield;
- naquadah power core and native power network;
- heavy plasma battery for local gravship combat;
- real two-seat native-shuttle Death Glider with ONAC fuel, exact loaded crew, physical staff-cannon attack passes, return-to-deck behavior and hacking/capture;
- bounded hostile Death Glider strikes bound only to verified existing Apophis/Anubis/Ra factions and exact RimGate Jaffa PawnKinds;
- real landed hostile Ha'tak carrier site built from the exact native GravEngine/GravshipHull plus actual Goa'uld WNG facilities, exact Jaffa defenders and physically parked crewed Death Gliders;
- bounded defensive Glider sorties from the carrier deck;
- true player-controlled cross-map/orbital bombardment from the exact physical heavy plasma battery when it is powered, on connected Goa'uld substructure, and the source map is Odyssey `Orbit`;
- orbital targeting selects a different generated Surface-layer `MapParent`, then an exact impact cell on that target map;
- the target receives Royalty's exact native `Bombardment` Thing, configured from author-tunable WNG Def values;
- no same-map turret shot/local explosion is relabeled as orbital fire.

ONAC/RimGate ownership is preserved. Do not create duplicate Goa'uld/Jaffa factions or duplicate `ONAC_LiquidNaquadria`.

---

# CURRENT REQUIRED UNFINISHED BRANCHES

These remain required unless Vardath changes them:

1. **Human-form Replicator / Asuran layer** — infiltration, Neural Interface, exact Queen, sovereign/capture consequences and mixed human-form/block integration.
2. **Hostile Ha'tak world behavior** — genuine takeoff/retreat/pursuit and hostile use of orbital fire through real Odyssey/world mechanics; do not replace the landed ship with an abstract proxy merely to claim that it moved.
3. **Goa'uld sensors/other Odyssey equivalents** only where Stargate function actually justifies them.
4. **Bombardment of otherwise-unloaded settlements/sites** only if map generation/consequences can be handled without pretending damage occurred on a nonexistent map.
5. **Safe standalone Goa'uld resource/research path** when ONAC is absent remains unresolved. Do not invent uranium/chemfuel.
6. **Final Puddle Jumper/Ancient power-fuel abstraction** remains deliberate future work.
7. **Professional final art/audio pass** — dedicated faction assets, all rotation/connection/corner states, Ha'tak/Death-Glider visuals, shield/VFX/audio, Wraith/Asuran production assets.
8. **Broad live RimWorld validation** — source/API/static reasoning is not live gameplay validation.

---

# NEXT ACTUAL SLICE

After `f2becbde...`, the active Ha'tak mechanical slice is:

**Reconcile hostile Ha'tak takeoff/retreat/pursuit and hostile orbital-fire behavior using genuine Odyssey gravship/world mechanics.**

Before coding:
- inspect the actual RimWorld 1.6 `Building_GravEngine`, pilot-console launch flow, gravship map transfer, leaving skyfaller/world-object behavior and orbit-layer destination mechanics;
- preserve the exact generated hostile carrier ship and physically loaded Death Gliders;
- use only the verified external System-Lord/Jaffa factions/crew;
- do not destroy the landed carrier and manufacture a replacement proxy merely to simulate takeoff;
- if native hostile/AI launch cannot be driven safely, record the exact missing native boundary and move to another required branch rather than faking it.

---

# VALIDATION STATUS

Current Ha'tak work has been source/API checked against current RimWorld 1.6 classes and Def patterns, including Odyssey gravship/world-layer APIs and Royalty orbital bombardment. No claim is made that RimWorld itself has been launched in this environment.

Live validation still required includes Def load, ONAC/RimGate integration, carrier-site generation, power/fuel/facility links, shields/turrets, Death Glider launch/return, gravship launch/travel, orbital world/cell targeting, native bombardment impacts and save-load.

---

# HANDOFF MAINTENANCE

After every meaningful implementation batch:
- update the exact mod HEAD above;
- state exactly what changed;
- move completed requirements out of unfinished state;
- record live-test-needed status honestly;
- derive the next slice from actual current `main`;
- never make Vardath reconstruct already-settled project state from raw chat again.
