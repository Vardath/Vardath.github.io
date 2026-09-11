# WNG — CURRENT PUBLIC STATE

Updated: **2026-09-11**  
Author/final design authority: **Vardath**

This is the mutable live-state supplement to `CANONICAL_RECOVERY_LEDGER.md` and `PUBLIC_RECONCILIATION_2026-09-11.md`.

**Current public source is implementation truth. Private/old work is reference evidence only. There are no known-good historical builds.**

## Mandatory recovery order

1. `STANDING_RULES.md`;
2. all of `CANONICAL_RECOVERY_LEDGER.md` for recovered history/design;
3. all of `PUBLIC_RECONCILIATION_2026-09-11.md`;
4. all of this file;
5. `WNG_IMPLEMENTATION_CHECKLIST.md`;
6. fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main` and compare it with the HEAD below;
7. inspect every newer commit before coding;
8. read active subsystem contracts/plan append(s);
9. follow `PLAN_EXECUTION_PROTOCOL.md`;
10. update this live state before handoff.

---

# CURRENT PUBLIC MOD HEAD

Repository: `Vardath/Wraith-Nanite-Gravtech-1.6`

**`26680fe84b95a0bfd5a23841b714fdba9cde1a98` — temporary Asuran lattice intrusion implementation/checkpoint landed on public `main`.**

The original canonical implementation snapshot `4af4f60...` is historical only and substantially behind current public source.

## Most recent completed slice — Temporary Asuran lattice intrusion

Status: **IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED**.

Public now contains:
- `WNG_AsuranLatticeLink` on `WNG_NaniteHumanoid`;
- hostile automatic use restricted to the exact hostile `WNG_AsuranLattice` faction;
- Def-tunable current first-build range 18, duration 2,500 ticks, cap 3, 600-tick AI check and 0.65 attempt chance;
- `TemporaryAsuran` authority now performs a real temporary controller transaction instead of an empty enum reservation;
- exact pre-intrusion authority/controller/original faction/control faction/domain snapshot;
- active temporary domain keyed by both exact Asuran intruder identity and exact restoration-domain identity;
- no merging of blocks that came from different Queen/Neural-Lattice/autonomous domains merely because the same Asuran hacked them;
- exact temporary/restoration state copied through hierarchy split/recombine via the existing `CopyAuthorityFrom` transaction path;
- save/load persistence for active intrusion and suspended authority metadata;
- timeout, intruder death/downing, physical separation, EMP and containment interrupt the intrusion;
- expiry/interruption restores the exact suspended Queen/Neural-Lattice/autonomous state when still valid, otherwise falls back through normal recorded-faction/autonomous release behavior;
- ordinary/recruited/player-aligned nanite humanoids do not silently auto-hijack blocks;
- ordinary Asurans still do **not** receive permanent Queen sovereignty.

Validation:
- temporary public branch workflow run **34590952017** passed `dotnet build Source/WNG/WNG.csproj -c Release`;
- all current Def/Patch XML parsed successfully;
- temporary validation workflow was removed before public `main` was fast-forwarded;
- checkpoint: `Docs/WNG_TEMPORARY_ASURAN_INTRUSION_CHECKPOINT_2026-09-11.md`;
- this is source/Def validation, **not live RimWorld validation**.

---

# CURRENT IMPLEMENTED FOUNDATIONS

## Block Replicators

Implemented foundation:
- `Drone -> Hunter -> Bulwark -> Titan -> Siege Mass` upward hierarchy and real downward destruction breakup;
- split-born recombination lockout;
- Controller, Repairer, Burrower and Artillery specialists;
- stored-matter assimilation/reproduction economy and bounded growth;
- dangerous Replicator Matter;
- EMP and powered containment;
- regeneration/local retaliation/terminal-consumption behavior;
- Child's Toy player branch;
- controller-domain-aware split/recombine/state inheritance;
- Material/Armor/Ranged/Power/Shield adaptation foundations;
- AntiShield persistent state/current Replicator-shield interaction;
- Grav learned/save-persistent state + visual overlay.

Still partial:
- richer Grav mobility/physical behavior;
- broader AntiShield interaction with concrete non-Replicator shield systems.

## Controller domains

Implemented:
- `None` autonomous;
- exact `Queen` authority;
- physical `NeuralLattice` implant authority;
- temporary restorable `TemporaryAsuran` intrusion.

Queen and implant remain separate exact controller identities. Temporary Asuran intrusion suspends/restores them rather than erasing them.

## Human-form Replicators / Asurans

Implemented foundation:
- `WNG_NaniteHumanoid`;
- native Food machinery presented/used as Nanite Reserve;
- synthetic depletion instead of ordinary malnutrition;
- reserve-powered reconstruction/fabrication;
- EMP disruption;
- Asuran workshop/fabrication;
- hidden hostile `WNG_AsuranLattice`;
- Operative/Technician/Commander roles;
- temporary lattice intrusion.

Still required:
- broader Neural Interface recruit/imprison/Ideology-enslave/copy/create-human-form system;
- exact copy/reconstruction preserving biography/name/skills/passions/XP/appearance/genome source data;
- real infiltration/impersonation/reveal;
- non-hostile Quiet Lattice;
- player human-form variants;
- broader role/faction composition and mixed human-form/block threats;
- native WNG backstories;
- complete synthetic disease/implant/temperature/vacuum physiology audit;
- final dedicated art/audio and live testing.

## Exact Replicator Queen

Implemented:
- one exact persistent female human-form Queen, current age 13;
- real precursor cryptosleep vault;
- immediate player recruitment on release;
- first all-or-nothing four-operative nonlethal Asuran recovery operation;
- exact physical Asuran recovery Jumper;
- capture commits only when the exact Queen physically exits in the exact hostile shuttle transit container;
- exact kidnapped-pawn persistence;
- genuine exact Queen block-Replicator sovereignty;
- physical Sovereign Neural Lattice exists separately from Queen authority;
- Temporary Asuran intrusion exists separately from both.

Still required:
- **recurring later recovery/capture operations targeting only the exact player map where the Queen is physically present**;
- no capture operation against another player map while Queen is traveling/off-map;
- captured-Queen consequences;
- genuine Asuran sovereign block access/mixed Asuran + block threats after successful capture;
- infiltration linkage.

## Wraith

Implemented foundation:
- one Wraith xenotype with Hunter/Warrior/Commander/Keeper/Queen castes;
- pale/white hair enforcement;
- Life Force, full Drain Life, Partial Feed, regeneration, hibernation/torpor;
- Sable Brood, Cinder Court, Veiled Hive, Pale Covenant;
- strategic faction hunger separated from ordinary feeding;
- exact captivity/rescue;
- Feeding Niche, Hibernation Pod, Dormancy Vault, Hive Heart;
- mature-Hive population/feeding-stock/retaliation foundation;
- living-tech bootstrap and real Wraith Grav Engine path;
- Wraith stun staff;
- Wraith Dart culling/captivity foundation;
- Wraith gravship mechanics and living-hull regeneration defense.

Still required:
- Wraith Growth Chamber;
- strategic hunger later UI stage showing involved-Wraith count/names;
- broader discovery/story progression;
- final presentation/audio/live testing.

Ordinary Wraith feeding, strategic faction hunger, mature-Hive local feeding ecology and mature-Hive retaliation remain four separate systems.

## Craft / Stargate integration

Mechanical foundations present:
- Wraith Dart;
- Wraith Strike/scout craft;
- Wraith Cruiser;
- Puddle Jumper;
- **Al'kesh**;
- Death Glider;
- Asuran recovery Jumper;
- Goa'uld transport rings;
- CatCraft/ONAC/RimGate ownership boundaries and verified package identities.

Still required/partial:
- friendly Quiet-Lattice/Puddle-Jumper Stargate courier path;
- deliberate Ancient/Puddle-Jumper power/fuel abstraction instead of temporary chemfuel;
- unloaded-world-site ring transport remains a later exact-world-object problem and must never use pawn recreation/proxies;
- broad live boarding/loading/fuel/launch/world/save-load validation;
- final distinct art/audio.

## Gravships / Goa'uld

Wraith and Asuran Odyssey-native mechanical gravship families are implemented with family-isolated fuel networks/pipes and appropriate parts. Wraith defense currently uses biological living-hull regeneration; the generic Wraith energy-shield reskin was rejected. Asuran uses a true powered native shield emitter.

Goa'uld/Ha'tak public foundation includes:
- Odyssey-native Ha'tak family;
- pel'tac/control, engine/hull/substructure, power/fuel network;
- heavy plasma battery;
- real two-seat Death Glider;
- verified System-Lord/Jaffa strikes;
- landed Ha'tak carrier site;
- real player cross-map/orbital bombardment.

Still required/blocked:
- safe standalone Goa'uld craft/gravship material/fuel/research route without ONAC — do not invent uranium/chemfuel fallback;
- hostile native Ha'tak takeoff/retreat/pursuit remains blocked by Odyssey's player-oriented gravship singleton and must not be faked;
- faction-specific professional hull corner/inside-corner/diagonal/transition presentation;
- final art/audio/live gravship testing.

---

# CURRENT REQUIRED UNFINISHED INVENTORY

Temporary Asuran intrusion is removed from this debt list because it is now implemented on public `main`.

1. **Recurring exact-map Queen recovery/capture operations.**
2. **Captured-Queen sovereign consequences + mixed Asuran/block threats.**
3. Human-form Neural Interface recruit/imprison/enslave/copy/create-human-form branch.
4. Human-form infiltration/impersonation/reveal.
5. Quiet Lattice non-hostile enclave, player human-form variants and broader human-form role/faction composition.
6. Native WNG backstories.
7. Richer block Grav adaptation and broader AntiShield integration.
8. Wraith Growth Chamber.
9. Strategic Wraith hunger involved-Wraith count/names UI stage.
10. Broader discovery/story progression.
11. Friendly Quiet-Lattice/Puddle-Jumper Stargate courier path.
12. Safe standalone Goa'uld craft/gravship material/fuel/research route when ONAC is absent.
13. Deliberate Ancient/Puddle-Jumper power/fuel abstraction.
14. Unloaded-world-site transport-ring exact-pawn/world-object transport; never fake via pawn recreation.
15. Faction-specific professional gravship corner/inside-corner/diagonal/transition presentation.
16. Final professional craft/gravship/implant/building/weapon/resource art review.
17. Professional WNG audio layer.
18. Hostile Ha'tak native takeoff/retreat/pursuit only if Odyssey ownership can be solved safely; never fake it.
19. Broad current-build live RimWorld/save-load/mod-stack/performance validation and tuning.
20. Approved planned-only Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty branches when Vardath advances them.

No item may silently disappear merely because another branch is worked first.

---

# GENUINE NEXT IMPLEMENTATION SLICE

**Recurring exact-map Replicator Queen recovery/capture operations.**

Required boundary:
- reuse the current exact Queen and existing physical recovery operation rather than creating a proxy/new Queen;
- target only the player map on which the exact Queen is physically spawned/present;
- no recovery raid against another player map while she is absent, traveling, caravanning or otherwise off that map;
- one recovery operation at a time;
- author-tunable interval/cooldown rather than another buried story-day constant;
- preserve exact nonlethal subdual/physical boarding/departure capture semantics;
- if the operation is interrupted before the exact physical departure boundary, the Queen remains recoverable/player-owned;
- save/load must not duplicate a scheduled/active operation;
- after this slice, implement the captured-Queen sovereign consequence/mixed-threat layer rather than replacing it with an outbreak-count modifier.

Live RimWorld validation remains required after source/Def implementation.