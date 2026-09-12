# WNG — block Replicator feature map

Author/final design authority: **Vardath**.

This is a **design/relationship map only**. It is not an implementation checkpoint, current-state inventory or next-task list. The master plan + active append(s) + corrections define the target; actual public `Vardath/Wraith-Nanite-Gravtech-1.6` source defines what is already implemented.

Do not infer present absence/completion from this file.

# Identity boundaries

Mechanical block Replicators, human-form Replicators/Asurans, the exact Replicator Queen and controller implants are separate identity layers even where they interact.

Physical size hierarchy, specialist bodies, learned adaptations and controller authority are also separate concepts.

Controller identity must remain explicit. Current authority concepts include:
- autonomous / no authority;
- exact Queen authority;
- Sovereign Neural Lattice authority;
- Temporary Asuran intrusion;
- captured-retained-Queen sovereign access where the plan/current design requires it.

Same faction never automatically implies same controller domain.

# Retained approved assets

Block body graphics:
- Drone/base;
- Hunter;
- Bulwark;
- Titan;
- Siege Mass;
- Controller;
- Repairer;
- Burrower;
- Artillery.

Adaptation overlays:
- Armor;
- Ranged;
- Power;
- Grav;
- Shield.

Resources:
- Replicator Matter;
- Replicator Core Fragment.

These retained assets are evidence of required/planned forms and branches. Do not copy the art tree and then omit corresponding behavior from memory.

No replacement art is generated unless Vardath explicitly asks.

# Physical hierarchy

Upward recombination:

**Drone -> Hunter -> Bulwark -> Titan -> Siege Mass**

Genuine destruction breakup:

**Siege Mass -> Titan -> Bulwark -> Hunter -> Drone**

Required behavior:
- Drone/base is irreducible;
- recombination counts/timing and split counts/lockout remain tunable;
- genuine destruction creates real lower forms rather than simply deleting the larger body;
- intentional upward consumption must not trigger death splitting;
- split-born children use the current approximately 2,500-tick / one-hour recombination lockout unless Vardath retunes it;
- learned state, stored matter and controller state survive transformations where appropriate;
- stored matter must not duplicate/disappear across hierarchy transactions;
- different controller domains cannot recombine merely because faction matches;
- player/controller-owned recombination must preserve deliberate authority boundaries.

# Specialists

## Controller
- coordination specialist, not a physical size rung or sovereign identity;
- focuses same-domain operational Replicators where appropriate;
- respects exact domain;
- EMP/controller interference suppresses active coordination.

## Repairer
- seeks and repairs damaged same-domain Replicators;
- serious damage should be prioritised appropriately;
- cannot freely heal another sovereign domain simply because faction matches;
- player/controller-owned Repairers may expose explicit repair orders;
- EMP/interference remains counterplay.

## Burrower
- structural breaching specialist;
- containment/access blockers/walls/barricades and valid hostile structures are appropriate targets according to current AI design;
- controller-owned Burrowers may expose explicit breach orders;
- respects hostility/domain/EMP rules.

## Artillery
- distinct long-range support specialist;
- separate from learned Ranged adaptation;
- range/warmup/damage/penetration remain tunable;
- controlled attack orders should use its actual artillery role when valid rather than reducing it to a label.

# Assimilation / block matter economy

Required design:
- autonomous hostile blocks seek useful accessible matter/technology;
- successful assimilation records technological evidence and creates usable replication matter/economy;
- useful technology is prioritised over arbitrary consumption where practical;
- offspring consume stored matter rather than spawning free mass;
- offspring/map population is bounded;
- player-owned/controller-owned bodies do not autonomously consume the player colony.

**Block stored matter is not human-form Nanite Reserve.**

# Learned adaptations

Adaptation is cumulative/save-persistent where gameplay needs it and should be learned from real encountered/assimilated evidence rather than arbitrary flags.

Required branches:
- Material;
- Armor;
- Ranged;
- Power;
- Shield;
- Grav;
- AntiShield/countermeasure development.

## Armor
- meaningful reduction/mitigation of appropriate incoming damage;
- EMP remains special where required;
- retained Armor overlay available.

## Ranged
- learned from ranged/weapon evidence;
- provides real ranged capability;
- distinct from Artillery specialist;
- retained Ranged overlay available.

## Power
- learned from power-system evidence;
- should materially affect self-repair/regeneration/energy behavior according to current implementation design;
- retained Power overlay available.

## Shield
- learned from shield/barrier evidence;
- real rechargeable/defensive behavior rather than name-only marker;
- EMP can bypass/suppress according to design;
- retained Shield overlay available.

## AntiShield
- requires repeated/meaningful shield evidence rather than instant universal mastery;
- persists through hierarchy changes where appropriate;
- must interact with concrete shield systems when integration exists;
- third-party shield support should only be added for verified external shield systems, not guessed APIs.

## Grav
- learned from real gravtech evidence;
- retained Grav overlay available;
- should produce a real physical/mobility/gravitic effect rather than a generic fake stat buff.

# Regeneration

- block self-healing is distinct from Repairer ally-repair;
- EMP suppresses/interferes;
- Power adaptation may improve it according to current design;
- rates/costs remain tunable.

# EMP

EMP is a meaningful countermeasure and may suppress/interfere with:
- assimilation;
- recombination;
- regeneration;
- specialist active behavior;
- adaptive shields/ranged functions where applicable;
- Queen signal through human-form disruption;
- Sovereign Neural Lattice signal through implant disruption;
- Temporary Asuran control;
- controller-issued block commands.

Do not make sovereignty magically bypass containment/EMP.

# Dangerous Replicator Matter

Replicator Matter is dangerous salvage, not inert crafting material only.

Required design:
- destroyed Replicators can produce Replicator Matter/Core Fragments according to the current economy;
- sufficiently large uncontained Matter may self-assemble into hostile Drones after a dormancy period;
- current intended dormancy is **one full RimWorld day / 60,000 ticks** unless Vardath retunes it;
- minimum pile, pawn cost, check cadence/chance/growth/cap remain tunable;
- powered containment resets/suppresses reassembly danger;
- population ceilings remain respected;
- analysis/research use may coexist with the danger mechanic rather than consuming its identity.

# Containment

Powered Replicator containment should meaningfully suppress appropriate hostile Replicator behavior within its field, including dangerous Matter reassembly and controller acquisition/signal where applicable.

Containment remains a real physical countermeasure and may be a Burrower priority target.

Valid player-controlled blocks should not treat their own functioning containment as an automatic hostile objective unless current design explicitly says so.

# Swarm coordination / AI

The behavior tree should preserve separate priority layers where appropriate:
- controller/interference suppression;
- Repairer support;
- Artillery support;
- Burrower breach;
- Controller coordination/focus;
- assimilation;
- normal duty/hostile fallback.

Authority/domain relationships must be respected.

# Population / growth

- assimilation growth spends matter;
- offspring are bounded;
- dangerous-Matter reassembly respects hostile-map caps;
- genuine death splitting is transformation mass, not free reproduction;
- split-born recombination lockout prevents instant large-form restoration.

# Child's Toy branch

Child's Toy is a distinct player branch:
- player-owned friendly Replicator content;
- valid control preserves colony ownership;
- prolonged feral/uncontrolled state may convert it into an ordinary hostile Drone according to current plan;
- learned state transfers appropriately;
- replacement must be successfully placed before source is consumed;
- gestation/cost/timing remain tunable.

# Threat roster

Block swarm roles may include:
- Drone;
- Hunter;
- Bulwark;
- Controller;
- Repairer;
- Burrower;
- Artillery;
- Titan;
- Siege Mass.

Human-form + block mixed threat composition is allowed where the Asuran/Queen plan calls for it. Block recombination remains block-only even when raid composition is mixed.

# Core Fragment

Replicator Core Fragment is real advanced salvage/material and may support containment, research, controller technology and reconstruction paths according to the master plan/current implementation.

# Controller layers

## Exact Queen
- one exact persistent human-form Queen has innate sovereign authority;
- authority is tied to exact controller identity/domain;
- real block ownership/control and restoration state, not an abstract outbreak modifier;
- same-map/same-caravan physical validity where current design uses it;
- EMP/containment interference;
- split/recombine continuity;
- domain-isolated coordination/repair/retaliation;
- tunable range/cap.

## Sovereign Neural Lattice
- physical WNG-specific controller implant, not Queen identity;
- bounded target-specific authority for exact bearer;
- real item/fabrication/surgery/removal path using appropriate Replicator/Asuran progression;
- unique bearer/domain save state;
- EMP/containment interference;
- split/recombine continuity;
- no overlapping Queen authority;
- tunable range/cap/disruption.

## Temporary Asuran intrusion
- distinct `TemporaryAsuran`-style authority;
- temporary hijack only;
- exact prior authority/domain/faction snapshot and restoration;
- EMP/containment counterplay;
- hierarchy transactions preserve both temporary state and restoration metadata;
- ordinary Asurans do not gain permanent Queen sovereignty.

## Captured Queen consequences
- if hostile Asurans retain the exact Queen, suitable threats can gain genuine sovereign block access;
- real mixed human-form + block threats are appropriate;
- no proxy Queen or flat arbitrary outbreak bonus.

# Human-form relationship

Human-form Replicators/Asurans remain a separate branch with nanite physiology, Neural Interface, infiltration, Quiet Lattice/player variants and exact-copy/reconstruction semantics according to the master plan.

Their existence must not collapse block Replicator identity or matter economy.

# Validation / continuity

Compile/XML/API checks establish source sanity only. Live RimWorld behavior/save-load/performance still requires real testing.

Do not create checkpoint files or pass logs for this map. When continuing, read the master plan/corrections and inspect current public source to determine which design requirements remain unfinished.
