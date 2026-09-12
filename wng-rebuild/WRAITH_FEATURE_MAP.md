# WNG — Wraith subsystem feature map

Author/final design authority: **Vardath**.

This is a **design/relationship map only**. It is not an implementation checkpoint, current-state inventory or next-task list. The master plan + active append(s) + corrections define the target; actual public `Vardath/Wraith-Nanite-Gravtech-1.6` source defines what is already implemented.

Do not infer present absence/completion from this file.

# Identity model

Required relationship:

**Wraith identity/xenotype -> caste/PawnKind -> faction role/behavior -> optional biography/backstory**

Wraith are one Wraith identity/xenotype, not separate races per caste.

Current caste/PawnKind roles include at minimum:
- Hunter;
- Warrior;
- Commander;
- Keeper;
- Queen.

Player-aligned variants may exist where useful, but remain the same Wraith identity rather than duplicate races.

Backstories are biography/history only. They do not define race, xenotype or caste.

# Wraith appearance

Current first-build presentation goals:
- strongly pale/white/colorless hair rather than ordinary random human colours;
- long straight Wraith-appropriate hair preferred where feasible;
- caste distinction primarily through role/apparel/behavior rather than separate races;
- presentation remains author-editable.

# Life Force — core biological resource

Life Force is central to feeding/regeneration/torpor behavior.

Required relationships:
- feeding raises Life Force;
- regeneration consumes/is throttled by Life Force;
- severe depletion can produce torpor/incapacitation;
- high reserve can support expensive healing/missing-part recovery;
- hibernation greatly reduces Life Force use;
- meaningful state survives save/load.

Capacities, drain rates and healing costs remain tunable/centralized where practical.

# Drain Life / Wither — ordinary pawn-level feeding

Current first-build full-feed target:
- one coherent Drain Life/Wither ability rather than duplicate competing abilities;
- touch-range valid biological target;
- victim biological age increases substantially, current target +50 years;
- feeding Wraith biological age decreases, current target -5 years, with adult floor around 18;
- victim receives temporary `Life Drained` state;
- Wraith receives temporary `Fed Recently` state;
- repeated full feeding before recovery may become lethal;
- partial feeding may remain a distinct smaller action;
- feeding modifies Life Force appropriately;
- duplicated/overwritten genes must not permanently lose granted ability gizmos.

Exact values remain tunable.

**Ordinary Drain Life does not open the strategic faction feeding-request UI.**

# Regeneration / biological recovery

Required behavior:
- Wraith heal more aggressively than ordinary humans where Life Force permits;
- low Life Force throttles regeneration;
- depletion may push Wraith into torpor rather than granting free healing;
- high reserve may recover severe injury/missing parts at appropriately high cost;
- bioelectric/EMP interactions must be coherent where relevant;
- rates/costs remain tunable.

# Strategic Wraith faction hunger — separate system

Strategic hunger belongs to factions/lineages, not ordinary pawn feeding.

Required behavior:
- each relevant Wraith faction has its own strategic feeding pressure;
- genuine strategic hunger determines when that faction needs feeding access/subjects;
- only genuine strategic faction hunger may create the feeding-request UI;
- ordinary Drain Life does not create that UI;
- mature-Hive local feeding stock does not create that UI;
- refusal/non-acceptance/unresolved hunger increases raid/attack pressure according to faction behavior;
- state remains faction-specific rather than global.

Current request UI intent:
- first stage identifies appropriate prisoner/feeding-stock subject(s);
- player does not choose individual Wraiths in the first modal;
- a following stage shows the exact count/names of involved Wraiths;
- the decision flow stays paused until complete;
- cancellation/refusal uses the strategic-hunger consequence path, not ordinary feeding logic.

# Mature-Hive feeding ecology — separate system

Mature-Hive feeding stock is local site/Hive ecology.

Required behavior:
- finite biological captives/feeding stock;
- Feeding Niches hold exact captive pawns where used;
- feeding stock belongs to the local Hive ecology;
- local depletion/replacement is bounded;
- local Hive feeding does not trigger strategic faction hunger request UI.

# Mature-Hive retaliation — separate system

Neutralizing a hostile mature Hive may create delayed retaliation tied to the relevant lineage/site.

This is separate from:
- ordinary Wraith feeding;
- strategic faction hunger/request UI;
- local mature-Hive feeding ecology.

Timing remains tunable and must not be buried as an old fixed schedule.

# Wraith factions / politics

Current lineage concepts:
- **Sable Brood** — uncompromising hostile predatory Hive;
- **Cinder Court** — militant Queen-led Hive, aggressive but politically mutable;
- **Veiled Hive** — cautious/selective/concealment-oriented and capable of negotiation;
- **Pale Covenant** — exile/offshoot capable of coexistence/trade when supplied appropriately.

Required relationships:
- factions raid independently of Stargates/ONAC/RimGate;
- caste-appropriate composition;
- lineage-specific diplomacy/hostility;
- exact faction identity preserved through captivity/rescue/retaliation where story depends on it;
- strategic hunger belongs to the actual faction/lineage;
- optional Stargate corridors can enhance events/travel but are not required for ordinary Wraith raids.

Future diplomacy/patronage/worship/client-state expansion is recorded in the planned Iratus/diplomacy/Royalty append and must not be implemented until Vardath advances it.

# Wraith captivity / exact-pawn continuity

The design supports exact identity through:
- abduction;
- captivity;
- feeding stock;
- prisoner feeding;
- rescue/recovery;
- later thrall/experiment/hybrid branches where retained.

Do not replace an abducted real pawn with a generated proxy when later story/rescue continuity depends on the exact pawn.

Save/load must preserve exact pawn/faction ownership where required.

# Mature Hive population / castes / infrastructure

Required ecology includes:
- bounded active Wraith population;
- caste-correct Queen/Keeper/etc.;
- ordinary hibernating population in Hibernation Pods;
- finite Dormancy Vault combat reserve where useful;
- finite feeding-stock captives;
- Feeding Niches containing exact captives;
- Hive Heart/biological infrastructure;
- bounded replacement/growth rather than infinite spawning;
- exact site-faction ownership;
- dormant occupants remain dormant until valid wake conditions;
- failed generation cleans up partial state.

# Wraith Growth Chamber

Required role:
- bounded biological Wraith replacement/growth;
- coherent resource/Queen/Hive requirements;
- same-faction/Hive linkage where appropriate;
- caste outcomes limited according to the current plan rather than uncontrolled spawning;
- exact pawn registration/state handled safely before resource commit;
- costs/timers/caps remain tunable.

Generated hostile Mature-Hive placement must not invent an ungrounded electrical/ZPM/Gravcore power source merely to make a Growth Chamber work. Site placement should follow the real Wraith ground-power/bioelectric design when that plan slice is reconciled.

# Wraith living technology

Wraith technology should feel grown, organic and biomechanical rather than generic industrial crafting.

Required concepts:
- biological interaction/implantation begins the progression;
- Living Forge/workshop can use living-host and corpse pathways where the current plan requires them;
- Wraith Grav Engine progression likewise supports the intended biological bootstrap;
- incubation timings remain tunable;
- grown structures/weapons have real functions;
- use **Wraith Grav Engine**, never obsolete Wraith Gravcore semantics.

# Bioelectric / living-power relationship

Wraith bioelectric technology should connect coherently to living-tech/gravship/ground-power needs rather than becoming an arbitrary generic generator label.

Where native Odyssey power behavior correctly supplies the mechanical layer, WNG should use it while preserving Wraith biological identity.

Any future Mature-Hive ground-power solution must be grounded in the plan/lore and must not be invented solely to satisfy another building.

# Wraith weapons / capture tools

Wraith weapons remain real functional systems with caste/faction-appropriate use and organic/biomechanical identity.

The Wraith stun staff is a distinct ranged nonlethal capture weapon:
- zero ordinary projectile health damage on a normal successful shot;
- native stun resistance/`StunHandler` remains authoritative;
- distinct from Drain Life, Dart culling, Goa'uld staff weapons and zats;
- Hunter/Warrior/Commander/Keeper carrier behavior follows the active plan;
- Queen/player Wraith roles are not automatically forced to carry it unless Vardath changes the design;
- final authentic art/audio remains a presentation task.

# Wraith Dart / culling / abduction

The Dart is a core Wraith culling craft/event family.

Current hostile-culling intent:
- exactly two real flyover/culling passes in the current first-build design unless Vardath changes it;
- passes perform actual absorption/culling/abduction, not decorative animation;
- exact abductee identities persist into captivity/rescue systems;
- pilot/craft retreat is physically tied to the real shuttle/native lifecycle;
- Wraith ordinary raids do not depend on Stargates or Dart incidents.

# Stargate integration — optional ownership boundary

CatCraft Stargates! is optional.

Ownership boundary:
- CatCraft owns gate network/address/dial/iris/shield/receive-buffer mechanics;
- WNG owns WNG incidents/corridors/craft/objectives/outcomes;
- no replacement Stargate network;
- no hard dependency;
- do not steal CatCraft receive-buffer ownership;
- avoid Harmony takeover when native/API integration works.

Friendly Quiet-Lattice/Puddle-Jumper courier behavior is separate from hostile Wraith Dart behavior.

# Wraith gravship family

Wraith uses an Odyssey-compatible gravship family with Stargate/Wraith biological identity.

Required family relationships include:
- real Odyssey gravship engine/connected structure behavior;
- Wraith living substructure/hull presentation;
- pilot/control interface;
- Wraith fuel/resource storage/feed;
- thrusters/field/support systems;
- native power network where appropriate;
- family isolation from Asuran/Goa'uld/vanilla hardware except deliberately shared native elements;
- physical fuel-routing where current WNG design uses it;
- vacuum/atmosphere/doors/power/sensors grounded in native Odyssey contracts where they fit;
- correct save/load/launch/construction behavior.

Wraith defensive identity is **living-hull regeneration**, not a generic Wraith energy-shield reskin, unless Vardath later changes that design.

Final themed hull topology/corners/diagonals/transitions and professional art/audio remain plan requirements even when native mechanics already work.

# Native backstories

Use RimWorld 1.6 `BackstoryDef` for native WNG biographies.

Backstory pools can align with caste/role but cannot substitute for identity/caste.

Wraith origin concepts include:
- Hive creche broodling;
- Living-ship broodling;
- Feeding-court ward.

Count/content remains editable.

# Discovery / progression

Wraith participates in the broader progression theme:

**mystery -> encounter -> evidence -> understanding -> reconstruction -> mastery**

Requirements:
- major content must be reachable in short campaigns;
- historical day-20-to-day-84 fixed schedules are rejected;
- pacing remains tunable/centralized;
- eligibility should not dump every event at once;
- encounters/salvage/analysis should introduce advanced technology before full reconstruction where appropriate;
- Mature-Hive/Hive-Heart evidence can logically support understanding Wraith living technology;
- broader ruins/lab/cloning/story progression remains governed by the master plan.

# Planned-only future biological branches

Anomaly/Ideology/Iratus/hybrid/diplomacy/pharmacology/Kassa/Royalty branches are recorded in their master-plan append files.

They are **planned-only until Vardath explicitly advances them**. Their presence in the broader Wraith design must not cause premature implementation.

# Audio / presentation

Professional-level presentation remains required where it meaningfully improves:
- feeding;
- living structures;
- weapons;
- craft/culling;
- Hive ambience;
- gravship/living-tech operation;
- major events.

Do not generate replacement art unless Vardath explicitly asks.

# Validation / continuity

Compile/XML/API checks establish source sanity only. Real `Player.log`, RimDoctor, screenshots, save/load and observed RimWorld behavior outrank static assumptions.

Do not create checkpoint files or pass logs for this map. When continuing, read the master plan/corrections and inspect current public source to determine which design requirements remain unfinished.
