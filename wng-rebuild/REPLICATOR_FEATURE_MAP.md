# WNG — block Replicator feature map

Author/final design authority: **Vardath**.

This is the working reconciliation map for the clean RimWorld 1.6 rebuild. It is not immutable canon. Newer explicit Vardath instructions override it.

## Scope / identity boundary

This map covers the **mechanical block Replicator foundation**. Human-form Replicators/Asurans and the Replicator Queen are separate later identity layers, although their later sovereign/control interfaces with block Replicators remain tracked as dependencies.

Specialist bodies and learned adaptations are separate from the physical size ladder.

## Retained assets — all accounted for

Body graphics retained under `Textures/Things/Pawn/Replicator/`:
- Drone/base
- Hunter
- Bulwark
- Titan
- Siege Mass
- Controller
- Repairer
- Burrower
- Artillery

Adaptation overlays retained under `Textures/Things/Pawn/Replicator/Adaptation/`:
- Armor
- Ranged
- Power
- Grav
- Shield

Resources retained under `Textures/Things/Item/Resource/Replicator/`:
- Replicator Matter
- Replicator Core Fragment

No replacement art is to be generated unless Vardath asks for it.

## Current public implementation inventory

Verified public `main` before this reconciliation: `84b9c08991cabd26e950d640fb9c4a350613e760`.

Current source:
- `ReplicatorState.cs` — material/adaptation state packet
- `ReplicatorAssimilation.cs` — hostile assimilation, matter yield, offspring spawning
- `ReplicatorEMP.cs` — EMP suppression
- `ReplicatorRegeneration.cs` — periodic healing while not EMP-suppressed
- `ReplicatorHierarchy.cs` — recombination, genuine-death splitting, split-born lockout, state transfer
- `ReplicatorMatter.cs` — death salvage and dangerous dormant-matter reassembly

Current Defs:
- Drone, Hunter, Bulwark, Titan, Siege Mass and Controller races/PawnKinds
- Repairer, Burrower and Artillery races/PawnKinds
- autonomous Replicator faction
- assimilation job / Replicator ThinkTree
- Replicator Matter / Core Fragment

## Complete relationship/status map

### Physical hierarchy

Upward recombination:

**Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass**

Downward genuine-destruction breakup:

**Siege Mass -> Titan -> Bulwark -> Hunter -> Drone/base**

Rules:
- Drone/base is irreducible.
- Combination counts and check timing are tunable Def values.
- Genuine destruction of a higher form produces operational lower forms rather than making the mass disappear.
- Intentional upward recombination consumption must not trigger death splitting.
- Split-born children receive the current tunable ~2,500-tick / ~1 in-game hour recombination lockout.
- **The purpose of that lockout is combat playability:** destroying a Titan or Siege Mass must not let its children immediately recreate the same large threat and make the fight effectively impossible/immortal.
- The exact duration remains tunable; the anti-impossible-combat behavior is required.
- Material/adaptation/control state must survive transformations where appropriate.

Status: **implemented foundation; cumulative adaptation state has now been added, while later control-domain transfer still remains to be implemented with the sovereign/control layer.**

### Controller

Relationship: specialist coordination body, not a size-ladder rung and not equivalent to Queen/implant sovereign control.

Required behavior:
- coordinate nearby same-domain Replicators;
- improve swarm target/focus/support behavior;
- respect EMP and ownership/control boundaries;
- remain useful but not required for basic Replicator operation.

Status: **unfinished — Def/PawnKind exists; behavior missing.**

### Repairer

Relationship: specialist support body.

Required behavior:
- find damaged allied block Replicators;
- move to/support them and actively repair injuries/damage;
- respect EMP and faction/control domains;
- never repair hostile Replicators merely because they share a race family.

Status: **unfinished — Def/PawnKind exists; behavior missing.**

### Burrower

Relationship: specialist breach/path-opening body.

Required behavior:
- identify tactically meaningful walls/doors/fortifications/containment blockers;
- breach them to open paths for the swarm;
- prioritize purposeful access over random destruction where practical;
- respect EMP and ownership/control boundaries.

Status: **unfinished — Def/PawnKind exists; behavior missing.**

### Artillery / siege support

Relationship: mature long-range support specialist.

Required behavior:
- possess a real ranged/siege attack or support function;
- operate at range behind/with the swarm rather than remain a melee pawn merely named Artillery;
- use swarm/controller target context where practical;
- respect EMP and control boundaries.

Status: **unfinished — Def/PawnKind exists; real ranged behavior missing.**

### Assimilation and matter economy

Required behavior:
- autonomous hostile Replicators seek accessible matter and useful technology;
- successful consumption produces Replicator matter/economy and learning evidence;
- growth/reproduction spends matter rather than spawning for free;
- target selection should value useful technology/materials/tactical targets rather than only nearest-object distance;
- population/growth must be bounded;
- player-owned Replicators must not autonomously consume the player colony.

Current implementation already prevents player-faction/player-controlled Replicators from autonomous assimilation and converts consumed targets into stored matter.

Status: **partial — basic consumption/economy implemented; target priorities and bounded swarm growth unfinished.**

### Learned adaptation state

Known independent learned branches:
- Material
- Armor
- Ranged
- Power
- Shield
- Grav
- Anti-shield/countermeasure knowledge after suitable shield experience

Evidence relationships:
- weapons/turrets -> Ranged learning
- armor/strong materials -> Armor/material learning
- power systems -> Power learning
- real shield technology/encounters -> Shield learning and suitable anti-shield knowledge
- gravtech -> Grav learning
- suitable advanced precursor/Asuran systems -> later advanced learned effects

Adaptations must be earned from successful interaction/assimilation rather than arbitrary spawn flags.

The previous fresh implementation stored only one enum adaptation at a time, causing later learning to overwrite earlier learning. This has been corrected to cumulative bit-flag state with save migration support.

Status: **implemented state foundation; gameplay effects and full target classifiers remain unfinished.**

### Adaptation gameplay effects and retained overlays

Armor:
- real protection/damage-resistance effect based on learned armor/material evidence.
- retained overlay: `WNG_ReplicatorAdapt_Armor.png`.

Ranged:
- real ranged combat capability learned from weapons/turrets; distinct from the Artillery specialist's innate siege role.
- retained overlay: `WNG_ReplicatorAdapt_Ranged.png`.

Power:
- real benefit learned from powered systems, such as improved regeneration/operational output, with exact tuning editable.
- retained overlay: `WNG_ReplicatorAdapt_Power.png`.

Grav:
- real mobility/grav-related benefit after gravtech learning; exact mechanic remains author-tunable and should not be faked before the relevant grav systems exist.
- retained overlay: `WNG_ReplicatorAdapt_Grav.png`.

Shield:
- real defensive shield adaptation / Shield Replicator behavior after shield learning.
- retained overlay: `WNG_ReplicatorAdapt_Shield.png`.
- later learned anti-shield/countermeasure development must exist after suitable shield encounters; this is separate from merely having a shield.

Status: **unfinished — state is now cumulative, but gameplay effects and retained overlay rendering are not implemented yet. Grav and anti-shield integration also depend on later concrete grav/shield targets for complete classification.**

### State inheritance

State that must survive split/recombine where appropriate:
- learned material information
- all learned adaptation flags/evidence
- recombination lockout on split-born children
- player/hostile ownership/control domain
- later sovereign-controller identity/control state
- matter/economy contribution where transaction semantics require it

Status: **partial — material and all current adaptation flags now copy/merge through transformations; later sovereign/control-domain state and explicit matter-accounting semantics remain to be added.**

### Regeneration

Required behavior:
- block Replicators repair themselves over time;
- EMP suppresses regeneration;
- Power/Repairer adaptations may modify this through centralized/tunable behavior.

Status: **basic regeneration implemented; specialist/adaptation interaction unfinished.**

### EMP suppression

Required behavior:
- EMP meaningfully suppresses replication systems across forms;
- at minimum blocks assimilation, recombination, regeneration and specialist/adaptation active functions while suppressed;
- exact duration remains tunable.

Status: **partial — core assimilation/recombination/regeneration suppression exists; new specialist/adaptation behaviors must integrate with it.**

### Dangerous Replicator Matter / reassembly

Required behavior:
- genuine Replicator destruction can leave Replicator Matter and occasional Core Fragments;
- sufficiently large dormant matter stacks can reassemble into hostile base Replicators;
- thresholds, delay, retry chance and output remain tunable;
- containment must provide a practical way to keep recovered matter safe.

Status: **dangerous reassembly implemented; containment interaction unfinished.**

### Containment

Required behavior:
- Replicators and recovered Replicator Matter should recognize effective containment where appropriate;
- containment must matter to escape/breach/reassembly decisions rather than be flavor text;
- Burrowers should be the specialist most capable of defeating physical containment;
- player-controlled Replicators must not treat their own colony containment as a hostile breach objective.

Status: **unfinished — dependency: concrete containment behavior/Defs must be implemented.**

### Swarm coordination / AI

Required behavior:
- local swarm members should not act as unrelated independent pawns;
- Controllers provide stronger coordination;
- specialists select jobs appropriate to their role;
- target focus, repairing, breaching and artillery support should cooperate where practical;
- avoid expensive whole-map per-tick scans; use bounded/interval-based decisions.

Status: **unfinished — current ThinkTree provides assimilation + LordDuty + wandering only.**

### Bounded population / growth

Required behavior:
- prevent uncontrolled tick-heavy self-replication;
- growth should depend on available matter and tunable limits/conditions;
- death-split children are transformation mass, not free new threat mass;
- autonomous matter reassembly must also remain bounded.

Status: **unfinished — individual assimilation has per-event offspring limits, but no coherent map/swarm population cap/budget exists yet.**

### Player-owned safety / control

Required behavior:
- player-owned Replicators must obey player control rather than autonomously consume player assets;
- their specialist/adaptation functions must respect player ownership;
- player-controlled bodies must not silently join hostile autonomous swarm domains unless a real feral/override/control transition occurs.

Status: **partial — current assimilation blocks player-owned/player-controlled Replicators; broader ownership/control semantics unfinished.**

### Child's Toy / player Replicator branch

Vardath clarification, 2026-09-10:
- **Child's Toy is a player-owned mech.**
- It remains player-owned while controlled/non-feral.
- **If it goes feral, it transforms into an ordinary Replicator Drone.**
- After that transformation it follows the normal Replicator Drone/autonomous-hostile behavior/domain unless another real control mechanic subsequently changes it.
- Historical gestation/feral timing remains tunable and must not be buried as magic numbers.

Historical public implementation is reference evidence only; the current rebuild must reconstruct this cleanly against the new block-state/control system.

Status: **unfinished — player mech Def/behavior, gestation/feral transition and Drone conversion need implementation.**

### Autonomous faction / threat roster

Required behavior:
- autonomous hostile block Replicator swarm faction;
- raid/threat roster can include ladder forms and specialist bodies at appropriate weights;
- later mixed block + human-form raid composition remains allowed where appropriate.

Current problem: current faction combat options list Drone, Hunter, Bulwark and Controller only; Titan, Siege Mass, Repairer, Burrower and Artillery are absent.

Status: **partial — faction exists; full roster/threat composition unfinished.**

### Core Fragment progression interface

Core Fragment is planned salvage for later research, containment and reconstruction/player systems. It should not be presented as completing those later mechanics by itself.

Status: **implemented resource; later research/reconstruction dependency recorded.**

### Human-form / Asuran / Queen sovereign dependencies

Tracked now, implemented later in the human-form layer:
- block Replicators remain mechanically distinct from human-form Replicators/Asurans;
- mixed raids can intentionally contain both;
- exact Queen has broader sovereign access to appropriate block Replicators;
- Sovereign Neural Lattice implant control is bounded and target-specific, not Queen identity;
- temporary Asuran lattice intrusion is another separate override state;
- if Asurans physically capture the Queen, later suitable Lattice threats gain genuine sovereign block-Replicator access.

Status: **unfinished — dependency recorded for later human-form/Queen implementation; current block state/control architecture must not make this impossible.**

## Implementation order from this reconciliation

1. Replace single-adaptation state with multi-adaptation/save-safe state and improve split/recombine merge semantics. **State portion implemented; later control-domain extension remains dependent.**
2. Implement adaptation effects/visual overlays that can be supported now; preserve explicit dependencies for Grav and anti-shield integration where later concrete systems are needed.
3. Implement Controller, Repairer, Burrower and Artillery actual behavior.
4. Improve assimilation target scoring and bounded population/growth.
5. Implement containment interaction and ensure matter reassembly respects it.
6. Implement broader swarm coordination/role AI.
7. Implement complete player-owned control semantics and Child's Toy player-mech -> feral -> normal Replicator Drone transformation.
8. Expand autonomous threat roster appropriately.
9. Reconcile the entire inventory again before leaving the block Replicator foundation.

Every item above must finish the Replicator pass as **implemented**, **unfinished with dependency recorded**, or **explicitly changed/rejected by Vardath**. There is no forgotten state.
