# WNG — block Replicator feature map

Author/final design authority: **Vardath**.

This is the current reconciliation map for the clean RimWorld 1.6 rebuild. It is not immutable canon; newer explicit Vardath instructions override it.

## Scope / identity boundary

Mechanical block Replicators, human-form Replicators/Asurans, the exact Replicator Queen, and controller implants are separate identity layers even where they interact.

Physical size ladder, specialist bodies, learned adaptations and controller authority are also separate concepts.

Current controller identities are deliberately distinct:
- autonomous / no authority;
- exact Queen authority;
- Sovereign Neural Lattice implant authority;
- future temporary Asuran intrusion.

Same faction never implies same controller domain.

## Current public snapshot

Current public mod HEAD:

**`0e5dfc893a8efec624053e677ae99d6983c25fc9`**

Fetch `main` again before editing.

## Retained assets — accounted for

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

No replacement art is generated unless Vardath asks.

---

# FEATURE STATUS MAP

## Physical hierarchy — IMPLEMENTED

Upward:

**Drone -> Hunter -> Bulwark -> Titan -> Siege Mass**

Genuine destruction:

**Siege Mass -> Titans -> Bulwarks -> Hunters -> Drones**

Implemented rules:
- Drone is irreducible;
- combine counts/timing and split counts/lockout remain Def-tunable;
- genuine destruction creates real lower forms rather than deleting large bodies;
- intentional upward consumption does not trigger death splitting;
- split-born bodies receive the current tunable ~2,500-tick recombination lockout;
- learned state and stored matter survive hierarchy transactions;
- stored matter sums upward and divides downward rather than duplicating/disappearing;
- exact controller authority/domain also survives both directions;
- different controller domains cannot recombine even when faction matches;
- controlled/player ladder forms require explicit controller recombination rather than restoring hostile autonomous recombination.

## Specialists — IMPLEMENTED

### Controller
- specialist coordination body, not a size rung or sovereign identity;
- coordinates nearby same-domain autonomous/operational Replicators onto shared hostile focus;
- respects exact controller domain;
- stops active coordination under EMP/controller interference.

### Repairer
- seeks and repairs damaged same-domain Replicators;
- prioritizes serious injury;
- cannot heal another sovereign domain merely because faction matches;
- controlled Repairers expose exact-target repair command;
- stops active repair under EMP/interference.

### Burrower
- real structural breaching role;
- prioritizes active WNG containment projector, then access blockers/walls/barricades, then eligible hostile structures;
- controlled Burrowers expose explicit breach command;
- respects hostility/domain/EMP rules.

### Artillery
- real long-range support job with Def-tunable min/max range, warmup, damage and penetration;
- distinct from learned Ranged adaptation;
- controlled attack orders use artillery job when valid, otherwise real physical attack fallback.

## Assimilation / block matter economy — IMPLEMENTED FOUNDATION

- autonomous hostile blocks seek useful accessible matter/technology;
- successful assimilation records technological evidence and creates stored replication matter;
- useful technology is prioritized over arbitrary objects;
- offspring consume stored matter;
- offspring count and map population are bounded;
- player-owned/controller-owned bodies do not autonomously eat the colony.

**Block stored matter is not human-form Nanite Reserve.**

## Learned adaptations — IMPLEMENTED FOUNDATION

Cumulative save-persistent branches:
- Material;
- Armor;
- Ranged;
- Power;
- Shield;
- Grav;
- AntiShield.

Learning follows real assimilation evidence.

### Armor — IMPLEMENTED
- reduces incoming non-EMP damage by tunable effect;
- retained Armor overlay renders.

### Ranged — IMPLEMENTED
- learned from ranged/weapon evidence;
- gives autonomous ranged fire;
- separate from Artillery specialist;
- retained overlay renders.

### Power — IMPLEMENTED
- learned from power systems;
- improves self-regeneration;
- retained overlay renders.

### Shield — IMPLEMENTED
- learned from shield/barrier evidence;
- rechargeable defensive shield pool;
- EMP bypasses/suppresses behavior;
- retained overlay renders.

### AntiShield — IMPLEMENTED STATE / BROADER INTEGRATION DEPENDENCY
- repeated shield evidence required rather than instant mastery;
- cumulative state survives transformations;
- current Replicator ranged interaction can exploit it against Replicator adaptive shields;
- broader non-Replicator shield interactions remain a later concrete-system dependency.

### Grav — IMPLEMENTED STATE/VISUAL / RICHER EFFECT DEPENDENCY
- grav evidence can be learned/saved;
- retained overlay renders;
- dedicated richer mobility behavior still needs deliberate integration rather than a generic fake buff.

## Regeneration — IMPLEMENTED
- block self-healing;
- EMP suppression;
- Power adaptation improves rate;
- separate from Repairer ally-repair.

## EMP — IMPLEMENTED
EMP suppresses/interferes with:
- assimilation;
- recombination;
- regeneration;
- specialist active behavior;
- adaptive shields/ranged functions where applicable;
- Queen signal through human-form EMP disruption;
- Sovereign Neural Lattice signal through implant EMP disruption;
- controlled block commands.

Interfered controlled blocks use a high-priority non-combat suppression job.

## Dangerous Replicator Matter — IMPLEMENTED
- destroyed Replicators can produce Matter/Core Fragments;
- sufficiently large uncontained Matter can self-assemble into hostile Drones;
- delay/chance/threshold/output are tunable;
- population ceiling respected;
- powered containment freezes reassembly clock.

## Containment — IMPLEMENTED
Powered projector:
- suppresses hostile assimilation/recombination within field;
- freezes dangerous Matter reassembly;
- is a Burrower priority target;
- does not become an autonomous objective for valid player-controlled blocks;
- blocks Queen and Neural-Lattice acquisition when target is contained;
- blocks controller signal while controller is contained;
- suppresses already-controlled blocks instead of letting sovereignty bypass containment.

## Swarm AI / coordination — IMPLEMENTED FOUNDATION
Current ThinkTree includes:
- controller-interference suppression before queued/player orders;
- Repairer support;
- Artillery support;
- Burrower breach;
- Controller focus;
- assimilation;
- normal duty/hostile fallback.

Relationships are controller-domain aware where authority exists.

## Population / growth — IMPLEMENTED
- assimilation growth spends matter;
- bounded offspring;
- hostile map population cap;
- Matter reassembly respects cap;
- genuine-death split is transformation mass rather than free reproduction and therefore is not blocked by the growth cap;
- split-born recombination lockout is the anti-instant-reformation combat mechanic.

## Child's Toy — IMPLEMENTED
- player-owned mech branch;
- valid control keeps colony ownership;
- prolonged feral/uncontrolled state converts it into a real hostile ordinary Drone;
- learned state transfers;
- replacement is successfully placed before Toy is consumed;
- current gestation uses Replicator Matter + basic subcore and research; tuning remains editable.

## Autonomous threat roster — IMPLEMENTED FOUNDATION
- Drone;
- Hunter;
- Bulwark;
- Controller;
- Repairer;
- Burrower;
- Artillery;
- Titan;
- Siege Mass.

Mixed human-form/block threat composition remains later Asuran integration work.

## Core Fragment — IMPLEMENTED RESOURCE
A real salvage resource used by containment/progression and now by Sovereign Neural Lattice fabrication. Broader future research/reconstruction use remains open.

---

# CONTROLLER LAYERS

## Exact Queen sovereignty — IMPLEMENTED

The one exact persistent age-13 female nanite-humanoid Queen has innate broader authority.

Implemented:
- exact persistent controller identity;
- real faction transfer of exact block pawns;
- same-map/same-caravan physical validity;
- exact-target acquisition plus bounded local-swarm seizure;
- Def-driven current tuning: 40-cell direct, 24-cell local swarm, normal cap 12;
- dedicated move/attack/repair/breach/recombine/release commands independent of vanilla mechanitor UI;
- existing-save Queen Hediff maintenance;
- EMP/containment interference;
- split/recombine authority continuity;
- domain-isolated Controller/Repairer/retaliation.

Queen sovereignty validation: **34576583840 SUCCESS** for C# build, XML parse and sovereignty invariants. Live RimWorld validation pending.

## Sovereign Neural Lattice — IMPLEMENTED

This is a WNG-specific Stargate-derived controller implant, **not a canon-named Stargate device and not a Queen identity**.

Physical/progression path:
- tangible `WNG_SovereignNeuralLattice` item;
- research requires both Replicator study and Asuran fabrication;
- manufactured only at `WNG_AsuranWorkshop`;
- ingredients include a real Replicator Core Fragment + `WNG_NaniteSludge` + high-tech substrate;
- native `Recipe_InstallImplant` brain surgery;
- native `Recipe_RemoveImplant` removal returns physical implant item.

Authority behavior:
- exact non-Queen bearer controls exact target blocks using `ReplicatorControlAuthority.NeuralLattice`;
- exact bearer reference and unique domain key persist through save/load;
- real block faction transfer and prior-faction restoration;
- **24-cell acquisition range / normal cap 3 / 1,800-tick EMP signal disruption** in current Def tuning;
- acquisition is target-specific only—no Queen-style swarm seizure;
- after acquisition, shared physical-presence validity is same map or same caravan; 24 cells is acquisition range, not an ownership-breaking live leash;
- EMP/containment interfere;
- block commands use the same proven controller command surface;
- split/recombine conserves exact implant domain;
- cross-domain merge/repair/coordination/retaliation remains prohibited;
- removing the implant releases that exact controller domain;
- exact Queen cannot create a second overlapping implant domain on top of innate Queen authority;
- genuine split may temporarily put a domain above the normal acquisition cap because inherited controller identity is conserved rather than stripped.

Validation:
- run **34580535936** caught direct protected `Gizmo.disabled` access;
- corrected to public `Command.Disable(...)`;
- run **34580647197** passed C# build, all Def/Patch XML parsing and implant/research/surgery/domain invariants;
- temporary workflow removed;
- live RimWorld validation remains pending;
- current vanilla health-item graphic is mechanics placeholder; final dedicated art is unfinished and no replacement art was generated.

## Temporary Asuran lattice intrusion — NEXT / UNFINISHED

Required next implementation:
- use `ReplicatorControlAuthority.TemporaryAsuran`;
- temporary hijack only;
- must preserve the exact previous authority/controller/domain/faction so expiry/interruption can restore Queen, Neural-Lattice or autonomous state correctly;
- ordinary Asuran does not receive permanent Queen sovereignty;
- author-tunable duration/range/cap/trigger behavior;
- EMP/containment remain counters;
- split/recombine during intrusion must keep coherent temporary state and restoration metadata;
- no cross-domain contamination.

## Queen recovery / captured-Queen consequence — PARTIAL

Implemented:
- exact vault/casket/release;
- first four-operative nonlethal recovery operation;
- physical Asuran Jumper;
- capture only at real departure with the exact Queen physically aboard;
- exact kidnapped-pawn persistence.

Still later:
- recurring recovery operations on the exact map containing the Queen;
- hostile consequences if Asurans retain/recruit her;
- genuine Asuran-controlled block access in suitable threat compositions;
- mixed Asuran + block threats;
- infiltration.

---

# CURRENT RECONCILIATION RESULT

Every known block/control requirement is currently either implemented or explicitly dependency-recorded. Current tracked future dependencies are:
- temporary Asuran intrusion;
- captured-Queen/mixed human-form threats;
- infiltration/broader Neural Interface;
- richer Grav adaptation;
- broader cross-system anti-shield behavior;
- final dedicated art/audio;
- live RimWorld validation.

Do not regress Queen or Neural-Lattice control into an aura, generic faction flag, outbreak modifier or fake mechanitor system.
