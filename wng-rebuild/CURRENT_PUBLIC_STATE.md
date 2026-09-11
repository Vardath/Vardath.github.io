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

**`ef04575fb88ed6300b7c681c32971eec0c98d253` — `feat: add System Lord Death Glider strikes`**

Recent state-changing Goa'uld/Ha'tak commits after the canonical ledger snapshot include:

- `277017be...` — Ha'tak gravship research;
- `26cbf24d...` — Ha'tak gravship substructure;
- `7220a08c...` — Ha'tak Odyssey gravship core family;
- `9111cbb9...` — Ha'tak liquid-Naquadria fuel pipes;
- `bbcc1a4a...` — Ha'tak native power conduits;
- `1ddd55cd...` — Ha'tak family linked into native Odyssey GravEngine;
- `f7342590...` — Ha'tak same-family fuel-pipe requirement;
- `647fa984a6383a7fa85ec753c5393294f45fe728` — Ha'tak heavy plasma battery;
- `0ce8830238eb5844208084dc5f4565b9aaa7333c` — real Ha'tak Death Glider fighter;
- `ef04575fb88ed6300b7c681c32971eec0c98d253` — exact System-Lord/Jaffa Death Glider strikes.

The old ledger statement that the Ha'tak family was not implemented is therefore **historical snapshot state only** and must not be used as current implementation state.

---

# CURRENT BROAD IMPLEMENTATION STATE

## Block Replicators

Current public source/Defs contain the fresh block-Replicator ecology: hierarchy and genuine split/recombine behavior, specialist roles, cumulative material/adaptation state, assimilation and physical map-cell consumption, regeneration/EMP suppression, retaliation, dangerous loose blocks, containment, population limits, salvage/matter economy and Child's Toy foundations.

Required later branches remain the human-form/Asuran sovereign layer, Queen story/capture layer, richer player sovereignty/control and mixed human-form + block threats.

## Wraith

Current public source/Defs contain:
- Wraith xenotype and caste PawnKinds;
- four Wraith factions;
- Life Force / Drain Life / regeneration / hibernation;
- strategic faction hunger and its feeding-request/raid-pressure system;
- Mature-Hive local feeding ecology, Hive Heart population, hibernation/dormancy, neutralization and retaliation;
- exact captivity/rescue foundations;
- living-tech bootstrap through living forge / grav-engine growth;
- Wraith stun staff;
- native-boardable Dart, scout craft and cruiser transport;
- Wraith Odyssey-native gravship family with living hull regeneration rather than a fake energy-shield reskin.

Ordinary Drain Life, strategic faction hunger, Mature-Hive local feeding and Mature-Hive retaliation remain separate systems.

## Asuran / Ancient-derived

Current public source/Defs contain Asuran Nanite Reserve/fabrication/workshop foundations and an Odyssey-native Asuran gravship family with themed native GravEngine/hull/substructure, nanite-sludge fuel family, power/fuel networks, shield and supporting Odyssey equivalents. Puddle Jumper remains a real native-boardable shuttle and its final deliberate power/fuel abstraction is still unfinished.

The human-form Replicator/Asuran infiltration, Neural Interface, exact Queen and sovereign/capture layer remain required and not yet implemented in the fresh public rebuild.

## Shuttles / Stargate integration

Current WNG shuttles use the complete native RimWorld/Odyssey player-shuttle stack wherever applicable. CatCraft Stargates! remains optional and owns its network/dial/direction/iris/receive-buffer mechanics. WNG adds Stargate-themed missions around that system without replacing it.

Al'kesh remains implemented and required.

## Goa'uld transport rings

Goa'uld transport rings are implemented as real powered transporter endpoints using native `CompTransporter` exact cargo/loading state. They do not require Stargate dialing. Their construction UI routes according to the current optional-integration rules; do not replace them with a Stargate proxy.

## Goa'uld / Ha'tak — CURRENT

The Ha'tak family **is implemented as an Odyssey-native gravship family**. Current public content includes:

- `WNG_GoauldGravships` research;
- Goa'uld engine seed converting into Odyssey's exact native `GravEngine` with `Goauld` theme;
- Goa'uld native gravship substructure;
- hull seed converting into exact native `GravshipHull` with Goa'uld runtime theme;
- pel'tac using native `CompPilotConsole` behavior;
- small/large ONAC `ONAC_LiquidNaquadria` reservoirs;
- small/large direction-sensitive native gravship thrusters;
- gravitic field projector;
- native Odyssey energy-shield generator behavior;
- naquadah power core on the ordinary RimWorld power net;
- visible/hidden liquid-Naquadria fuel pipes;
- visible/hidden native power conduits;
- same-family fuel-pipe enforcement and gravship-family isolation;
- powered on-map Ha'tak heavy plasma battery;
- real `WNG_GoauldDeathGlider` native shuttle fighter;
- physical Death Glider/Ha'tak carrier relationship: a real fighter parked on connected Ha'tak substructure is carried by Odyssey with the gravship, with no fake hangar inventory;
- Death Glider two-person combat crew requirement, paired physical staff-cannon passes, short no-hyperdrive range, ONAC fuel, return-to-origin/deck behavior and hacking support;
- bounded optional `WNG_GoauldDeathGliderStrike` using only exact verified existing System-Lord factions (`JKB_JaffaApophis`, `JKB_JaffaAnubis`, `JKB_JaffaRa`) and exact verified RimGate Biotech Jaffa warrior PawnKinds;
- hostile Glider strike uses exact craft/crew through the physical pass and real native shuttle withdrawal; failed withdrawal leaves the actual craft/crew on-map.

ONAC/RimGate ownership is preserved. Do not create duplicate Goa'uld/Jaffa factions or duplicate `ONAC_LiquidNaquadria`.

---

# CURRENT REQUIRED UNFINISHED BRANCHES

These are required unless Vardath changes them:

1. **Human-form Replicator / Asuran layer** — infiltration, Neural Interface, exact Queen, sovereign/capture consequences and mixed human-form/block integration.
2. **Hostile Ha'tak carrier encounter** — a real map/site/encounter path that physically stages a valid Ha'tak and its carried/deployed Death Gliders rather than relying only on the standalone edge-strike incident.
3. **True Ha'tak cross-map/orbital bombardment** — separate from the already implemented on-map heavy plasma battery; must reuse appropriate native Odyssey/world systems rather than faking an orbital label.
4. **Goa'uld sensors/other Odyssey equivalents** only where Stargate function actually justifies them.
5. **Safe standalone Goa'uld resource/research path** when ONAC is absent remains unresolved. Do not remove current ONAC gating or invent uranium/chemfuel to force a solution.
6. **Final Puddle Jumper/Ancient power-fuel abstraction** remains deliberate future work.
7. **Professional final art/audio pass** — dedicated faction assets, all rotation/connection/corner states, Death Glider/Ha'tak visuals, shield/VFX/audio, Wraith/Asuran production assets.
8. **Broad live RimWorld validation** — XML/static reasoning does not prove live gameplay. ONAC integration, incidents, gravships, launch/travel, save/load and exact-craft behavior still require real-game testing.

---

# NEXT ACTUAL SLICE

The next Ha'tak slice after `ef04575...` is:

**Reconcile and implement a real hostile Ha'tak carrier encounter/deployment path that can physically stage/deploy its exact Death Gliders.**

Before coding it:
- establish the Stargate role and encounter scale;
- inspect current Odyssey gravship/map-generation APIs and any native hostile/orbital gravship encounter grammar;
- preserve a genuinely valid connected native GravEngine/substructure/facility structure rather than spawning decorative Ha'tak props;
- use only existing verified external System-Lord/Jaffa factions/crew;
- preserve the exact physical Death Glider carrier model already implemented;
- if native mechanics cannot safely support the intended encounter in the first slice, record the concrete dependency rather than substituting a fake ship.

After that, the other current Ha'tak mechanical branch is true cross-map/orbital bombardment.

---

# VALIDATION STATUS

The recent Death Glider / hostile-strike implementation was structurally checked against APIs already used by current WNG (`CompTransporter`, `CompRefuelable`, exact-craft skyfallers, native `TransportShip` / `ShipJob_FlyAway`). The current environment has not run RimWorld itself. Do not call these features live-game validated until they are actually tested in RimWorld with the intended optional mods.

---

# HANDOFF MAINTENANCE

After every meaningful implementation batch:

- update the exact mod HEAD above;
- state exactly what changed;
- move completed requirements out of unfinished state rather than leaving stale contradictions;
- record live-test-needed status honestly;
- derive the next slice from actual current `main`;
- never make Vardath reconstruct already-settled project state from raw chat again.
