# WNG — Wraith subsystem feature map

Author/final design authority: **Vardath**.

This map is the pre-implementation reconciliation for the fresh RimWorld 1.6 rebuild after the block Replicator foundation was accounted for. It is not immutable canon. Newer explicit Vardath instructions override it.

## Current implementation state

Fresh public implementation repository: `Vardath/Wraith-Nanite-Gravtech-1.6`.

Verified public `main` before beginning this Wraith reconciliation: `94705ee8894b6659920178e19ea0ebe21555c7be`.

The current clean-reset tree contains the block Replicator foundation only. **No old Wraith implementation is currently present.** This is intentional.

Historical public Wraith source/Defs/assets may be inspected only as reference evidence. There are no known-good historical builds and old code must not be restored wholesale.

## Identity model

Required relationship:

**Wraith identity/xenotype -> caste/PawnKind -> faction role/behavior -> optional biography/backstory**

Wraith are one Wraith identity/xenotype, not separate races per caste.

Current caste/PawnKind roles include at minimum:
- Hunter
- Warrior
- Commander
- Keeper
- Queen

Player-aligned variants may exist where useful, but must remain the same Wraith identity rather than duplicate races.

Backstories are biography/history only. They must not be used to define race, xenotype or caste.

Status: **not implemented in fresh reset**.

## Wraith appearance

Current first-build presentation requirements:
- strongly enforce pale/white/colorless Wraith hair rather than normal random human colors;
- long straight Wraith-appropriate hair preferred where feasible;
- caste distinction should come from role/apparel/behavior rather than inventing separate races;
- future visual tuning remains author-editable.

Status: **not implemented in fresh reset**.

## Life Force — core biological resource

Life Force is the central Wraith feeding/regeneration resource.

Required relationships:
- feeding raises Life Force;
- regeneration consumes/is throttled by Life Force;
- severe depletion can produce torpor/incapacitation behavior;
- high reserve can support expensive healing/missing-part recovery;
- hibernation greatly reduces Life Force use;
- save state must preserve meaningful Life Force values.

Exact capacities/drain/healing costs remain tunable and should be centralized/Def-driven where practical.

Status: **not implemented in fresh reset**.

## Drain Life / Wither — ordinary pawn ability

Current first-build full-feed behavior:
- one coherent Drain Life/Wither ability rather than duplicate competing abilities;
- touch-range valid biological target;
- victim biological age increases substantially (current target +50 years);
- feeding Wraith biological age decreases (current target -5 years) but not below adulthood/current target age 18;
- victim receives a temporary `Life Drained` state, roughly 1–2 days in current design;
- Wraith receives a temporary `Fed Recently` state, roughly about a day in current design;
- repeated full feeding before recovery may become lethal;
- partial feeding may remain a distinct smaller action;
- feeding modifies Life Force appropriately;
- duplicated/overwritten genes must not permanently lose their granted ability gizmos.

**Critical separation:** normal Drain Life/feeding does **not** open the strategic faction feeding-request popup.

Status: **not implemented in fresh reset**.

## Regeneration / biological recovery

Required behavior:
- Wraith heal more aggressively than ordinary humans where Life Force allows;
- low Life Force throttles regeneration;
- depleted Wraith may enter torpor rather than freely regenerating;
- high reserve may regenerate severe injury/missing parts at appropriately high cost;
- EMP/bioelectric interactions must be reconciled where relevant;
- exact rates/costs remain tunable.

Status: **not implemented in fresh reset**.

## Strategic Wraith faction hunger — separate from ordinary feeding

This is a faction-level system, not a pawn ability.

Required behavior:
- each relevant Wraith faction/lineage has strategic hunger/feeding pressure;
- genuine strategic hunger determines when that faction needs subjects/access;
- **only genuine strategic faction hunger may create the feeding-request popup**;
- regular Wraith Drain Life does not create that popup;
- mature-Hive local feeding stock does not create that popup;
- refusal/non-acceptance/unresolved hunger increases that faction's raid/attack pressure;
- hunger should affect request and attack likelihood rather than being mislabeled as a generic quest requirement;
- state should remain faction-specific rather than global if multiple lineages exist.

Current request UI intent retained from prior design:
- first stage identifies relevant feeding-stock/prisoner subject(s);
- player does not choose individual Wraiths in the first modal;
- next stage shows count/names of involved Wraiths;
- decision flow remains paused until the decision sequence completes.

Status: **not implemented in fresh reset**.

## Mature-Hive feeding ecology — separate system

Mature-Hive feeding stock is local site/Hive ecology.

Required behavior:
- finite biological captives/feeding stock;
- Feeding Niches hold exact captive pawns where used;
- feeding stock belongs to the local Hive ecology;
- local depletion/replacement rules are bounded;
- local feeding stock does not trigger strategic hunger request UI.

Status: **not implemented in fresh reset**.

## Mature-Hive retaliation — separate system

Neutralizing a hostile mature Hive can produce delayed retaliation tied to the relevant lineage/site.

This retaliation is separate from:
- normal Wraith feeding;
- strategic faction hunger/request UI;
- local feeding-stock ecology.

Timing remains tunable and must not be buried as an old fixed schedule.

Status: **not implemented in fresh reset**.

## Wraith factions / politics

Current lineage concepts:
- **Sable Brood** — uncompromising hostile predatory Hive;
- **Cinder Court** — militant Queen-led Hive, aggressive but politically mutable;
- **Veiled Hive** — cautious/selective/concealment-oriented and capable of negotiation;
- **Pale Covenant** — exile/offshoot capable of coexistence/trade when supplied appropriately.

Required faction behavior:
- raid independently of Stargates/ONAC/RimGate;
- caste-appropriate raid composition;
- lineage-specific diplomacy/hostility;
- exact faction identity preserved through captivity/rescue/retaliation where story depends on it;
- strategic hunger belongs to the actual faction/lineage;
- later optional Stargate corridors enhance travel/events but are not required for ordinary Wraith raids.

Status: **not implemented in fresh reset**.

## Wraith captivity / exact-pawn continuity

Required behavior supports real pawn identity through:
- abduction;
- captivity;
- feeding stock;
- prisoner feeding;
- rescue/recovery;
- thrall/experiment/hybrid branches where retained by the final plan.

Do not replace an abducted real pawn with a fake proxy victim when later rescue/story continuity depends on the exact pawn.

Save/load must preserve exact pawn and faction ownership where required.

Status: **not implemented in fresh reset**.

## Mature Hive population / castes / infrastructure

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
- failed generation cleans up partial state rather than leaking pawns/things/world state.

Historical public reference families included `WraithMatureHivePopulation`, `WraithHibernation`, `WraithHibernationPod`, `WraithDormancyVault`, `WraithFeedingNiche`, `WraithHiveHeart` and mature-Hive site/incident workers. These names are reference evidence only, not code authority.

Status: **not implemented in fresh reset**.

## Wraith growth / biological production

Historical design included Wraith Growth Chamber behavior.

Required relationship:
- support bounded Wraith biological growth/replacement where retained;
- caste outcomes and resource requirements must be coherent with Wraith biology/faction ecology;
- no uncontrolled infinite spawning;
- exact timers/costs remain tunable.

Status: **not implemented in fresh reset**.

## Wraith living technology

Wraith technology should feel grown/organic/biomechanical rather than generic industrial crafting.

Required current concepts:
- biological interaction/implantation starts the progression;
- Living Forge/workshop can be grown from a living host **or a corpse** where this route remains in the first build;
- Wraith Grav Engine progression can likewise use living-host/corpse interaction where appropriate;
- incubation timings are tunable;
- grown structures/weapons must have actual gameplay functions;
- **use Wraith Grav Engine, never obsolete Gravcore substitution**.

Historical public reference families included `WraithLivingForge`, `WraithGrowthChamber`, `WraithBioelectricOrgan` and related research/recipes. Reference only.

Status: **not implemented in fresh reset**.

## Bioelectric organ / Wraith biological interaction

Historical design included a Wraith bioelectric-organ branch and implantation/testing paths.

Required reconciliation before implementation:
- determine exact role in Life Force, living-tech bootstrap and Grav Engine progression from current plan/history;
- support corpse interaction where Vardath explicitly required it for Living Forge/Grav Engine testing/progression;
- avoid recreating obsolete Gravcore semantics.

Status: **explicitly unfinished pending detailed living-tech slice reconciliation**.

## Wraith weapons

Wraith living weapons remain planned.

Required behavior:
- real functional weapon effects;
- caste/faction-appropriate usage;
- organic/biomechanical identity;
- professional audio where appropriate later;
- avoid orphan weapon Defs with no acquisition/use path.

Status: **not implemented in fresh reset**.

## Wraith Dart / culling / abduction

Wraith Dart remains a core Wraith craft/event family.

Current first-build hostile-culling intent:
- two real flyover/culling passes in the current design;
- passes perform actual ray-of-absorption/culling/abduction, not decorative flyovers;
- abductee identities persist into captivity/rescue systems;
- craft transitions to intended final state after the passes;
- pass count remains editable by Vardath.

Wraith raids do not depend on Stargates or Dart events.

Status: **later Wraith craft/event dependency; not implemented in fresh reset**.

## Stargate interaction — optional later dependency

CatCraft Stargates! is optional.

Ownership boundary:
- CatCraft owns gate network/address/dial/iris/shield/receive-buffer mechanics;
- WNG owns Wraith incidents/corridors/craft/objectives/outcomes;
- no replacement Stargate network;
- no hard dependency;
- do not steal CatCraft receive-buffer ownership;
- avoid Harmony takeover where native/API integration works.

Status: **later integration dependency**.

## Wraith gravship family — later dependency

A distinct Odyssey-compatible Wraith gravship family remains planned, separate from Asuran/Precursor gravships.

Must ultimately include real:
- hull/substructure;
- walls/corners/diagonals/transitions where needed;
- functional Wraith Grav Engine;
- pilot console/node;
- fuel storage/feed;
- thrusters/field systems;
- boarding/world/save-load behavior as appropriate.

Do not cross-connect Wraith resources with Asuran/Precursor resources by accident.

Status: **later craft/gravship subsystem dependency**.

## Backstories — biography only

Native RimWorld 1.6 `BackstoryDef` should be used when WNG biographies are rebuilt.

Historical first-build target was 30 WNG backstories across Wraith/synthetic origins and adult histories. Count/content remains editable.

Wraith origin concepts included:
- Hive creche broodling;
- Living-ship broodling;
- Feeding-court ward.

Backstory pools may align with caste/role but cannot substitute for identity/caste.

Status: **not implemented in fresh reset**.

## Discovery / progression

Wraith content participates in the broader progression theme:

**mystery -> encounter -> evidence -> understanding -> reconstruction -> mastery**

Historical day-20-to-day-84 schedules are rejected as fixed gating.

Requirements:
- major WNG/Wraith content must be reachable in short campaigns;
- pacing remains tunable/centralized;
- eligibility should not dump every event at once;
- encounters/salvage/analysis should introduce advanced tech before full reconstruction.

Useful historical site concepts include ruined Wraith laboratories, cloning installations and mature Hive sites.

Status: **later story/progression layer dependency**.

## Audio / presentation

Professional-level audio remains expected where it meaningfully improves Wraith weapons, craft, feeding, living structures and major incidents.

No replacement/generated art is to be created unless Vardath explicitly requests image/art generation.

Status: **later presentation pass, but audio hooks/Defs should not be designed out of current systems**.

## Immediate Wraith implementation order from this reconciliation

1. Rebuild one Wraith identity/race/xenotype foundation and caste PawnKinds without race-per-caste mistakes.
2. Rebuild Life Force and ordinary Drain Life/Wither as a coherent pawn-level system, including age changes, temporary states and regeneration/torpor interactions.
3. Rebuild the four Wraith factions/lineages and caste-appropriate raid composition.
4. Rebuild strategic faction hunger and feeding-request pressure **separately** from ordinary feeding.
5. Rebuild exact-pawn captivity/rescue/feeding-stock foundations.
6. Rebuild Mature-Hive ecology, population, hibernation, Feeding Niches, Dormancy Vault, Hive Heart and retaliation as separate local systems.
7. Rebuild Living Forge / biological-tech bootstrap / Wraith Grav Engine progression, including corpse pathways where required.
8. Rebuild remaining living weapons/growth/backstory/research/progression hooks.
9. Reconcile the Wraith foundation again before moving to human-form Replicators/Asurans/Queen or craft/integration layers.

Every item must end its pass as **implemented**, **explicitly unfinished with dependency recorded**, or **explicitly changed/rejected by Vardath**. There is no forgotten state.
