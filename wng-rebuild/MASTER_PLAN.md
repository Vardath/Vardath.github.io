# WNG RimWorld 1.6 — Rebuild Master Plan and Continuity Contract

Last consolidated: 2026-09-10

**Interpret this together with `CORRECTIONS_LOG.md`. Newer Vardath corrections override older wording below. In particular, any “locked/canonical/protected” wording means a current first-build target, not immutable design law. Do not recreate anti-regression/release-check bureaucracy.**

Author/design authority: **Vardath**.

## How to use this document

When told “refresh memory and continue” or equivalent:

1. Read `wng-rebuild/REFRESH_MEMORY_AND_CONTINUE.md`.
2. Read `wng-rebuild/CORRECTIONS_LOG.md`.
3. Read this plan and the active subsystem contract(s).
4. Fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` before editing.
5. Continue implementation rather than stopping after a summary.
6. Historical/private builds are reference evidence only; there are no known-good historical states.
7. Newer explicit Vardath instructions override this file and should be appended to the continuity record.

## Rebuild mission

WNG is a complete professional RimWorld 1.6 mod. The current reset instruction is to rebuild the public 1.6 repository from scratch, preserving only approved block Replicator graphics and the intended Replicator behavior or reconstructing that behavior cleanly. Everything else is to be rebuilt from requirements rather than copied wholesale from old code.

The first complete build should be coherent, functional, save-safe where state matters, optional-mod safe, visually coherent and actually playable. Avoid orphan Defs, missing PawnKinds/classes, impossible recipes, dead research, fake functionality and descriptions that promise mechanics that do not exist.

Do not mistake “first-build target” for permanent law. Timers, races/xenotypes, castes, sounds, art, resources, balance, quests, progression, UI, processes and whole systems remain editable by Vardath.

# 1. Identity model

Keep race/xenotype/caste/PawnKind/faction/backstory concepts separate.

Wraith hierarchy for the current design:

**Wraith identity/xenotype -> caste/PawnKind -> faction role/behavior -> optional biography/backstory**

Current Wraith caste roles include Hunter, Warrior, Commander, Keeper and Queen, plus player variants where useful. These are castes/roles, not separate races just because their behavior differs.

Backstories are biography/history only. They are not races, xenotypes or castes.

Human-form Replicators/Asurans are nanite humanoids using Human-pawn systems plus their own xenotype/genes/roles. They are distinct from mechanical block Replicator custom forms.

Block Replicators are mechanical forms with their own hierarchy, matter economy, adaptation and swarm behavior.

# 2. Block Replicator foundation — preserve/reconstruct first

Approved block Replicator graphics are the only existing mod assets explicitly carried into the clean reset. Preserve their directional graphics and adaptation/resource art unless Vardath later requests changes.

Core behavior to reconstruct cleanly:
- technological infestation behavior;
- consume accessible matter/technology and turn successful consumption into a matter/resource economy;
- player-owned Replicators must not autonomously eat the player colony;
- bounded population/growth rather than uncontrolled tick-heavy spawning;
- EMP suppression;
- containment awareness where appropriate;
- learned adaptation from successfully assimilated technology/materials;
- swarm coordination and specialist/support bodies;
- save-persistent state only where needed for actual behavior.

Current hierarchy intent:
- base/Drone is irreducible;
- small forms can recombine into larger forms when enough same-domain units/material/conditions are present;
- larger forms split downward on genuine destruction instead of disappearing;
- intentional upward recombination consumption must not trigger accidental death-split;
- state/material/adaptation/control should survive appropriate hierarchy transitions.

Current first-build death ladder is:

**Siege Mass -> Titans -> Bulwarks -> Hunters -> Drones/base**

Historical counts were two children per step. Historical split-born recombination delay was about one in-game hour. Treat counts/timing as editable defaults, not permanent constraints.

Specialists historically included Controller, Repairer, Burrower and Artillery/Siege-style bodies. Preserve the functional idea, not necessarily every old implementation detail.

Replicator Matter remains dangerous salvage capable of reassembly/self-assembly when sufficient material remains. Historical minimum/delay values are reference defaults only and should be centralized/tunable rather than scattered.

Child’s Toy/player Replicator remains an intended branch: friendly player content with its own gestation/feral behavior. Historical gestation/feral timings are tunable.

# 3. Replicator adaptation

Adaptation must be earned by actual interaction/assimilation, not arbitrary flags.

Examples:
- weapons/turrets -> ranged/weapon adaptations;
- armor/material -> protection/material adaptation;
- shield technology -> shield adaptation;
- power systems -> power adaptation;
- gravtech -> grav capability;
- Asuran/advanced precursor systems -> advanced learned effects.

Adaptation should matter in gameplay and be represented visually where useful. Do not create a rigid audit that forbids later adaptation redesign.

# 4. Replicator faction/raid composition

Autonomous block swarm and human-form/Lattice content are distinct but may interact.

Current design supports:
- hostile autonomous block Replicator swarm;
- hostile human-form/Lattice/Asuran faction;
- non-hostile human-form enclave/Quiet Lattice content;
- player human-form variants;
- player block Replicators/Child’s Toy;
- mixed block + human-form raid groups where appropriate.

Do not confuse block recombination rules with raid composition: block growth can stay block-only while mature/advanced raids contain human-form units.

# 5. Human-form Replicators / Asurans

Human-form Replicators are synthetic nanite humanoids, not reskinned block machines.

Current role ideas:
- engineer;
- infiltrator;
- soldier;
- coordinator/commander;
- player-aligned variants.

Nanite physiology intent:
- ordinary Food need can remain as feedstock intake;
- effectively no ordinary food-poisoning outcome;
- visible Nanite Reserve or equivalent internal resource;
- eating/feedstock can replenish reserve;
- reserve should not passively vanish just because time passes unless design changes;
- reserve powers accelerated repair/reconstruction;
- EMP disrupts reconstruction/collective functions.

Historical first-build tuning used reserve costs and fast/emergency heal timers. Do not bury these as immutable constants. Centralize/tune them after functional implementation.

Neural Interface intent:
- recruit/imprison/enslave where game/DLC rules permit;
- acquire/copy skill/personality/pattern data;
- create/reconstruct human-form synthetic copies where intended;
- exact copy should preserve biography/name/skills/passions/appearance/genome source data before nanite layering;
- generated synthetic backstories must not overwrite an exact copied person’s real history;
- failed copy placement must not spend the full resource cost;
- no free duplication loop.

Infiltration must become a real mechanic: infiltrators can appear human until scanning, injury or suspicious behavior reveals synthetic nature. Do not leave this as flavor text only.

# 6. Replicator Queen

Detailed current design is in `REPLICATOR_QUEEN.md`.

Current first-build Queen:
- one exact human-form Replicator individual;
- female;
- age 13 in current design;
- unique sovereign authority belongs to that exact pawn, not every human-form Replicator;
- held in a real cryosleep/cryptosleep chamber at a precursor-style site;
- when released/spawned, recruited to the player immediately;
- release triggers hostile Asuran/Lattice recovery attempt;
- hostile capture only commits after physical carrier exits the map with her;
- later occasional capture raids may target a home map only when the Queen is physically present there;
- successful hostile capture gives Lattice genuine sovereign block-Replicator access in suitable future threats, not a fake +1 outbreak bonus.

Queen innate authority and Sovereign Neural Lattice implant authority are separate. Implant bearer is not a Queen and has bounded target-specific control. Temporary Asuran lattice intrusion is another separate temporary override system.

Do not hard-code old day-84 discovery. Pacing must suit short campaigns and remain tunable.

# 7. Wraith identity and Life Force

Wraith are one current identity/xenotype with caste PawnKinds/roles.

Life Force is the central feeding/regeneration resource.

Current full Drain Life/Wither design:
- one coherent full-feed ability rather than duplicated competing abilities;
- touch-range biological target;
- victim ages substantially; historical current target +50 biological years;
- feeding Wraith de-ages; historical current target -5 years with adult floor around 18;
- victim gets temporary Life Drained state;
- Wraith gets temporary Fed Recently state;
- repeated full feeding before recovery may become lethal;
- partial feeding can remain distinct;
- low Life Force throttles regeneration;
- depletion can cause torpor;
- high reserve supports expensive healing/missing-part recovery;
- hibernation greatly reduces Life Force use.

These numeric values are current tuning targets, not immutable constants.

Gene overwrite/deduplication must not permanently remove WNG gene-granted ability gizmos.

Wraith appearance should strongly enforce pale/white/colorless hair, with long straight Wraith-like hair preferred where feasible. Appearance remains editable.

# 8. Strategic Wraith faction hunger — separate system

This correction is essential.

Ordinary Wraith feeding ability does **not** open a faction feeding-request popup.

Strategic hunger belongs to Wraith factions/lineages and influences:
- when a faction genuinely needs feeding access/subjects;
- likelihood/timing of feeding requests;
- attack/raid pressure when hunger is unresolved/refused.

A request popup appears only when a faction is genuinely strategically hungry and asks for feeding subjects/access. If the player refuses/does not accept, attack likelihood rises according to faction behavior.

This is not necessarily a generic quest system.

Current multi-stage request UI intent:
- first stage identifies relevant feeding-stock/prisoner subject(s);
- player does not choose individual Wraiths in the first modal;
- next stage shows count/names of involved Wraiths;
- decision flow remains paused until complete.

Keep this system completely separate from ordinary Drain Life and from mature-Hive local feeding stock.

# 9. Wraith factions/politics

Current lineage concepts:
- Sable Brood — uncompromising hostile predatory Hive;
- Cinder Court — militant Queen-led Hive, aggressive but politically mutable;
- Veiled Hive — cautious/selective/concealment-oriented, can negotiate;
- Pale Covenant — exile/offshoot capable of coexistence/trade if supplied appropriately.

Wraith factions:
- raid independently of Stargates/ONAC/RimGate;
- use caste-appropriate composition;
- maintain lineage-specific diplomacy;
- retain exact faction identity through captivity/rescue/retaliation where required.

Faction design is an intended first-build structure and can be revised by Vardath later.

# 10. Wraith prisoners, feeding stock, thralls and rescue

Wraith gameplay should support real pawn identity through:
- abduction;
- captivity;
- feeding stock;
- prisoner feeding;
- thrall/experiment/hybrid content where retained;
- rescue/recovery of exact abducted pawns.

Do not replace a kidnapped real pawn with a fake proxy victim. Save/load must preserve exact pawn/faction ownership where the story depends on it.

# 11. Mature Wraith Hive ecology

Mature Hive is local ecology, distinct from strategic hunger.

Current intended features:
- bounded active Wraith population;
- caste-correct Queen/Keeper/etc.;
- ordinary hibernating Wraith population in Hibernation Pods;
- separate finite Dormancy Vault combat reserve where useful;
- finite biological feeding-stock captives;
- Feeding Niches holding exact captives;
- Hive Heart/biological infrastructure;
- bounded replacement/growth rather than infinite spawning;
- exact site-faction ownership;
- dormant occupants stay dormant until valid wake conditions;
- failed site generation cleans up partial state.

Neutralizing a hostile mature Hive can trigger delayed retaliation tied to the lineage/site. That retaliation is separate from strategic hunger request UI.

Historical delays are tuning references only. Make story timing editable/centralized.

# 12. Wraith living technology

Wraith technology should feel grown/organic/biomechanical rather than generic industrial crafting.

Current progression concepts:
- biological interaction/implantation starts the chain;
- Living Forge/workshop can be grown from a living host and also from a corpse where that route remains useful;
- Wraith Grav Engine growth/implant progression similarly supports living-host/corpse use where appropriate;
- incubation timings are tunable;
- do not accidentally restore obsolete “Gravcore” where the intended functional object is the **Wraith Grav Engine**.

Living weapons/buildings should have real functions and Wraith organic visual language.

# 13. Native backstories

Use RimWorld 1.6 `BackstoryDef` when native WNG biographies are implemented.

Historical first-build target was 30 WNG backstories: six origins/childhood and twenty-four adult histories across Wraith and synthetic roles. Treat count/content as editable if Vardath changes it.

Wraith origin ideas:
- Hive creche broodling;
- Living-ship broodling;
- Feeding-court ward.

Synthetic origin ideas:
- Archive-born template;
- Constructed service pattern;
- Recovered biological imprint.

Role pools should align with caste/role but never substitute for race/xenotype/caste identity. Block Replicators receive no human childhood/adulthood biography filtering.

Keep bonuses modest and coherent; avoid forced traits/body types/work bans just to balance a role.

# 14. Discovery / ruins / story progression

Theme:

**mystery -> encounter -> evidence -> understanding -> reconstruction -> mastery**

Historical progression used a long sequence stretching from day 20 to day 84. Vardath explicitly rejected that pacing because colonies can become performance-bound around day 20.

Do not reuse that schedule as hard-coded gating.

Rebuild discoveries so major WNG content becomes reachable within short campaigns, while not dumping everything at once. Story pacing should be author-tunable through Defs/settings/centralized configuration and can also consider storyteller/threat/readiness conditions.

Historical site concepts still useful as content ideas:
- ruined Wraith laboratory;
- Replicator-consumed ruin;
- Ancient/precursor laboratory;
- abandoned Wraith cloning installation;
- precursor vault;
- dormant Asuran facility;
- deceptive Ancient survey annex / hidden Asuran reveal;
- Replicator Queen vault.

Advanced technology should initially come through encounters, salvage, analysis, damaged evidence and reconstruction rather than a giant starting research dump.

# 15. CatCraft Stargates! integration

CatCraft Stargates! is optional.

Ownership boundary:
- CatCraft owns gate network/address/dial/iris/shield/receive-buffer mechanics;
- WNG owns WNG incidents, corridors, craft, objectives and outcomes;
- no replacement Stargate network;
- no hard dependency;
- avoid Harmony takeover where native/API integration works;
- do not steal CatCraft receive-buffer ownership.

Wraith Dart hostile corridor current intent:
- two real flyover/culling passes in the current first-build design;
- each pass performs real culling/abduction rather than decorative animation;
- exact abductee identities persist into captivity/rescue;
- after passes, transition to intended final craft state.

Pass count may be changed later by Vardath; do not encode it into an anti-regression test.

Friendly Puddle Jumper/Quiet Lattice courier behavior is separate from hostile Dart behavior. Historical friendly delegation concept: CatCraft gate arrival + normal neutral visitors + real finite WNG Puddle Jumper courier then departure, without inheriting hostile Wraith sabotage/culling/capture behavior.

# 16. ONAC / RimGate compatibility

ONAC/RimGate own their Goa’uld/Tok’ra/Jaffa systems.

WNG should recognize/integrate where appropriate without duplicating them and must remain safe when optional mods are absent.

Replicators can be treated as extreme technological threats; Wraith as rival-power actors. Do not hard-depend on optional systems.

# 17. Craft/shuttles

Primary WNG craft concepts:
- Wraith Dart;
- Puddle Jumper;
- Wraith Strike Craft;
- Wraith Cruiser.

Each should actually work through the full player/game path:

**board -> load -> fuel -> launch -> world/Stargate use -> save/load**

Prefer native Odyssey passenger-shuttle behavior where possible. Do not preserve a disabled “Get in shuttle” merely because a static test says it is native. Avoid custom right-click transporter hacks when normal Odyssey behavior can be made to work.

Craft should have distinct roles, graphics, event behavior and appropriate audio.

# 18. Gravships

Current plan has two distinct Odyssey-compatible gravship families:
- Wraith;
- Asuran/Precursor.

Use vanilla Odyssey gravship behavior wherever practical while maintaining distinct WNG visual/resource identity.

Families should not accidentally cross-connect/consume each other’s fuel/resources.

Each family should ultimately have real:
- hull/substructure;
- walls/corners/diagonals/transitions;
- functional Grav Engine;
- pilot console/node;
- fuel storage/feed;
- thrusters;
- field extenders;
- shields;
- support modules;
- power conduits/network topology.

Wraith visual language: organic, grown, asymmetrical, biomechanical, internal glow.

Asuran visual language: precise, clean, geometric, Ancient-derived, nanite-engineered.

Historical resource names/ideas:
- Wraith bio-fluid propellant (`WNG_WraithBiofluidFuel`);
- Asuran nanite slurry (`WNG_AsuranNaniteSlurry`).

Names/values can be revised, but do not accidentally revert to obsolete cultured-biomass shuttle fuel or Gravcore behavior when current intent is different.

Power/fuel conduits should use connected graphics and turn correctly. Hull topology must look intentional rather than merely technically connected.

# 19. Art direction

Professional cohesive quality is expected.

Approved block Replicator graphics are being preserved through the reset.

Other art should be rebuilt/reviewed as content is implemented:
- pawns;
- buildings;
- apparel/worn facings;
- weapons/wielded graphics;
- genes/abilities;
- resources;
- craft;
- gravship parts;
- furniture/environment structures.

Avoid generic repeated icons, missing textures, placeholder panels, bad transparency/chroma remnants and missing directional variants.

Do not generate new image assets unless Vardath explicitly asks for image generation/art creation in that task.

# 20. Audio

Professional audio remains part of the intended mod. Historical planning mentioned around 30 distinct cues, but count is not immutable.

Useful cue families:
- Replicator metallic/electrical clickety-clack movement;
- assimilation;
- assembly/recombination;
- splitting/reproduction;
- power/adaptation;
- Wraith weapons;
- living-tech growth/operation;
- Wraith drives/interfaces;
- culling/craft;
- Hive ambience;
- Asuran/precursor/nanite systems.

Judge audio in game for mix/loudness/repetition/theme rather than by waveform/static checks alone.

# 21. Research and acquisition

Research should unlock real usable content and fit the fiction.

Avoid unreachable prerequisites, missing rewards, impossible recipes and generic bench crafting that contradicts biological/reconstruction systems.

Use discovery, salvage, analysis, growth, reconstruction, faction encounters and ruins/vaults.

Implants/medical operations need valid body targets, ingredients/research/worker behavior/removal where appropriate.

# 22. Save/load / transaction safety

Only persist state that gameplay actually needs, but do it correctly.

Examples:
- Replicator split/recombine transaction state;
- material/adaptation/control inheritance;
- temporary lattice overrides;
- Queen exact pawn/capture state;
- Wraith exact abductees/captivity;
- Neural Interface copies;
- nanite reserve/reconstruction timers;
- strategic hunger/request state;
- Stargate corridor/craft state;
- living-tech incubation;
- mature-Hive population/retaliation.

At-most-once gameplay transactions should stay at-most-once through reload: no duplicate split children, Queen, victims, rewards, craft, transformations or double resource spending.

# 23. Compatibility/performance

WNG must coexist with a large mod stack.

Prefer local components/native systems over brittle global Harmony patches.

Do not attempt to repair unrelated external-mod errors inside WNG unless evidence shows WNG owns/triggers the problem.

Avoid heavy per-tick global scans where less frequent/local event-driven logic works. Vardath’s games can become tick-bound early, so performance is a real design constraint.

Optional integrations must fail safely when absent.

# 24. Testing philosophy — corrected

The previous rebuild accumulated many anti-regression and release-check audits that began dictating implementation. Do **not** recreate that system.

Use only what is genuinely useful to implementation:
- C# compile/build when needed;
- basic XML/reference sanity if it catches a concrete error;
- actual in-game testing;
- save/load testing for stateful systems;
- screenshots/log review when diagnosing behavior.

Do not create tests whose purpose is “this timer/count/race/process can never change.” Static tooling does not decide design acceptance. Vardath does.

A successful compile is useful but does not mean a feature is good or final.

# 25. Rebuild order after the 2026-09-10 reset

1. Preserve approved Replicator graphics/resources.
2. Reconstruct block Replicator defs/faction/PawnKinds and behavior: matter economy, hierarchy split/recombine, swarm jobs, EMP, adaptation, specialists, control and player safety.
3. Make that foundation compile/play without importing old design-lock tooling.
4. Rebuild Wraith xenotype/identity and caste PawnKinds/factions.
5. Rebuild Life Force, full/partial feeding, regeneration, hibernation and appearance.
6. Rebuild strategic faction hunger separately from ordinary feeding.
7. Rebuild Wraith captivity/rescue, Feeding Niche, Growth Chamber, Hive Heart, Dormancy/Hibernation infrastructure and mature-Hive ecology.
8. Rebuild Wraith living-tech progression and Grav Engine.
9. Rebuild human-form Replicators/Asurans, nanite physiology, Neural Interface, infiltration, factions and backstories.
10. Rebuild Queen vault/recruitment/recovery raids/sovereign consequences using `REPLICATOR_QUEEN.md`.
11. Rebuild discovery/story progression with tunable short-campaign pacing.
12. Rebuild optional Stargate/ONAC/RimGate interactions.
13. Rebuild craft/shuttles.
14. Rebuild Wraith and Asuran gravship families.
15. Complete/review professional art/audio.
16. Live-test, tune and freely revise anything Vardath dislikes.

# 26. Things not to repeat from failed process

- Do not call a historical state “known good.”
- Do not assume a green audit means gameplay is correct.
- Do not let an audit force correct gameplay backward to satisfy stale strings.
- Do not confuse backstories with races/castes.
- Do not turn Wraith castes into separate races by accident.
- Do not trigger strategic feeding popup from ordinary Drain Life.
- Do not conflate mature-Hive feeding stock with strategic hunger.
- Do not make Queen capture a flat autonomous-outbreak count bonus.
- Do not make Queen neutral after casket release; she joins player immediately.
- Do not schedule Queen content so late that a normal Vardath colony never sees it.
- Do not replace day 84 with another buried magic number.
- Do not recreate “locked/canonical/protected” constant classes just to satisfy old planning language.
- Do not recreate the giant anti-regression/release-check framework.
- Do not require private-repo access for continuity.
- Do not generate replacement art unless asked.

# 27. Final authority rule

This plan is a memory and implementation guide. **Vardath can change any part of it.**

If Vardath says a current result is wrong, update the plan/continuity notes and change the mod. Do not argue that an earlier plan, audit, commit or assistant statement makes the old behavior permanent.
