# WNG rebuild — corrections and process history

This file records explicit Vardath corrections. These notes override older assistant assumptions and old source behavior. Preserve this file when the plan evolves; append new corrections instead of erasing history.

## Process corrections

### No known-good state
Vardath repeatedly corrected the assumption that an older build/commit was “known good.” There are **no known-good historical WNG states**. Old public/private builds can be inspected only for design/reference evidence.

### Rebuild rather than patching accumulated damage
The active instruction is to rebuild cleanly. Do not keep repairing a tangled current implementation merely because work already exists.

### Preserve Replicator graphics/behavior, rebuild everything else
For the 2026-09-10 reset, keep the approved block Replicator graphics and preserve/reconstruct the intended Replicator behavior. Everything else is to be rebuilt from the plan.

### Vardath is the author/design authority
The mod author is **Vardath**. The assistant implements Vardath’s design and may propose implementation details, but must not convert those proposals into permanent doctrine.

### Nothing is set in stone
Vardath explicitly stated that timers, races, sounds, art, processes, systems, balance and the entire mod can be changed later if the results are unsatisfactory.

Therefore any older plan language such as “locked,” “canonical,” “protected,” “must remain stable,” or similar means only “current intended first-build behavior” unless Vardath explicitly says a detail is immutable.

### No hard-coded design doctrine
Do not scatter author-tunable behavior through magic constants. Story/event timing in particular must be adjustable and must not repeat the day-84 mistake. Prefer Defs/settings/configuration/centralized parameters.

This does **not** ban every literal constant in programming. Internal polling intervals, algorithmic invariants and technical values may be constants where appropriate. The rule is against burying design/balance choices so they are painful to change.

### No anti-regression/release-check bureaucracy
Vardath explicitly rejected the large anti-regression/audit/release-check framework that had started to dictate the design.

Do not rebuild it. Only use checks that are genuinely necessary to implement a functioning mod, such as compilation or a small reference-validation check when it catches a concrete breakage. Static tests must never decide design acceptance.

### Public repo only for current continuity
Private repo work is currently unavailable/undesired because private credits were exhausted. Keep enough requirements in this website repo and work against public `Vardath/Wraith-Nanite-Gravtech-1.6`. Do not spend private-repo credits or require private access.

### Do not waste chat turns
Read the continuity documents and current repo first. Do not ask questions already answered in the plan/history.

### Do not omit features — standing correction
Vardath explicitly corrected the fresh reset after Shield Replicators and the wider Replicator hierarchy/adaptation branches were omitted from the initial scaffold.

**Standing rule: do not omit any feature.** Every feature, subsystem, branch, faction, caste, race/xenotype, PawnKind, Replicator form, adaptation path, quest, event, integration, craft, gravship component, resource, art/sound family, UI flow and behavior recorded in the current plan/history must either be implemented or remain explicitly tracked as unfinished. Never silently simplify it away because it is difficult, secondary, inconvenient or appears redundant.

A temporary partial scaffold may exist during implementation, but it must be identified as partial and cannot be treated as the finished subsystem. Before moving on, compare the subsystem against the whole plan/history and account for all known branches.

## Gameplay/design corrections

### Wraith feeding request popup
The popup/request is **not** triggered by a normal Wraith using Drain Life or feeding.

It appears only when a Wraith **faction** becomes strategically hungry enough to request feeding subjects/access. If the player refuses or does not accept the genuine request, raid/attack likelihood rises. This is strategic faction pressure, not an ordinary pawn ability and not necessarily a generic quest.

### Mature Hive vs strategic hunger
Mature-Hive feeding stock is local Hive ecology. It must not trigger the strategic feeding-request popup. Mature-Hive neutralization retaliation is another separate system.

### Wraith castes
Wraith have castes. Hunter, Warrior, Commander, Keeper, Queen, etc. are Wraith caste/PawnKind roles under the Wraith identity, not separate races.

### Backstories
Backstories are not races. They are biography/history and must not be used as race/caste identity.

### Replicator hierarchy/adaptation branches
The initial fresh-reset scaffold incorrectly reduced the Replicator design to the primary combat ladder plus a few placeholder specialists. Vardath corrected that omission.

The rebuild must account for the full recorded Replicator ecology, including the primary size ladder **and** specialist/adaptation branches. In particular, **Shield Replicators / shield adaptation are not optional**, including the learned shield specialization and later anti-shield/countermeasure development recorded in the prior design. Controller, Repairer, Burrower, Artillery, ranged, armor, power and grav adaptations must likewise remain represented/tracked. Exact balance and implementation may be redesigned, but the features may not silently disappear.

### Clarification: “other hierarchy” means the physical small-to-large ladder
Vardath clarified that the hierarchy being referred to is the full physical size/combat chain and its two-way transformation behavior:

**Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass** upward through recombination, and **Siege Mass -> Titan -> Bulwark -> Hunter -> Drone/base** downward through genuine destruction breakup.

Split-born children must be prevented from immediately recombining for approximately **one in-game hour** in the current design (historically 2,500 ticks). This exists specifically so destroying a Siege Mass/Titan does not produce children that instantly rebuild the same large threat and make the big Replicator appear immortal. The delay is a tunable gameplay parameter, not a design-lock audit rule.

### Replicator graphics as completeness evidence
The approved retained `Textures/Things/Pawn/Replicator` tree itself must be inventoried when reconstructing the Replicator roster. The reset retained graphics for Drone, Hunter, Bulwark, Titan, Siege Mass, Controller, Repairer, Burrower and Artillery plus adaptation overlays for Armor, Ranged, Power, Grav and Shield. Do not copy the graphics tree and then rebuild an incomplete Def/behavior roster from memory alone.

### Replicator split behavior
Large combined block forms must break down into smaller existing forms when destroyed rather than simply disappearing. The transformation state/material economy should survive where appropriate; intentional upward recombination consumption must not accidentally trigger death splitting.

### Human-form Replicators
Human-form Replicators/Asurans are distinct from block Replicator custom races. They are nanite humanoids with appropriate xenotype/genes/PawnKinds and collective/reconstruction/interface systems.

### Mixed raids
Human-form + block Replicator raid composition can be intentional. Do not prohibit mixed raids just because block recombination is block-only.

### Replicator Queen
Current first-build design:
- one exact female human-form Replicator Queen;
- age 13 in the current design;
- discovered in a real cryosleep/cryptosleep chamber;
- she is recruited to the player immediately when released/spawned;
- hostile Asuran/Lattice operatives attempt to capture her during the vault encounter;
- later, while she remains player-owned, the Asurans may occasionally raid a home map where she is physically present specifically to capture her;
- no capture raid should target a different home map while she is absent/traveling/off-map;
- capture commits only after a hostile carrier physically exits the map with the exact Queen pawn;
- if interrupted before exit she remains recoverable/player-owned;
- if captured, the Lattice gains real sovereign block-Replicator access in appropriate future threats rather than an arbitrary `+1 outbreak` bonus.

### Queen pacing correction
The old “day 84” vault timing was rejected as absurdly late for Vardath’s actual games, which can bog down around day 20. Major WNG content should be reachable much earlier.

Do not replace day 84 with another buried magic number. Rebuild discovery/event pacing so it is tunable and suitable for short campaigns. Eligibility should not mean every event is forcibly dumped on the player at once.

### Grav Engine
A Wraith **Grav Engine** is intended. Do not accidentally restore obsolete “Gravcore” naming/content where the engine should be.

### Wraith appearance
Wraith hair should be strictly pale/white/colorless rather than ordinary random human colors. Long straight Wraith-appropriate hair is preferred where feasible. This is tunable presentation, not a separate race definition.

### Wraith Drain Life
Current first-build behavior remembered from Vardath:
- full Drain Life/Wither is one coherent ability;
- victim biological age increases substantially (current target +50 years);
- Wraith biological age decreases (current target -5 years), not below adulthood/current target age 18;
- victim gets temporary Life Drained state;
- Wraith gets temporary Fed Recently state;
- duplicated/overwritten genes must not permanently lose their granted ability gizmos.

Exact numeric values may be tuned after testing.

### Wraith living-tech bootstrap
Living Forge/workshop and Grav Engine progression should support corpse use as well as a living host where that system remains in the first build, so testing/progression is not dependent on keeping a living victim available.

### Art generation
Do not generate new images merely because graphics are being audited. Vardath has explicitly instructed not to generate images unless asked.

## 2026-09-10 full reset
Vardath explicitly ordered:

- copy the full plan/refresh material to the website repository;
- delete the 1.6 repo working contents;
- start WNG again;
- keep only approved Replicator graphics and intended Replicator behavior, or reconstruct that behavior cleanly;
- rebuild according to the accumulated plan and corrections;
- no hard-coded design doctrine;
- no anti-regression or release-check machinery unless absolutely necessary for implementing a functioning mod.
