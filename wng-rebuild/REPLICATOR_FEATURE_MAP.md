# WNG — block Replicator feature map

Author/final design authority: **Vardath**.

This is the current reconciliation map for the clean RimWorld 1.6 rebuild. It is not immutable canon. Newer explicit Vardath instructions override it.

## Scope / identity boundary

This map covers the **mechanical block Replicator foundation**. Human-form Replicators/Asurans and the exact Replicator Queen are separate later identity layers, although their sovereign/control interfaces with block Replicators are tracked here as dependencies.

Specialist bodies and learned adaptations are separate from the physical size ladder.

## Retained assets — all accounted for

Body graphics under `Textures/Things/Pawn/Replicator/`:
- Drone/base
- Hunter
- Bulwark
- Titan
- Siege Mass
- Controller
- Repairer
- Burrower
- Artillery

Adaptation overlays under `Textures/Things/Pawn/Replicator/Adaptation/`:
- Armor
- Ranged
- Power
- Grav
- Shield

Resources under `Textures/Things/Item/Resource/Replicator/`:
- Replicator Matter
- Replicator Core Fragment

No replacement art is to be generated unless Vardath asks for it.

## Current public implementation snapshot

Fresh-rebuild implementation cleanup head after the latest verified block work:
- `94705ee8894b6659920178e19ea0ebe21555c7be`

The head must always be fetched again before future edits.

Current block source includes:
- `ReplicatorState.cs`
- `ReplicatorAssimilation.cs`
- `ReplicatorEMP.cs`
- `ReplicatorRegeneration.cs`
- `ReplicatorHierarchy.cs`
- `ReplicatorMatter.cs`
- `ReplicatorAdaptationEffects.cs`
- `ReplicatorSpecialists.cs`
- `ReplicatorContainment.cs`
- `ChildsToy.cs`

Current Defs include the full ladder, all four specialist bodies, Child's Toy, Replicator faction, jobs/ThinkTree, research/gestation, containment and Replicator resources.

## Complete relationship/status map

### Physical hierarchy — IMPLEMENTED

Upward recombination:

**Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass**

Downward genuine-destruction breakup:

**Siege Mass -> Titan -> Bulwark -> Hunter -> Drone/base**

Rules implemented:
- Drone/base is irreducible.
- combine counts/check timing are Def-tunable;
- genuine destruction creates operational lower forms rather than making large forms vanish;
- intentional upward recombination consumption does not trigger death splitting;
- split-born children receive the tunable ~2,500-tick / ~1 in-game hour recombination lockout;
- the lockout exists specifically for combat playability so killing a Titan/Siege Mass does not immediately recreate the same threat and appear immortal;
- learned state and stored matter survive hierarchy transactions appropriately;
- stored matter sums upward and is divided among genuine-death children rather than being duplicated or lost.

Later sovereign-control identity transfer remains a dependency of the later Queen/control layer, not a missing block-hierarchy mechanic.

### Controller — IMPLEMENTED

Controller is a specialist coordination body, not a size-ladder rung and not equivalent to Queen/implant sovereign control.

Implemented behavior:
- finds nearby same-faction autonomous Replicators;
- provides a shared hostile focus;
- respects faction/control boundaries;
- stops active coordination behavior under EMP;
- ordinary Replicators still function without a Controller.

### Repairer — IMPLEMENTED

Implemented behavior:
- seeks damaged same-faction block Replicators;
- prioritizes more seriously injured allies;
- moves into repair range and heals damage;
- does not repair hostile Replicators merely because they are Replicators;
- stops active repair under EMP.

### Burrower — IMPLEMENTED

Implemented behavior:
- breaches hostile structures;
- prioritizes the WNG Replicator containment projector first;
- then prioritizes access blockers such as doors/gates/bulkheads, walls and barricades;
- generic hostile buildings are fallback targets;
- can attack eligible factionless access blockers where necessary;
- respects ownership/hostility and EMP rules.

This is the current first-build tactical implementation and remains tunable/refinable through testing.

### Artillery / siege support — IMPLEMENTED

Implemented behavior:
- real long-range support attack;
- Def-tunable minimum/maximum range, warmup, damage and armor penetration;
- operates as a ranged support specialist rather than a melee pawn with an Artillery label;
- respects hostility/control boundaries and EMP.

### Assimilation and matter economy — IMPLEMENTED FOUNDATION

Implemented behavior:
- autonomous hostile Replicators search for accessible assimilable matter/technology;
- useful technology is prioritized above arbitrary nearest-object choice;
- shield/barrier, grav, ranged weapons, power systems, apparel/strong structures and valuable matter receive differentiated priority;
- successful assimilation records learning evidence and converts consumed material into stored replication matter;
- offspring consume stored matter rather than spawning freely;
- offspring count is bounded per assimilation;
- autonomous hostile Replicator population is capped by a Def-tunable per-map ceiling;
- player-owned/player-controlled Replicators do not autonomously consume the player colony.

### Learned adaptation state — IMPLEMENTED FOUNDATION

Independent cumulative branches:
- Material
- Armor
- Ranged
- Power
- Shield
- Grav
- AntiShield

The fresh rebuild originally allowed only one adaptation enum value at a time. That has been corrected to cumulative save-persistent bit flags with migration for the earlier fresh-save field.

Learning is driven by successful assimilation evidence rather than arbitrary spawn flags.

### Armor adaptation — IMPLEMENTED

- learned from applicable armor/material/strong-target evidence;
- reduces incoming non-EMP damage through Def-tunable multiplier;
- retained Armor overlay renders when learned.

### Ranged adaptation — IMPLEMENTED

- learned from ranged weapon/technology evidence;
- gives autonomous block Replicators learned ranged fire;
- distinct from the Artillery specialist's innate siege-support role;
- retained Ranged overlay renders when learned.

### Power adaptation — IMPLEMENTED

- learned from powered systems;
- improves self-regeneration through Def-tunable multiplier;
- retained Power overlay renders when learned.

### Shield adaptation / Shield Replicator behavior — IMPLEMENTED

- learned from shield/barrier evidence;
- gives a rechargeable defensive shield pool;
- EMP bypasses/suppresses the adaptive shield behavior;
- retained Shield overlay renders when learned.

### Learned anti-shield development — IMPLEMENTED STATE / EXTERNAL INTEGRATION DEPENDENCY

- first shield encounter does **not** instantly grant complete anti-shield mastery;
- repeated shield evidence is required (current threshold Def-tunable);
- AntiShield knowledge is stored cumulatively and survives hierarchy transformations;
- current adaptive ranged damage can exploit learned anti-shield state against Replicator adaptive shields.

Still dependent on later concrete non-Replicator WNG shield systems for full cross-system countermeasure interaction. This is explicitly unfinished with dependency recorded, not forgotten.

### Grav adaptation — IMPLEMENTED STATE/VISUAL / GAMEPLAY DEPENDENCY

- grav evidence can be learned and retained;
- Grav overlay renders when learned;
- actual mobility/grav gameplay effect is intentionally **not faked** before WNG's real gravtech/gravship mechanics exist.

Dependency: bind Grav adaptation to the later concrete WNG grav system once implemented.

### State inheritance — IMPLEMENTED FOR CURRENT BLOCK STATE

Current split/recombine transfer includes:
- material identity;
- all cumulative adaptation flags;
- shield/anti-shield evidence;
- split-born recombination lockout;
- stored replication matter with conservation semantics;
- faction ownership through normal pawn generation/transaction flow.

Later exact sovereign-controller identity/control metadata belongs to the later Queen/control subsystem.

### Regeneration — IMPLEMENTED

- block Replicators heal over time;
- EMP suppresses regeneration;
- Power adaptation improves healing rate;
- Repairer support is a separate active ally-repair system.

### EMP suppression — IMPLEMENTED FOUNDATION

EMP meaningfully suppresses core replication systems including:
- assimilation;
- recombination;
- regeneration;
- specialist active functions;
- adaptive shield recharge/active ranged functions.

Exact timing remains tunable.

### Dangerous Replicator Matter / reassembly — IMPLEMENTED

- genuine Replicator destruction can produce Replicator Matter and Core Fragments;
- sufficiently large dormant Matter stacks can reassemble into hostile Drones;
- thresholds/delay/chance/output are tunable Def/component values;
- autonomous reassembly respects the same population ceiling as assimilation growth;
- powered containment freezes the reassembly clock.

### Containment — IMPLEMENTED

A powered Replicator containment projector now exists.

While active:
- dangerous Replicator Matter does not advance toward reassembly;
- hostile block Replicators inside the field cannot assimilate or recombine;
- Burrowers specifically prioritize destroying the projector when eligible;
- player-controlled Replicators do not treat their own colony containment as an autonomous hostile objective.

Projector radius, power draw, construction cost and research access remain tunable.

### Swarm coordination / AI — IMPLEMENTED FOUNDATION

The current Replicator ThinkTree now includes role-specific behavior:
- Repairer support;
- Artillery ranged support;
- Burrower breaching;
- Controller-shared target focus;
- assimilation;
- normal LordDuty/hostile behavior fallback.

Controller and specialist searches are bounded by role/range and are not a design-lock architecture; further tactical refinement can follow live testing.

### Bounded population / growth — IMPLEMENTED

- assimilation offspring require matter;
- per-assimilation offspring count is bounded;
- map-level hostile Replicator population ceiling is Def-tunable;
- dangerous Matter reassembly respects the ceiling;
- genuine-death split children are treated as transformation mass rather than free autonomous growth and therefore are not blocked by the growth cap;
- the one-hour split-born recombination lockout remains the combat-balancing mechanism for large-form breakup.

### Player-owned safety / control — IMPLEMENTED FOUNDATION

- player-owned/player-controlled Replicators do not autonomously assimilate colony assets;
- specialist autonomous hostile jobs exclude player-controlled bodies;
- player-owned ladder forms do not silently perform hostile-style automatic recombination;
- richer deliberate sovereign control commands are deferred to the later Queen/control subsystem.

### Child's Toy / player Replicator branch — IMPLEMENTED

Vardath rule:
- **Child's Toy is a player-owned mech.**
- while validly controlled it remains a normal colony mech;
- **if it goes feral, it transforms into an ordinary Replicator Drone**;
- the feral/uncontrolled delay is tunable;
- transformation carries learned Replicator state into the Drone;
- replacement Drone is successfully placed before the Toy is consumed, preventing failed transformation from silently deleting the pawn;
- the resulting Drone belongs to the hostile autonomous Replicator swarm and follows normal Drone behavior.

The current gestation recipe uses Replicator Matter plus a basic subcore and is gated by Replicator gestation research; exact cost/timing remains tunable.

### Autonomous faction / threat roster — IMPLEMENTED FOUNDATION

Current combat roster includes:
- Drone
- Hunter
- Bulwark
- Controller
- Repairer
- Burrower
- Artillery
- Titan
- Siege Mass

Weights are editable. Mixed block + human-form raid composition remains a later Asuran/human-form integration dependency.

### Core Fragment progression interface — IMPLEMENTED RESOURCE / LATER DEPENDENCY

Core Fragment exists as salvage/research material. Later reconstruction/control/advanced research uses remain dependent on later subsystems and are not implied complete merely because the resource exists.

### Human-form / Asuran / Queen sovereign dependencies — EXPLICITLY UNFINISHED

Tracked for the later human-form/Queen layer:
- block Replicators remain mechanically distinct from human-form Replicators/Asurans;
- mixed raids may intentionally contain both;
- exact Queen has genuine sovereign block-Replicator authority;
- Queen is one exact female human-form Replicator, age 13 in the current first-build design, held in a real cryosleep chamber;
- she becomes player-recruited immediately when released/spawned;
- Asuran/Lattice operatives attempt to capture her during recovery;
- while player-owned, later Asuran capture raids may target **any player map where she is physically present**, not only home maps;
- capture commits only when a hostile carrier physically exits the map with the exact Queen;
- if captured, suitable future Lattice threats gain genuine sovereign block-Replicator access rather than a fake outbreak modifier;
- Sovereign Neural Lattice implant control remains separate and bounded;
- temporary Asuran lattice intrusion remains another distinct override state.

## Final block-foundation reconciliation result

Every known block Replicator feature found in the plan, correction history, retained asset tree and current implementation now ends this pass as either:

- **implemented in the block foundation**, or
- **explicitly unfinished because it depends on a later concrete subsystem** (Grav gameplay integration, external shield countermeasure integration, Queen/Asuran sovereign-control integration, mixed human-form raids and richer sovereign player commands).

There is no known block Replicator feature currently left in an untracked/forgotten state.

Latest fresh implementation was minimally verified with a temporary GitHub Actions compile/XML pass; both succeeded and the temporary workflow was removed afterward.
