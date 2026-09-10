# WNG Wraith foundation checkpoint — 2026-09-10

Author/final design authority: **Vardath**.

Implementation repository: `Vardath/Wraith-Nanite-Gravtech-1.6`

Implementation cleanup head at this checkpoint: `be3798c810d4dfce1ead66ef44fd667580559714`.

Always fetch current `main` before editing because the repository may have advanced after this checkpoint.

## Implemented fresh — not restored wholesale

The first Wraith implementation slice has been written anew against RimWorld 1.6 after full subsystem reconciliation.

Implemented:
- one `WNG_Wraith` xenotype identity;
- caste PawnKinds under that identity: Hunter, Warrior, Commander, Keeper and Queen;
- player Wraith PawnKind uses the same identity rather than a separate race;
- native Life Force gene-resource implementation;
- tunable Life Force thresholds, daily drain, hibernation drain reduction and regeneration scaling;
- Life Force starvation and torpor states;
- deliberate Wraith hibernation;
- Life Force-backed regeneration that actually spends Life Force rather than healing for free;
- Fed Recently accelerates regeneration;
- ordinary full Drain Life: current first-build values victim +50 biological years, caster -5 biological years, caster floor 18, Life Drained 1–2 days, Fed Recently about 1 day, full Life Force restoration, repeated full feeding before recovery may be lethal;
- Partial Feed: current first-build values victim +10 years, caster -1 year, partial Life Force restoration, no lethal-repeat rule;
- ordinary feeding is explicitly independent of strategic faction hunger and cannot open the feeding-request popup;
- WNG gene ability reconciliation so duplicated/overwritten active genes do not permanently lose their ability gizmos;
- strict near-white Wraith hair enforcement and preference for an available long non-curled/non-braided hair Def, with graphics dirtied after correction;
- four Wraith lineage factions: Sable Brood, Cinder Court, Veiled Hive and Pale Covenant;
- caste-appropriate combat/settlement/peaceful group compositions by lineage;
- strategic faction hunger as a separate save-persistent GameComponent;
- hunger tuning attached to each lineage through `DefModExtension` values rather than four scattered hard-coded faction state implementations;
- genuine strategic hunger thresholds control feeding requests;
- only non-hostile request-capable lineages can issue controlled feeding requests;
- Sable Brood does not negotiate feeding requests and instead converts hunger to higher hostile raid pressure;
- refusal/declining a genuine request can make the lineage hostile and schedule a real raid;
- high strategic hunger independently increases hostile raid pressure;
- accepted controlled feeding ages the selected biological prisoner, applies Life Drained and reduces that lineage's strategic hunger;
- synthetic/Wraith targets are excluded from controlled prisoner feeding eligibility.

## Verification

The core identity/Life Force slice initially exposed a new-code API mismatch: RimWorld 1.6 `Gene_Resource` requires `BarColor` and `BarHighlightColor`. These were implemented, two property-hiding warnings were also cleaned up, and the corrected slice passed.

The subsequent faction/strategic-hunger slice also passed.

Latest minimal verification before temporary workflow deletion:
- RimWorld 1.6 C# assembly build: **SUCCESS**
- Def XML syntax parse: **SUCCESS**

The temporary workflow was removed after verification. Do not recreate permanent audit/release-lock bureaucracy.

## Critical separation preserved

**Ordinary Wraith Drain Life/Partial Feed never opens the strategic feeding-request popup.**

The popup exists only inside the strategic `WraithFactionHunger` component when a real lineage has crossed its configured hunger/request threshold, the player has a valid biological prisoner, and that lineage is politically able to request access.

Mature-Hive local feeding ecology remains a separate upcoming system and must not be wired into this popup merely because it also concerns feeding.

Mature-Hive retaliation also remains separate.

## Explicitly unfinished — next Wraith slices

- exact-pawn Wraith captivity/abduction/rescue continuity;
- Feeding Niche and local Mature-Hive feeding-stock ecology;
- Mature-Hive population, caste balance, hibernation pods, Dormancy Vault and Hive Heart;
- Mature-Hive retaliation;
- Wraith Growth Chamber/bounded biological replacement;
- biological/living-tech progression;
- Living Forge;
- Wraith bioelectric organ relationship;
- **Wraith Grav Engine** progression (never obsolete Gravcore substitution), including corpse pathway where required;
- living weapons;
- Wraith Dart/culling/abduction and exact captive identity transfer;
- Wraith backstories as biography only;
- Wraith discovery/research/progression hooks;
- Wraith craft/gravship and optional CatCraft integration later;
- professional audio/presentation pass later.

Before implementing captivity treatment/escalation details such as experimentation/conditioning/enthrallment, reconcile those specific branches against current plan/corrections instead of assuming an old implementation is still desired.
