# WNG — CURRENT PUBLIC STATE

Updated: **2026-09-11**  
Author/final design authority: **Vardath**

# PURPOSE

This is the **mutable live-state supplement** to `CANONICAL_RECOVERY_LEDGER.md`. The canonical ledger preserves the one-time historical reconstruction and its original implementation snapshot; this file records what public WNG actually contains now.

Mandatory reset recovery order:
1. `STANDING_RULES.md`;
2. all of `CANONICAL_RECOVERY_LEDGER.md`;
3. all of this file;
4. `WNG_IMPLEMENTATION_CHECKLIST.md`;
5. fetch current public mod `main` and compare it with the HEAD below;
6. inspect any newer commits before coding;
7. active subsystem contracts/plan appends;
8. `PLAN_EXECUTION_PROTOCOL.md`;
9. update this live state before handoff.

Current public `main` always beats stale checkpoint/"next" prose.

---

# CURRENT MOD HEAD

Repository: `Vardath/Wraith-Nanite-Gravtech-1.6`

**`0e5dfc893a8efec624053e677ae99d6983c25fc9` — `cleanup: remove temporary Neural Lattice validation workflow`**

Recent major implementation milestones after the canonical-ledger snapshot include:
- Ha'tak native gravship family, heavy plasma battery, real Death Glider, exact System-Lord/Jaffa strikes, landed hostile carrier site and true cross-map/orbital bombardment;
- human-form Replicator/Asuran nanite physiology using native `Need_Food` as Nanite Reserve;
- one exact persistent age-13 female Replicator Queen in a real cryptosleep vault;
- hardened physical four-operative Asuran Queen recovery/capture layer;
- genuine exact-Queen controller-domain sovereignty over real block Replicators;
- **physical Sovereign Neural Lattice implant and bounded non-Queen controller-domain authority**.

The ledger's original `4af4f60...` state is historical only.

---

# GLOBAL CONTENT / OWNERSHIP RULES

WNG requires the complete current RimWorld DLC set:
- Royalty;
- Ideology;
- Biotech;
- Anomaly;
- Odyssey.

Use a DLC system only where it actually models the Stargate/WNG function; the dependency does not require checkbox content.

Third-party Stargate ecosystem mods remain optional unless Vardath changes this:
- CatCraft Stargates! — owns gate network/address/dial/iris/receive-buffer mechanics;
- ONAC — owns its Goa'uld resources/systems including `ONAC_LiquidNaquadria` and tretonin/tritonin content;
- RimGate Jaffa Biotech — owns its Jaffa/System-Lord identities.

Do not duplicate externally owned factions/resources. Do not invent uranium/chemfuel or another unspecified Goa'uld fallback. **Al'kesh exists and stays.**

---

# CURRENT IMPLEMENTATION

## Block Replicators

Implemented foundation includes:
- physical hierarchy `Drone -> Hunter -> Bulwark -> Titan -> Siege Mass`;
- genuine destruction breaks larger forms downward instead of making them disappear;
- split-born recombination lockout remains tunable;
- specialist Controller, Repairer, Burrower and Artillery bodies;
- cumulative Material/Armor/Ranged/Power/Shield/Grav/AntiShield adaptation state;
- adaptation overlays, ranged adaptation, armor mitigation, power-assisted regeneration, adaptive shield behavior and repeated-evidence anti-shield state;
- assimilation and stored-matter reproduction economy;
- dangerous Replicator Matter reassembly;
- population bounds;
- EMP suppression;
- powered Replicator containment;
- local retaliation;
- Child's Toy player-mech branch and feral conversion to a real hostile Drone.

Block Replicators **do not use Food/Nanite Reserve**. Their stored matter remains a separate mass/reproduction/construction/adaptation economy.

### Live controller-domain architecture

Every real WNG block body inherits `CompReplicatorSovereignty`. Authority identities are separate:
- `None` — autonomous block domain;
- `Queen` — exact Replicator Queen innate authority;
- `NeuralLattice` — physical Sovereign Neural Lattice implant bearer;
- `TemporaryAsuran` — reserved for the next temporary-intrusion layer.

Controlled blocks store the exact controller pawn reference, original faction, control faction, domain key and authority metadata. Real faction ownership changes; this is not an aura/outbreak modifier/proxy system.

Domain identity is preserved through real split/recombine transactions with learned adaptations and stored matter. Different controller domains cannot recombine, coordinate Controller focus, receive Repairer support or share retaliation merely because faction matches.

EMP and active Replicator containment interfere with real controller authority rather than being bypassed. Controlled blocks expose dedicated move/attack/repair/breach/recombine/release commands without pretending vanilla mechanitor control exists.

## Exact Queen sovereignty

Implemented:
- authority belongs only to the exact persistent Queen pawn;
- same-map or same-caravan physical-presence validity;
- real faction transfer of exact controlled blocks;
- exact-target acquisition plus bounded nearby swarm seizure;
- current Def-driven first-build tuning: 40-cell direct acquisition, 24-cell local-swarm acquisition, 12 normal controlled bodies;
- invalid physical/controller state releases/restores authority;
- EMP/containment suppress control;
- existing-save maintenance ensures the exact Queen sovereign Hediff.

Queen sovereignty validation run **34576583840** passed C# build, all Def/Patch XML parsing and domain invariants. Temporary workflow was removed. Live RimWorld validation remains pending.

## Sovereign Neural Lattice — IMPLEMENTED

`Sovereign Neural Lattice` is a **WNG-specific Stargate-derived extrapolation**, not a canon-named implant. Its basis is demonstrated Replicator command architecture: Reese directly commanded her Replicators; commands embedded in her could be exploited; later human-form Replicators commanded block forces.

Implemented now:
- tangible `WNG_SovereignNeuralLattice` health item;
- dedicated research requiring both `WNG_ReplicatorStudy` and `WNG_AsuranFabrication`;
- fabrication only at `WNG_AsuranWorkshop` from a real Replicator Core Fragment, `WNG_NaniteSludge`, plasteel and advanced components;
- native brain installation with `Recipe_InstallImplant`;
- native removal with `Recipe_RemoveImplant`, returning the physical item through `spawnThingOnRemoved`;
- non-Queen bearer gets exact-target `NeuralLattice` authority using the same real `CompReplicatorSovereignty` persistence/domain architecture;
- exact Queen is not converted into a second implant domain; her innate Queen authority remains distinct;
- current Def-driven first-build tuning: **24-cell acquisition range, 3 normal controlled bodies, 1,800-tick EMP signal disruption**;
- no Queen-style nearby-swarm seizure command;
- ongoing validity uses the existing same-map/same-caravan physical-presence rule; the 24-cell value is acquisition range, not an automatic ownership-breaking leash;
- split/recombine conserves the exact implant-controller domain;
- new acquisitions stop at the normal cap, while genuine destruction split can temporarily create more valid same-domain bodies because controller identity is conserved;
- implant EMP disruption and Replicator containment block/suppress commands;
- removal releases the exact bearer's Neural-Lattice domain.

Initial validation run **34580535936** exposed one real compile defect: direct access to protected `Gizmo.disabled`. It was corrected to RimWorld's public `Command.Disable(...)` API.

Corrected run **34580647197** then passed:
- WNG C# build — SUCCESS;
- all Def/Patch XML parse — SUCCESS;
- physical item/Hediff/research/fabrication/install/remove wiring checks — SUCCESS;
- Neural-Lattice controller-domain/hierarchy checks — SUCCESS.

Temporary workflow was removed before promotion. **No live RimWorld validation is claimed.** Final dedicated lattice art remains unfinished; current item graphic is explicitly a vanilla mechanics placeholder and no replacement art was generated.

## Human-form Replicators / Asurans / exact Queen

Implemented:
- `WNG_NaniteHumanoid` physical xenotype identity;
- ordinary Lattice Operative/Technician/Commander roles remain separate from Queen identity;
- hidden hostile `WNG_AsuranLattice` foundation;
- native Food behavior repurposed as visible **Nanite Reserve** for human-form nanite bodies only;
- ordinary edible matter refills that reserve through native eating/caravan behavior;
- normal need drain represents matter consumption; repair/fabrication spend the same reserve;
- synthetic depletion replaces biological starvation consequences, with same-tick Malnutrition cleanup;
- EMP disrupts self-repair/lattice behavior;
- current human-form body is ageless/sterile synthetic physiology foundation;
- exact persistent female Queen, age 13;
- real neutral vault and vanilla `CryptosleepCasket`;
- exact release recruits her immediately;
- all-or-nothing four-operative nonlethal Asuran recovery mission;
- exact physical Asuran recovery Jumper;
- capture commits only when the exact Queen physically leaves the map inside that exact shuttle transit container, then enters the exact Asuran faction's native kidnapped-pawn tracker.

Still later: broader Neural Interface copy/reconstruction, infiltration, recurring recovery, captured-Queen consequences and mixed human-form/block hostile compositions.

## Wraith

Implemented public foundation includes:
- one Wraith xenotype with Hunter/Warrior/Commander/Keeper/Queen caste PawnKinds;
- pale/white Wraith hair handling;
- Life Force, Drain Life/Partial Feed, regeneration, hibernation/torpor;
- four lineage factions: Sable Brood, Cinder Court, Veiled Hive, Pale Covenant;
- strategic faction hunger/request/raid pressure;
- exact-pawn captivity/rescue;
- Mature-Hive active/dormant/feeding-stock ecology, Feeding Niches, Hibernation Pods, Dormancy Vault, Hive Heart and retaliation;
- living-tech bootstrap and Wraith Grav **Engine** path;
- ranged nonlethal Wraith stun staff;
- Wraith Dart culling/abduction/captive continuity and native craft/retreat foundations;
- Odyssey-native Wraith gravship family with living-hull regeneration.

Critical separation remains mandatory: ordinary Drain Life, strategic faction hunger, Mature-Hive local feeding ecology and Mature-Hive retaliation are four separate systems.

## Craft / gravships / Stargate integration

Current native/Odyssey craft stack includes Wraith Dart, Wraith scout/strike craft, Wraith cruiser, Puddle Jumper, **Al'kesh**, Death Glider and Asuran recovery Jumper where applicable. CatCraft retains gate-system ownership.

Wraith, Asuran and Goa'uld/Ha'tak gravship families use real Odyssey-native GravEngine/hull/substructure behavior with family isolation rather than fake replacement engines.

## Goa'uld / Ha'tak

Implemented:
- Goa'uld gravship research and native Odyssey engine/hull/substructure family;
- pel'tac, native-direction thrusters, field projector, shield, power core, power/fuel networks;
- ONAC liquid-Naquadria integration when ONAC exists;
- heavy plasma battery;
- real two-seat Death Glider using native shuttle/transport/launch mechanics and physical combat passes;
- verified System-Lord/Jaffa hostile Death Glider strikes;
- landed hostile Ha'tak carrier world site with real native gravship engine/hull/facilities, Jaffa defenders and physically parked crewed Gliders;
- true player cross-map/orbital bombardment from a real powered Ha'tak battery on an Odyssey Orbit map into a distinct generated Surface map using Royalty's native `Bombardment` Thing.

### Hostile Ha'tak native blocker

Odyssey's native traveling gravship path stores the active gravship through the player-oriented singleton `Current.Game.Gravship`. Driving an independent hostile Ha'tak through that path risks corrupting/overwriting the player's gravship state. Therefore genuine hostile takeoff/retreat/pursuit is **not implemented and must not be faked** through deletion/proxy replacement.

---

# APPROVED PLANNED CONTENT — NOT CURRENTLY IMPLEMENTED

The newer planning appends remain authoritative planned work, including:
- Anomaly handling of Wraith/Iratus xenobiology, Whispers-type fog/hearing experiments, intelligent human-Wraith hybrids, Bug People, unstable transformations, containment/study and laboratory/village sites;
- real Iratus bug animals with rare wild ecology, physical neck attachment/paralysis/feeding, salt-water-assisted removal and Iratus queens;
- Wraith diplomacy/client states/worshippers/tributaries and faction-specific relationship development;
- Royalty-based Wraith telepathy/court/favour concepts where native mechanics fit;
- Ideology precepts/rituals/roles around feeding, hybridisation, xenobiology, Wraith patronage, synthetic life, nanites, Goa'uld hosts, Ancient technology and Stargates;
- Wraith/Iratus pharmacology: raw/refined enzyme, weaning serum, life-enzyme emergency medicine, Iratus paralytic/rejection agent/Queen restorative, hybrid stabiliser, retrovirus/suppression cocktail, gene therapy and Hoffan serum;
- **Kassa as a farmable, nutritionally sufficient staple crop/food that is extremely addictive**;
- Reol secretion and possible Goa'uld pheromonal-control content later;
- tretonin/tritonin remains ONAC-owned and must not be duplicated.

These planning branches do not override the immediate implementation order unless Vardath explicitly reprioritizes them.

---

# CURRENT REQUIRED UNFINISHED BRANCHES

1. **Temporary Asuran lattice intrusion** — current next slice. It must use `TemporaryAsuran`, remain distinct from Queen/implant authority, expire, and restore the exact prior controller/faction/domain rather than simply dropping to autonomous state.
2. Recurring Queen recovery attempts on whichever player map physically contains the exact Queen.
3. Captured-Queen hostile sovereign consequences and mixed Asuran + controlled-block threat composition.
4. Human-form infiltration / broader Neural Interface copy-reconstruction system.
5. Hostile Ha'tak genuine takeoff/retreat/pursuit only if the Odyssey singleton problem can be solved safely; do not fake it.
6. Safe standalone Goa'uld resource/research route when ONAC is absent; do not invent fuel/material substitutes.
7. Final deliberate Ancient/Puddle-Jumper power/fuel abstraction.
8. Later concrete Grav-adaptation/cross-system anti-shield refinements.
9. Approved Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa branches above.
10. Professional final art/audio/rotation/connection-state audit.
11. Broad **live RimWorld validation** of the fresh public build.

---

# NEXT ACTUAL SLICE

Implement **temporary Asuran lattice intrusion** on top of the now-live controller-domain architecture.

Required boundary:
- use `ReplicatorControlAuthority.TemporaryAsuran` rather than Queen or `NeuralLattice`;
- it is a temporary override, not a permanent acquisition technology;
- record enough prior authority state to restore the exact pre-intrusion controller/domain/faction when the intrusion expires or is broken;
- do not destroy Queen/implant ownership metadata merely because an Asuran temporarily hijacks a block;
- EMP/containment remain real interference;
- exact duration/range/cap/trigger rules must be author-tunable;
- hierarchy transactions during an active intrusion must not duplicate, lose or cross-contaminate controller state;
- no ordinary Asuran gets permanent Queen authority merely because the faction shares human-form nanite physiology.

After that, derive the next slice from actual public `main`, not this prose.

---

# VALIDATION BOUNDARY

Static/API/CI checks establish source/Def sanity only. **Live RimWorld testing has not been performed in this environment unless explicitly recorded from an actual game/log.** Never report static validation as live-game validation.
