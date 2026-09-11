# WNG — CANONICAL RECOVERY LEDGER

Author/final design authority: **Vardath**  
Ledger established: **2026-09-11**

# PURPOSE — THIS IS THE ONE-TIME HISTORY RECONSTRUCTION

This ledger is the durable result of the one-time broad reconstruction of WNG conversation history, continuity documents, current public source/Defs, and fresh-rebuild commit history.

Vardath's explicit intent is:

> Do the exhaustive history recovery once, preserve the decisions correctly here, then make every later handoff/recovery smooth without forcing Vardath to repeat every decision ever made.

Future GPT instances **do not re-read weeks of raw chat by default**. They must instead:

1. read `STANDING_RULES.md`;
2. read this `CANONICAL_RECOVERY_LEDGER.md` completely;
3. read `WNG_IMPLEMENTATION_CHECKLIST.md`;
4. fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main` and compare it with the implementation snapshot below;
5. read only the active subsystem documents/contracts needed for the next work;
6. retrieve older raw WNG chat history **only when** this ledger identifies an unresolved historical conflict/gap, current evidence conflicts with the ledger, or Vardath explicitly asks for raw-history review.

After every meaningful implementation batch, **update this ledger** with the new public HEAD, completed state, newly unfinished dependencies, and any new Vardath correction/supersession. The ledger must move with the mod so the next handoff starts from state, not archaeology.

This ledger is not immutable doctrine. Vardath may change anything. Newer explicit Vardath instructions always override this file and must then be written back into it.

---

# 1. CURRENT AUTHORITY AND REPOSITORIES

## Author/design authority

**Vardath is the author and final design authority.** Assistant implementation choices are proposals/technical decisions, not permanent lore or design doctrine.

## Active implementation repository

`Vardath/Wraith-Nanite-Gravtech-1.6`

Current verified public `main` at ledger creation:

**`4af4f60c184f1971ee7bc7516b63e3b33142fea0` — `cleanup: remove temporary Wraith stunner validation workflow`**

Fresh-rebuild base:

**`0386f33665b08f9c4f82cbcec23d844bc68ea3af` — `reset: restart WNG from Replicator foundation only`**

Current `main` is 269 commits ahead of that fresh-reset base at ledger creation.

## Durable continuity repository

`Vardath/Vardath.github.io/wng-rebuild/`

## Private historical repository

Older WNG work used private `Vardath/Wraith-Nanite-Gravtech` as working authority. **That instruction is superseded for current work.** The private repository and old branches/builds may be historical/reference evidence only unless Vardath explicitly re-authorizes them.

Do not consume private-repo credits or make the private repository a dependency of current recovery.

---

# 2. CORE PROCESS CONTRACT

Every implementation pass must answer these questions before code:

1. **What is this in Stargate?**
2. **What does it actually do in Stargate?**
3. **What has Vardath decided about it?** Use this ledger first; use raw history only for a flagged conflict/gap.
4. **What does current public WNG already implement?** Inspect actual current `main`; old next-step prose is never proof of absence.
5. **What did historical WNG attempt, and what should/should not be learned from it?** Reference evidence only.
6. **What does vanilla RimWorld 1.6 / Odyssey / Biotech already provide?** Reuse native mechanics wherever they correctly express the intended behavior.
7. **What do optional Stargate mods own?** Do not duplicate or hijack externally owned systems.
8. **What is the best faithful implementation?** Preserve Stargate identity rather than creating generic sci-fi substitutes.

Mandatory working order:

**CANONICAL LEDGER -> STARGATE LORE -> CURRENT PUBLIC STATE -> ACTIVE CONTRACTS -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> UPDATE LEDGER/HANDOFF**

Every known feature ends a pass as:
- **implemented**;
- **unfinished — dependency recorded**; or
- **changed/rejected by Vardath**.

There is no forgotten/silently removed state.

`rebuild`, `correct`, `refine`, `reconcile`, `unfinished`, or `next` **never means remove a required feature** unless Vardath explicitly removes it.

---

# 3. GLOBAL DESIGN PRINCIPLES RECOVERED FROM HISTORY

- WNG is a **Stargate mod**, not generic alien-tech content. Stargate lore/function is a mandatory design input on every pass.
- Preserve feature identity and gameplay purpose; do not implement a name-only approximation.
- Prefer native RimWorld/Odyssey/Biotech mechanics where they already solve boarding, transport, world travel, gravships, power, genes, factions, save/load, etc.; add WNG logic for Stargate-specific behavior that native systems do not provide.
- No known-good historical WNG build exists. Old builds/branches can prove that a feature existed or show intended behavior/art, but they are not implementation authority and must not be copied wholesale.
- Live RimWorld behavior, screenshots, `Player.log`, and RimDoctor evidence outrank a green static audit when judging actual playability.
- Static compile/XML/reference validation is useful for implementation sanity but is not design authority and does not prove live behavior.
- Do not build design-locking anti-regression/release bureaucracy. Use minimal checks needed for function.
- Nothing is set in stone. Timers, balance, art, sounds, races/xenotypes, castes, quests, systems and whole implementations can be revised by Vardath.
- Do not bury author-tunable design/balance choices as scattered magic numbers. Prefer Defs/settings/centralized configuration where practical.
- Do not generate replacement art unless Vardath explicitly asks for image/art generation or a specific art task requires it.
- Professional final presentation remains required: coherent faction-specific art, correct directional/rotational/connection states, and professional audio where appropriate.

---

# 4. IMPORTANT SUPERSEDED / CONFLICTING HISTORY

This section exists so older recovered memories cannot be mistaken for current instructions.

## Repository authority

**OLD:** private WNG repo was authoritative and public 1.6 was not to be touched.  
**CURRENT:** public `Vardath/Wraith-Nanite-Gravtech-1.6` `main` is the active implementation repository. Private/old builds are reference evidence only.

## “Known-good” checkpoints

**OLD:** several branches/commits were at times called stable/known-good.  
**CURRENT:** Vardath explicitly corrected this: **there are no known-good historical states.** Older checkpoints can be mined for requirement evidence only.

## Fixed discovery schedule

**OLD:** historical progression used day 20/28/36/44/52/60/72/84 and Queen vault at day 84.  
**CURRENT:** fixed day-84-style pacing is rejected. Major WNG content must be reachable in shorter campaigns. Eligibility/timing must be tunable and must not dump every event at once.

## Wraith Gravcore

**OLD:** Gravcore names/implementations existed historically.  
**CURRENT:** use the intended **Wraith Grav Engine**. Do not restore obsolete Wraith Gravcore as the ship engine.

## Wraith stun weapon

**OLD:** historical versions/notes described shorter-range/melee-ish/paralysis variants with differing numbers.  
**CURRENT:** newest contract/current public implementation is a **ranged nonlethal Wraith stun staff** using native `StunHandler`, zero ordinary projectile health damage, automatically carried by Hunter/Warrior/Commander/Keeper but not forced on Queen/player-Wraith PawnKinds. Current mechanics-first Def uses 26.9 range and 1,800 stun ticks, but these balance values remain tunable. Final Stargate-authentic art/audio is unfinished.

## Goa'uld integration visibility

**OLD:** Goa'uld WNG construction could disappear when ONAC was absent.  
**CURRENT:** standalone-capable **WNG-owned** Goa'uld technology should fall back to WNG construction when ONAC is absent and route to `ONAC_Architect` when ONAC exists. Transport rings already follow this. Existing Al'kesh/Ha'tak-related gating must **not** be stripped until their standalone resource/research route is genuinely reconciled.

## Goa'uld ship fallback fuel

**REJECTED MISTAKE:** uranium/chemfuel fallback was invented on 2026-09-11 and immediately rejected. The bad commit was removed from `main`.

Do not invent a replacement fuel/resource/research route merely to remove ONAC gating.

## ONAC liquid resource naming

Vardath described Goa'uld ship fuel as liquid naquadah. The supplied ONAC implementation actually exposes **`ONAC_LiquidNaquadria`** labelled liquid Naquadria, produced from `ONAC_Naquadah`. When ONAC is installed, WNG uses the real external resource rather than duplicating/renaming it. A distinct WNG liquid-naquadah resource would require a new explicit design decision.

## Old gravship mirror/ParentName architecture

Historical attempts used invalid concrete Odyssey Defs such as `GravEngine`, `ChemfuelTank`, `LargeThruster`, etc. as XML parents and produced runtime failures. Current fresh architecture deliberately uses Odyssey's exact native systems/Defs where hard-coded and themes/bridges them instead of cloning invalid parents.

---

# 5. REPLICATOR DESIGN CONTRACT

## Identity split

Block Replicators are mechanical custom forms. Human-form Replicators/Asurans are nanite humanoids and are a separate identity layer.

## Physical hierarchy

Upward recombination:

**Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass**

Genuine destruction breakup:

**Siege Mass -> Titan -> Bulwark -> Hunter -> Drone/base**

Base Drone is irreducible.

Intentional upward recombination must not accidentally trigger death-splitting. Genuine split must be at-most-once/save-safe. Matter/state should survive transitions where appropriate rather than disappearing.

Current first-build split-born recombination lockout: approximately **one in-game hour / 2,500 ticks**, tunable. The purpose is to prevent a destroyed large form instantly recreating itself.

## Specialist/adaptation branches that must not disappear

- Controller
- Repairer
- Burrower
- Artillery/Siege support
- Ranged adaptation
- Armor adaptation
- Power adaptation
- Grav adaptation
- Shield adaptation / Shield Replicators
- learned anti-shield/countermeasure development

Adaptations are learned from encountered/assimilated technology and recurring swarms may retain learned state. EMP remains a meaningful countermeasure.

## Matter/economy/control

- dangerous Replicator Matter
- assimilation
- matter-budget offspring production
- population ceiling
- regeneration with EMP suppression
- containment/countermeasure structures
- state inheritance across split/recombine where appropriate
- player-owned Replicators must not autonomously consume the colony
- Child's Toy is a distinct player-owned mech branch; if it goes feral it becomes an ordinary hostile Replicator Drone

## CURRENT PUBLIC IMPLEMENTATION STATUS

At `4af4f60...`, the fresh public tree contains the block hierarchy, specialist behaviors, cumulative adaptation state/effects, matter systems, containment, retaliation/cell consumption, regeneration, Child's Toy, Replicator faction roster and related research/Defs.

Tracked dependencies still requiring later concrete systems or integration include richer sovereign/player control, Queen/Asuran sovereign consequences, mixed human-form+block raids, and any adaptation effect that depends on later systems not yet present.

---

# 6. HUMAN-FORM REPLICATORS / ASURANS / QUEEN CONTRACT

Human-form Replicators/Asurans are nanite humanoids, not block custom races.

Recovered intended systems include:
- human-looking infiltration until scanning/injury/suspicious behavior reveals them;
- role/PawnKind concepts such as engineer, infiltrator, soldier, coordinator/commander and player variants;
- Neural Interface operations including recruit, imprison, enslave, copy and create human-form;
- copied pawns should preserve relevant exact identity/biography/title/surname, skills, passions/XP, appearance/genome and continuity through save/load where the copy mechanic requires it;
- reconstruction/collective backup has real costs/limits, not free infinite duplication;
- Nanite Reserve supports healing/fabrication/reconstruction economy.

## Replicator Queen

Current first-build requirement:
- one exact **female human-form Replicator Queen**;
- current age target **13**;
- found in a real cryosleep/cryptosleep chamber;
- becomes player-recruited **immediately on release/spawn**;
- Asuran/Lattice recovery operatives attempt physical capture during the vault encounter;
- later capture raids may target **any player map where the exact Queen is physically present**;
- never target a different player map when she is absent/travelling/off-map;
- capture commits only when a hostile carrier physically exits the map with the exact Queen;
- before exit she remains recoverable/player-owned;
- successful capture gives the Lattice **real sovereign access to block Replicators** in appropriate future threats, not an arbitrary `+1 outbreak` modifier.

## CURRENT PUBLIC IMPLEMENTATION STATUS

At ledger creation, current `main` contains Asuran **fabrication/workshop/Nanite Reserve** and Asuran **gravship** foundations, but code search does **not** show the planned human-form Replicator/Queen/Neural Interface/infiltration/sovereign layer. Treat that layer as **required and not yet implemented in the fresh public rebuild**, unless current `main` later proves otherwise.

---

# 7. WRAITH IDENTITY, BIOLOGY AND FACTIONS

## Identity layers

Wraith are one Wraith identity/xenotype. Castes are PawnKind/role distinctions, not separate races.

Current caste roles:
- Hunter
- Warrior
- Commander
- Keeper
- Queen

Backstories/biographies are not races or castes.

## Appearance

- hair strongly pale/white/colorless; avoid ordinary random human hair colours;
- long straight Wraith-appropriate hair preferred where feasible;
- caste presentation should come from role/apparel/behavior rather than race duplication.

## Life Force and ordinary Drain Life/Wither

Drain Life/Wither is one coherent ordinary Wraith feeding ability/system.

Current first-build full-feed target:
- victim biological age **+50 years**;
- feeding Wraith biological age **-5 years**;
- never de-age Wraith below current adulthood target **18**;
- victim gets temporary **Life Drained** roughly 1–2 days;
- Wraith gets temporary **Fed Recently** roughly one day;
- Life Force is a real resource linked to feeding/regeneration/torpor;
- overwritten/deduplicated genes must not permanently lose granted ability gizmos.

Exact balance remains tunable.

**Ordinary Drain Life never opens the strategic faction feeding-request popup.**

## Strategic faction hunger — distinct system

Strategic hunger is faction-level pressure. Only a Wraith faction that is genuinely hungry enough may generate the feeding request UI. Refusal/non-acceptance/unresolved hunger increases attack/raid pressure. It affects request/raid likelihood and is not automatically a generic quest.

The current public Wraith factions are:
- **The Sable Brood** — uncompromising hostile predatory lineage;
- **The Cinder Court** — militant Queen-led Hive, politically mutable;
- **The Veiled Hive** — selective/concealment-oriented, negotiable;
- **The Pale Covenant** — exile/offshoot capable of coexistence/trade when supplied.

Their hunger state is faction-specific.

## Mature Hive feeding ecology — distinct system

Mature-Hive local feeding stock/captives, Feeding Niches, hibernation/dormancy population, Hive Heart, bounded replacement/growth and local site ecology are separate from strategic faction hunger.

Mature-Hive feeding does **not** create the strategic feeding-request popup.

## Mature Hive retaliation — third separate system

Neutralizing a mature Hive can create delayed lineage/site retaliation. This is separate from ordinary feeding and separate from strategic hunger/request UI.

## Exact captivity/rescue

Abduction/culling/captivity/rescue must preserve the **exact pawn identity** wherever later rescue/story continuity depends on it. Do not recreate proxy victims.

## CURRENT PUBLIC IMPLEMENTATION STATUS

At `4af4f60...`, current public `main` contains:
- Wraith xenotype/caste PawnKinds;
- four Wraith factions above;
- Wraith Life Force/core/feeding code and Hediffs;
- strategic faction hunger code;
- Mature Hive incident/site/population/neutralization/retaliation code;
- Feeding Niche, Hibernation Pod, Dormancy Vault and Hive Heart Defs;
- captivity and rescue-site code;
- raid kidnap bridge;
- Wraith maintenance/core systems.

These are current implemented source/Defs, **not a claim of full live-game validation**.

---

# 8. WRAITH LIVING TECHNOLOGY / BOOTSTRAP

Wraith technology should feel grown/organic/biomechanical rather than generic industrial crafting.

Current requirements:
- Living Forge/workshop progression can originate from biological implantation;
- living host **or corpse** pathways are required where specified so progression/testing is not dependent on keeping a living host;
- Wraith Grav Engine progression similarly supports the intended biological bootstrap;
- current historical target incubation is approximately one day, but timing remains tunable;
- do not restore obsolete Wraith Gravcore semantics.

## CURRENT PUBLIC IMPLEMENTATION STATUS

Current `main` contains Wraith bootstrap research, implantation job, save-safe workshop/grav-engine growth state, bootstrap implants, Living Forge/deploy-core foundations, recipes/settings gates and production contract/checkpoint files.

The Wraith engine seed deliberately produces/themes Odyssey's **real native GravEngine** rather than creating an incompatible parallel engine Def.

---

# 9. SHUTTLES / CRAFT

All primary WNG craft should be real usable native-style vehicles rather than raid-only decorative objects.

Native Odyssey loading/boarding/transport/launch/world behavior is authoritative wherever possible.

Current craft families:
- `WNG_WraithDart`
- `WNG_WraithStrikeCraft` / Wraith scout craft
- `WNG_WraithCruiser`
- `WNG_PuddleJumper`
- `WNG_AlkeshTransport`

## Wraith Dart

Canon/gameplay identity:
- Wraith culling fighter;
- current hostile mission design uses **exactly two real flyover/culling passes**;
- those passes perform actual absorption/capture, not decoration;
- exact captives persist through the native shuttle transit/escape boundary;
- hostile pilot and retreat are physically tied to the native shuttle lifecycle.

## Puddle Jumper

Ancient/Lantean gate-capable shuttle. Ancient drones and optional Stargate mission behavior are WNG additions on top of native shuttle handling.

Do not casually invent its final energy/fuel abstraction; current chemfuel in the Def is explicitly a temporary native-mechanics placeholder pending deliberate Ancient power/fuel design.

## Al'kesh

**Required retained feature. Do not remove it.**

It began as a provisional shuttle foundation and was later upgraded into the full native Odyssey player-shuttle stack.

Current public Al'kesh:
- real `Building_PassengerShuttle`;
- native shuttle/launchable/transporter/refuelable stack;
- native TransportShipDef/world object/incoming/leaving skyfallers;
- ONAC-gated at current head;
- current construction uses verified ONAC Naquadah;
- current fuel uses verified `ONAC_LiquidNaquadria`;
- current research is `WNG_GoauldShuttles` gated through ONAC/`ONAC_NaquadahLiquefaction`.

`rebuild/refine Al'kesh` means fix/refine its implementation while retaining the feature, **not delete it**.

## CURRENT PUBLIC IMPLEMENTATION STATUS

All five craft above have the complete native shuttle stack at current `main`. Static compile/XML validation has been performed during implementation; live-game behavior still needs real in-game verification where not already demonstrated.

---

# 10. STARGATE / OPTIONAL INTEGRATION OWNERSHIP

## CatCraft Stargates!

Verified package: **`ccyt.stargatesmod`**.

CatCraft owns:
- gate network/address data;
- dialing/connection direction;
- iris/shield state;
- receive-buffer/rematerialization rules;
- gate usability/traversal state.

WNG owns only its added incidents/craft/objectives/outcomes around the gate.

Important gate semantics to preserve include one-way solid-matter travel, iris/shield destruction of inbound matter before rematerialization, and not treating an inbound active connection as an outbound retreat route.

WNG has no hard dependency on CatCraft.

## ONAC / RimGate Biotech

Verified ONAC package: **`idolord.ONAC`**.  
Verified RimGate Biotech package: **`CraveMode.RimGateJaffaKreeBiotech`**.

Do not bind the older HAR RimGate variants by fuzzy name matching.

Verified RimGate factions:
- `JKB_JaffaApophis`
- `JKB_JaffaAnubis`
- `JKB_JaffaRa`

Verified xenotypes:
- `JKB_Jaffa`
- `JKB_JaffaFirstPrime`

ONAC/RimGate own Goa'uld/Tok'ra/Jaffa faction/biology systems. WNG may add interoperability/craft, not duplicate those systems.

Verified ONAC construction/economy surface:
- `ONAC_Architect`
- `ONAC_Naquadah`
- `ONAC_LiquidNaquadria`
- `ONAC_MakeLiquidNaquadria`
- `ONAC_NaquadahLiquefaction`
- `ONAC_GoauldFoundryResearch`
- `ONAC_GoauldResearchBench`
- `ONAC_NaquadahLiquefier`

Use exact IDs from supplied source, never guessed external Def names.

---

# 11. GOA'ULD TRANSPORT RINGS

Transport rings are required WNG-owned Goa'uld technology.

Current design:
- `WNG_GoauldTransportRings` buildable endpoint;
- native `CompTransporter` loading/ThingOwner semantics;
- exact people, animals, mechs and items;
- no Stargate dialing/address sequence;
- same-map transport, including sealed/internal rooms;
- cross-currently-loaded-map transport;
- destination list when more than two compatible powered rings exist;
- exact Thing/pawn identity survives save/load/transport;
- failed placement never deletes exact cargo;
- tunable cooldown;
- unloaded world-site transfer remains a later exact-world-object problem and must never be faked through pawn recreation.

Architect routing:
- ONAC present + exact `ONAC_Architect` -> route there;
- ONAC absent -> standalone-capable WNG ring tech appears under WNG.

## CURRENT PUBLIC IMPLEMENTATION STATUS

Current `main` contains generic Goa'uld Architect routing, ring research/building, native-loaded ring network, same/cross-loaded-map destination handling, power guard and cooldown persistence.

Final authentic rising-ring visuals/audio remain a later presentation pass.

---

# 12. WRAITH STUN STAFF

Newest/current contract:
- ranged nonlethal capture weapon;
- zero ordinary projectile health damage on successful shot;
- native `StunHandler` / native stun resistance remains authoritative;
- Hunter, Warrior, Commander and Keeper automatic carrier castes;
- Queen/player-Wraith PawnKinds not forcibly assigned it;
- distinct from Goa'uld staff weapon, zat, Dart culling beam and Drain Life;
- dedicated Stargate-authentic final art/audio later.

## CURRENT PUBLIC IMPLEMENTATION STATUS

`WNG_WraithStunStaff` and custom non-damaging stun projectile are implemented in current `main`; current mechanics-first values include 26.9 range and 1,800 stun ticks, both tunable.

---

# 13. ODYSSEY GRAVSHIP ARCHITECTURE

Authority order for WNG gravships:
1. Vardath current requirements/current contracts;
2. Stargate canon/lore;
3. actual RimWorld 1.6 Odyssey gravship Defs/classes/connections/construction/launch/rendering;
4. fresh WNG implementation.

Historical WNG gravship code is failure/reference evidence only.

Native behaviors to preserve:
- real Odyssey `GravEngine`;
- connected gravship substructure/map-moving system;
- native hull/cut-corner grammar;
- native pilot console semantics;
- native directional thrusters;
- native power net where applicable;
- native fuel accounting/consumption wherever the themed tank can participate;
- family isolation so Wraith/Asuran/Goa'uld/vanilla hardware cannot accidentally satisfy another family's engine.

WNG adds themed physical fuel-pipe connectivity as a deliberate extension while leaving native tanks/engine fuel accounting authoritative.

## Wraith gravship family — current

Current public implementation includes:
- native engine seed -> exact Odyssey GravEngine themed Wraith;
- living substructure;
- hull seed -> exact native GravshipHull with Wraith theme;
- control/pilot interface;
- small/large bio-sludge tanks;
- small/large thrusters;
- field extender;
- signal jammer;
- fuel optimizer and living-hull regeneration identity where implemented;
- research gate;
- native power conduits;
- visible/hidden Wraith fuel pipes;
- same-family pipe-feed enforcement.

Wraith fuel/resource current fresh-rebuild identity: **Wraith bio sludge** (`WNG_WraithBioSludge`).

## Asuran gravship family — current

Current public implementation includes:
- Asuran engine seed -> exact Odyssey GravEngine themed Asuran;
- Asuran native substructure;
- hull seed -> exact native GravshipHull with Asuran theme;
- control interface;
- small/large nanite-sludge tanks;
- small/large thrusters;
- field extender;
- signal jammer;
- fuel optimizer;
- shield emitter using native gravship shield semantics;
- Asuran power cell using native gravcore-power-cell behavior (this is a power-cell role, not restoration of obsolete Wraith Gravcore);
- vacuum/orbital support slice;
- research progression;
- native power conduits;
- visible/hidden Asuran fuel pipes;
- same-family pipe-feed enforcement.

Asuran current resource identity: **nanite sludge** (`WNG_NaniteSludge`).

## Presentation/live status

Current exposed fuel-pipe graphics reuse native conduit art as mechanics placeholders; final faction-specific professional art/connection states remain unfinished. Do not call the visual pass complete.

No current static checkpoint should be described as full live-game validation without actual in-game evidence.

---

# 14. GOA'ULD / HA'TAK GRAVSHIP FAMILY

Required Stargate identity:
- Ha'tak is a **Goa'uld mothership/capital warship**, not a shuttle;
- RimWorld representation is an Odyssey gravship family scaled to RimWorld gameplay, not a literal television-scale ship;
- identity includes central pyramid/superstructure feel, command/pel'tac role, shields, heavy energy weapons, Jaffa complement/transport capability, and transport rings;
- actual Ha'taks carry Death Gliders and use transport rings internally; rings are expected internal Ha'tak equipment where practical.

Required implementation direction:
- Odyssey-native gravship family;
- Goa'uld-themed engine/drive presentation;
- Goa'uld hull/substructure architecture using native placement/join/corner grammar;
- command/pilot console;
- propulsion/thrusters;
- shield/heavy systems consistent with Goa'uld identity;
- liquid-Naquadria storage/feed when ONAC integration is active;
- visible/hidden fuel routing when the family is built;
- ONAC Architect integration when ONAC is active;
- standalone WNG fallback only after the standalone resource/research path is genuinely reconciled;
- do not invent uranium/chemfuel or other arbitrary fallback.

## CURRENT PUBLIC IMPLEMENTATION STATUS

The shared C# gravship theme/network infrastructure already recognizes `Goauld`, but current-tree search at ledger creation finds **no completed Ha'tak/Goa'uld gravship Def family**. Treat Ha'tak as **required and not yet implemented** in the fresh public rebuild.

The Al'kesh is already implemented separately and must remain.

---

# 15. PROFESSIONAL ART / AUDIO CONTRACT

Final WNG should look and sound like a professional RimWorld/Stargate mod, not placeholder content.

Recovered presentation requirements include:
- purpose-specific graphics for visible items, pawns, buildings, apparel, weapons, genes, abilities, craft and gravship structures;
- Wraith organic/biomechanical visual identity;
- Asuran/Precursor precise/geometric identity;
- Replicators articulated/mechanical identity;
- correct directional/rotational/facing art where RimWorld expects it;
- gravship wall/hull/corner/diagonal-transition art that preserves native Odyssey connection/corner semantics;
- visible/hidden pipe/conduit states and appropriate connection/corner graphics;
- dedicated final craft/weapon/structure art rather than vanilla placeholders;
- professional audio for movement, weapons, living technology, culling, drives, nanites, assembly, ambience and major events where appropriate;
- live mix/repetition/loudness/cohesion must be judged in-game.

Historical private builds contained extensive art/audio inventories, but old assets/builds are reference evidence only unless explicitly retained/migrated by current design. Approved block Replicator graphics remain intentionally preserved.

**Do not generate replacement art unless Vardath explicitly asks.**

---

# 16. VALIDATION CONTRACT

Static checks may establish:
- C# compilation;
- XML parsing/reference sanity;
- narrow implementation invariants.

They do **not** by themselves establish:
- correct live RimWorld Def loading in every mod combination;
- correct world generation;
- functional UI/boarding/launch;
- save/load transaction safety;
- correct art rendering;
- correct audio mix;
- actual raid/quest/faction behavior.

When a candidate build is tested, actual `Player.log`, RimDoctor, screenshots and observed gameplay outrank claims based only on CI.

Do not resurrect a large audit/release bureaucracy. Use practical validation proportionate to the current slice.

---

# 17. CURRENT IMPLEMENTATION SNAPSHOT AT `4af4f60...`

## Implemented in fresh public source/Defs

### Block Replicators
Full primary hierarchy, specialist/adaptation foundations, matter/assimilation/regeneration/containment, Child's Toy/player-safety branch and related faction/research behavior are present.

### Wraith
Wraith identity/xenotype/castes, four factions, Life Force/feeding, strategic faction hunger, Mature Hive ecology/retaliation, captivity/rescue, feeding niches/hibernation/dormancy/Hive Heart, living-tech bootstrap, Wraith Dart mission/culling/pilot/native retreat/captive persistence, Wraith gravship family and Wraith stun staff are present in current source/Defs.

### Asuran foundations
Nanite Reserve/fabrication/workshop/nanite sludge and Asuran Odyssey gravship family are present.

### Craft
Wraith Dart, Wraith scout/strike craft, Wraith cruiser transport, Puddle Jumper and Al'kesh have complete native Odyssey shuttle stacks.

### Optional integrations
Exact CatCraft/ONAC/RimGate package/Def identities are recorded in source; optional integration ownership is established; Goa'uld transport rings are implemented.

### Gravship networking
Wraith/Asuran themed native-engine architecture, family isolation, native-net power conduits and family-specific visible/hidden fuel-pipe connectivity are present.

## Required but not currently found/complete

- human-form Replicator/Asuran infiltration/Neural Interface/Queen/sovereign layer;
- Queen vault/capture-raid story layer;
- mixed human-form + block Replicator raid integration tied to that layer;
- Goa'uld/Ha'tak gravship family;
- reconciled standalone resource/research path for WNG-owned Goa'uld shuttle/gravship infrastructure when ONAC is absent;
- final Ancient/Puddle Jumper power/fuel abstraction;
- final professional art/audio pass and full directional/connection asset audit;
- broad live-game validation of the fresh current build.

Other missing items may exist; before implementing a subsystem, inspect current `main` and this ledger together. If a requirement is discovered, add it to the ledger instead of silently omitting it.

---

# 18. CURRENT NEXT-WORK INTERPRETATION

At ledger creation, **do not touch/remove Al'kesh**. It exists and is required.

Before the latest continuity interruption, the plausible next unimplemented major craft/gravship item was the **Ha'tak gravship family**, but that is not an instruction to blindly begin coding it. A future continuation must:

1. fetch current public `main` and confirm HEAD/state;
2. check whether work advanced after `4af4f60...`;
3. read the active Goa'uld/rings/gravship contracts and supplied ONAC verification;
4. run the Stargate-lore/current-state checklist;
5. preserve Al'kesh/rings/current ONAC integration;
6. implement only the genuinely unfinished slice.

The human-form Replicator/Queen layer is also still a major required unfinished branch and must not be forgotten simply because craft work is currently nearby.

---

# 19. HANDOFF MAINTENANCE RULE — HOW FUTURE RECOVERY STAYS SMOOTH

After every meaningful batch, update this file before ending the work session:

- **Current public HEAD:** exact SHA + message.
- **What actually changed:** name the files/features/mechanics, not vague “continued work.”
- **Current status:** implemented / unfinished dependency / changed by Vardath / live-test-needed.
- **New decisions:** record Vardath's newest correction in the relevant design section.
- **Superseded decisions:** move old conflicting wording into the superseded section rather than leaving both active.
- **Next actual slice:** derive it from current `main`, not an older checkpoint.

Do not create a fresh competing handoff summary that drifts from this ledger. `NEXT_GPT_PRIMER.md` should remain a short pointer/current snapshot; **this ledger is the canonical recovered continuity record**.

The objective is simple: the next GPT should be able to recover WNG accurately without making Vardath reconstruct the project again.
