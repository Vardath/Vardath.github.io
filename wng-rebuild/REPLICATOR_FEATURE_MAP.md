# WNG — block Replicator feature map

Author/final design authority: **Vardath**.

This is the current reconciliation map for the clean RimWorld 1.6 rebuild. It is not immutable canon. Newer explicit Vardath instructions override it.

## Scope / identity boundary

This map covers the **mechanical block Replicator foundation and its live sovereign-control interface**. Human-form Replicators/Asurans and the exact Replicator Queen remain separate identity layers even where they control block bodies.

Specialist bodies and learned adaptations are separate from the physical size ladder. Queen authority, Sovereign Neural Lattice authority and temporary Asuran intrusion are separate controller domains rather than one generic control flag.

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

Current public mod head after the validated Queen-sovereignty pass:

- **`f2b9c0b3c7ac6ac440dd80d715d44f47a0981973`**

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
- `ReplicatorRetaliation.cs`
- `ReplicatorSovereignty.cs`
- `ChildsToy.cs`

Current Defs include the full ladder, all four specialist bodies, Child's Toy, Replicator faction, jobs/ThinkTree, research/gestation, containment, Replicator resources and Queen-sovereignty Hediff/job wiring.

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
- the lockout exists specifically so killing a Titan/Siege Mass does not immediately recreate the same threat and appear immortal;
- learned state and stored matter survive hierarchy transactions;
- stored matter sums upward and is divided among genuine-death children rather than duplicated or lost;
- sovereign controller authority/domain now also survives both directions;
- different control domains cannot recombine merely because their current faction is the same;
- Queen-controlled player blocks use explicit sovereign recombination rather than silently restoring hostile automatic recombination.

### Controller — IMPLEMENTED

Controller is a specialist coordination body, not a size-ladder rung and not equivalent to Queen/implant sovereign authority.

Implemented behavior:
- finds nearby same-domain autonomous Replicators;
- provides a shared hostile focus;
- respects controller-domain boundaries, not faction equality alone;
- stops active coordination behavior under EMP or sovereign interference;
- ordinary Replicators still function without a Controller.

### Repairer — IMPLEMENTED

Implemented behavior:
- seeks damaged same-domain block Replicators;
- prioritizes more seriously injured allies;
- moves into repair range and heals damage;
- does not repair Replicators belonging to another sovereign domain merely because faction matches;
- stops active repair under EMP/interference;
- a Queen-controlled Repairer also exposes an explicit sovereign repair command for an exact same-domain target.

### Burrower — IMPLEMENTED

Implemented behavior:
- breaches hostile structures;
- prioritizes the WNG Replicator containment projector first;
- then prioritizes access blockers such as doors/gates/bulkheads, walls and barricades;
- generic hostile buildings are fallback targets;
- can attack eligible factionless access blockers where necessary;
- respects ownership/hostility and EMP rules;
- Queen-controlled Burrowers expose a dedicated sovereign breach command rather than depending on mechanitor UI.

This is the current first-build tactical implementation and remains tunable/refinable through testing.

### Artillery / siege support — IMPLEMENTED

Implemented behavior:
- real long-range support attack;
- Def-tunable minimum/maximum range, warmup, damage and armor penetration;
- operates as a ranged support specialist rather than a melee pawn with an Artillery label;
- respects hostility/control boundaries and EMP;
- sovereign attack orders use the real artillery job when range/line-of-sight permit, otherwise fall back to normal physical attack behavior.

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

Queen/human-form **Nanite Reserve remains separate** from this block stored-matter economy.

### Learned adaptation state — IMPLEMENTED FOUNDATION

Independent cumulative branches:
- Material
- Armor
- Ranged
- Power
- Shield
- Grav
- AntiShield

The fresh rebuild originally allowed only one adaptation enum value at a time. That was corrected to cumulative save-persistent bit flags with migration for the earlier fresh-save field.

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

Still dependent on concrete non-Replicator shield integrations for broader cross-system countermeasure interaction. This is explicitly unfinished with dependency recorded, not forgotten.

### Grav adaptation — IMPLEMENTED STATE/VISUAL / GAMEPLAY DEPENDENCY

- grav evidence can be learned and retained;
- Grav overlay renders when learned;
- the retained learned state exists even though a richer dedicated block mobility effect still needs deliberate integration with current gravtech/gravship mechanics rather than a fake generic buff.

### State inheritance — IMPLEMENTED FOR CURRENT BLOCK + QUEEN AUTHORITY STATE

Current split/recombine transfer includes:
- material identity;
- all cumulative adaptation flags;
- shield/anti-shield evidence;
- split-born recombination lockout;
- stored replication matter with conservation semantics;
- faction ownership through normal pawn transaction flow;
- sovereign authority type;
- exact controller reference/domain key;
- control/original faction metadata.

Different controller domains are deliberately prevented from accidental cross-domain recombination.

Future Neural Lattice and temporary-Asuran authority must reuse this same persistence/transaction interface.

### Regeneration — IMPLEMENTED

- block Replicators heal over time;
- EMP suppresses regeneration;
- Power adaptation improves healing rate;
- Repairer support is a separate active ally-repair system.

### EMP suppression — IMPLEMENTED FOUNDATION + SOVEREIGN INTERFERENCE

EMP meaningfully suppresses core replication systems including:
- assimilation;
- recombination;
- regeneration;
- specialist active functions;
- adaptive shield recharge/active ranged functions;
- sovereign block commands when the block is EMP suppressed;
- exact-Queen command signal when the Queen's human-form lattice is EMP disrupted.

A sovereign-controlled block under EMP/containment receives a dedicated high-priority non-combat suppression job. Exact timing remains tunable.

### Dangerous Replicator Matter / reassembly — IMPLEMENTED

- genuine Replicator destruction can produce Replicator Matter and Core Fragments;
- sufficiently large dormant Matter stacks can reassemble into hostile Drones;
- thresholds/delay/chance/output are tunable Def/component values;
- autonomous reassembly respects the same population ceiling as assimilation growth;
- powered containment freezes the reassembly clock.

### Containment — IMPLEMENTED + SOVEREIGN INTERFERENCE

A powered Replicator containment projector exists.

While active:
- dangerous Replicator Matter does not advance toward reassembly;
- hostile block Replicators inside the field cannot assimilate or recombine;
- Burrowers specifically prioritize destroying the projector when eligible;
- player-controlled Replicators do not treat their own colony containment as an autonomous hostile objective;
- Queen acquisition/commands are blocked when the target block is contained;
- Queen command signal is blocked while the Queen herself is inside active Replicator containment;
- already controlled blocks in active containment are suppressed rather than sovereignty bypassing containment.

Projector radius, power draw, construction cost and research access remain tunable.

### Swarm coordination / AI — IMPLEMENTED FOUNDATION

The current Replicator ThinkTree includes role-specific behavior:
- sovereign interference suppression above queued/player orders;
- Repairer support;
- Artillery ranged support;
- Burrower breaching;
- Controller-shared target focus;
- assimilation;
- normal LordDuty/hostile behavior fallback.

Controller, Repairer and retaliation relationships now use controller-domain identity where authority exists. Further tactical refinement can follow live testing.

### Bounded population / growth — IMPLEMENTED

- assimilation offspring require matter;
- per-assimilation offspring count is bounded;
- map-level hostile Replicator population ceiling is Def-tunable;
- dangerous Matter reassembly respects the ceiling;
- genuine-death split children are transformation mass rather than free autonomous growth and therefore are not blocked by the growth cap;
- the one-hour split-born recombination lockout remains the combat-balancing mechanism for large-form breakup.

### Player-owned safety / control — QUEEN FOUNDATION IMPLEMENTED

- player-owned/player-controlled Replicators do not autonomously assimilate colony assets;
- specialist autonomous hostile jobs exclude ordinary player-controlled bodies;
- player-owned ladder forms do not silently perform hostile-style automatic recombination;
- exact Queen sovereignty is now genuine persistent per-block control/faction state;
- Queen-controlled blocks expose dedicated sovereign move/attack/repair/breach/recombine/release commands so the system does not pretend vanilla mechanitor control exists;
- exact Queen can acquire an individual block or a bounded nearby swarm;
- current Queen range/cap are Def-tunable and subject to live balance testing;
- invalid physical/controller state releases authority cleanly.

Still later: the bounded Sovereign Neural Lattice implant control path and temporary Asuran override path.

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

### Exact Queen sovereign authority — IMPLEMENTED FOUNDATION

Current exact-Queen behavior:
- Queen is one exact persistent female human-form Replicator, age 13 in the current first-build design;
- she uses real human-form nanite identity, not a block-machine race;
- she becomes player-recruited immediately on actual vault casket release;
- `WNG_ReplicatorQueenSovereignty` is ensured on that exact pawn, including existing-save maintenance;
- only that exact Queen has innate `Queen` authority;
- ordinary Asuran rank/xenotype is not sovereign authority;
- exact block pawns receive persistent authority/controller/domain metadata and real faction transfer;
- current physical-presence validity is same map or same caravan;
- EMP/containment interrupt command rather than being bypassed;
- hierarchy and specialist state remain real while controlled;
- authority survives split/recombine with domain isolation;
- Queen capture remains a separate exact-pawn physical storyline boundary.

### Sovereign Neural Lattice — EXPLICIT NEXT UNFINISHED CONTROL LAYER

Required behavior remains:
- bearer is **not** a Queen;
- bounded target-specific control;
- must use the existing `NeuralLattice` authority value and `CompReplicatorSovereignty` persistence/domain system;
- exact controller identity persists through save/load while valid;
- split/recombine preserves the correct controller domain;
- different controller domains never merge accidentally;
- invalid bearer/controller state restores/releases ownership cleanly;
- capacity/range/cost/cooldown should remain author-tunable and mechanically more bounded than the exact Queen.

### Temporary Asuran lattice intrusion — EXPLICITLY UNFINISHED AND SEPARATE

Required later:
- separate `TemporaryAsuran` authority path;
- explicit expiry/restoration semantics;
- must not silently convert into Queen or Neural Lattice ownership;
- future hostile Asuran control should use real domain state, not faction-only shortcuts.

### Queen recovery/captured-Queen consequences — PARTIAL / LATER DEPENDENCY

Implemented:
- exact Queen vault/release;
- first all-or-nothing four-operative Asuran recovery operation;
- nonlethal dedicated jobs;
- physical Asuran Jumper;
- capture commits only when exact Queen physically departs in exact transit container;
- exact kidnapped-pawn persistence.

Still later:
- recurring recovery operations on any player map where the exact Queen physically exists;
- consequences if Asurans retain/recruit the captured Queen;
- suitable Lattice threats gaining genuine sovereign block access from the captured Queen;
- mixed Asuran + sovereign block threat composition;
- infiltration.

## Final block-foundation reconciliation result

Every known block Replicator feature found in the plan, correction history, retained asset tree and current implementation is currently either:

- **implemented in the block/Queen-control foundation**, or
- **explicitly unfinished because it belongs to a later concrete subsystem** (broader Grav gameplay refinement, cross-system shield countermeasures, Sovereign Neural Lattice, temporary Asuran intrusion, recurring/captured-Queen consequences, mixed human-form threats and infiltration).

There is no known block Replicator feature currently left in an untracked/forgotten state.

Queen sovereignty was validated with temporary GitHub Actions run **34576583840**: C# build SUCCESS, all Def/Patch XML parse SUCCESS, sovereignty-domain invariants SUCCESS. The temporary workflow was removed afterward. This is not live RimWorld gameplay validation.
