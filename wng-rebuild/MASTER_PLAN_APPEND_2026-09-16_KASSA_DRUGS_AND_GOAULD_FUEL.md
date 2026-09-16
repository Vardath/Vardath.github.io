# WNG Master Plan Append — Kassa, Stargate Pharmacology and Goa'uld Fuel Fallback

Date: 2026-09-16  
Design authority: Vardath  
Status: **ACTIVE PLANNED CONTENT. Newest explicit Vardath instruction overrides older wording where this append conflicts.**

This append supplements `MASTER_PLAN.md`, `MASTER_PLAN_APPEND_2026-09-11_IRATUS_DIPLOMACY_PHARMACOLOGY_ROYALTY.md`, and `MASTER_PLAN_APPEND_2026-09-16_COMPARATIVE_XENOBIOLOGY.md`.

## 1. Kassa — reaffirmed and expanded

Kassa remains a required WNG farmable crop/food branch.

Stargate identity to preserve:
- Kassa is a corn-like food crop associated with the Lucian Alliance;
- it is deliberately and extremely addictive;
- it is still food, not merely a recreational drug item;
- its value comes from combining calories, convenience and dependency.

WNG gameplay direction:
- Kassa is a plant the player can cultivate in fields;
- harvested Kassa is edible and should provide enough nutrition to function as a genuine staple rather than a token drug-food;
- a colony should be able to sustain itself substantially or entirely on Kassa if the player accepts the addiction consequences;
- regular use creates strong dependence and makes interruptions to supply dangerous;
- Kassa should remain commercially attractive because buyers who become dependent create persistent demand;
- where technically practical and save-safe, factions/traders/settlements exposed to Kassa should become more likely to return for more rather than every trade being stateless;
- this repeat-demand loop should emerge from dependency/economic state, not from a hidden guaranteed-return cheat;
- selling Kassa should therefore be lucrative but ethically and strategically dangerous.

The desired gameplay identity is:

**Kassa solves food scarcity, then turns food security into dependency.**

### 1.1 Kassa-derived harder drugs

Kassa should also become a raw material for a later illicit pharmacology branch.

After suitable research, Kassa can be processed into stronger psychoactive/stimulant products. Exact names and formulas are not locked yet. The design goals are:
- stronger and faster effects than eating raw Kassa;
- substantially greater addiction/overdose risk;
- high trade value;
- useful emergency, combat, industrial or recreational effects depending on the final formulation;
- a reason to cultivate Kassa even when the colony itself no longer eats it;
- later criminal-market/Lucian-Alliance-style content can build on this economy without being required for the first implementation.

These processed Kassa drugs are WNG gameplay extensions unless a specific formulation is directly canon-derived. Keep canon Kassa distinct from newly designed derivatives in labels/descriptions.

## 2. Stargate pharmacology catalogue for later implementation

WNG should gradually add Stargate-derived drugs, medicines and biochemical agents when their mechanics have an appropriate home. Do not dump every chemical into one research node.

### 2.1 Wraith enzyme

Already planned and reaffirmed.

- raw Wraith enzyme: very powerful temporary physical/consciousness boost, highly addictive, dangerous withdrawal;
- refined formulation: safer and more controllable, still addictive;
- weaning treatment: expensive staged treatment rather than instant addiction deletion;
- emergency life-enzyme derivative may be developed later as WNG-original medicine based on the enzyme's canon survival role.

### 2.2 Hoffan drug

Already planned and reaffirmed.

- blocks Wraith feeding on treated humans;
- can poison/kill a Wraith attempting to feed;
- early versions retain severe recipient mortality/immune-system consequences;
- later research may improve survivability but must not trivialize the original danger.

### 2.3 Wraith retrovirus and suppression treatment

Already planned and reaffirmed.

Treat these as separate layers:
- retrovirus initiates suppression of Wraith/Iratus-derived traits;
- follow-up drug cocktail prevents reversion and requires continuing treatment where appropriate.

### 2.4 Reol chemical

Keep as a future infiltration/intelligence drug.

- derived from Reol biology;
- manipulates recognition/perception so the target accepts the user as someone familiar;
- best suited to infiltration, disguise and social operations rather than generic mood manipulation;
- implement only when the source/acquisition and infiltration mechanics are coherent.

### 2.5 Nish'ta

Add as a future Goa'uld biochemical-control agent.

- gaseous biological mind-control compound;
- renders exposed subjects highly suggestible;
- electrical shock/Zat-style discharge can remove the organism/effect in the canon model;
- should function as coercive chemical control, not a normal recreational drug;
- integration must respect ONAC/RimGate ownership and avoid duplicating an equivalent implementation if one already exists.

Hathor's pheromonal control remains a related but distinct mechanism and should not simply be renamed Nish'ta.

### 2.6 Roshna

Add as a future Goa'uld dependency/control drug.

- canon identity is enforced physiological dependence rather than ordinary intoxication;
- suitable for Goa'uld-controlled client populations, captives or species-specific content;
- withdrawal can be life-threatening or fatal where the relevant biology calls for it;
- should be implemented with its dependency/political purpose intact, not as another generic stimulant.

If the Ilempiri or equivalent context is not present yet, Roshna can remain research/planning content until it has a meaningful gameplay home.

### 2.7 Symbiote poison

Record as a future chemical weapon/medicine-adjacent technology rather than an ordinary drug.

- Tok'ra/Tau'ri-derived compound lethal to Goa'uld/Tok'ra symbiotes;
- can endanger Jaffa who depend on a larval symbiote;
- should only be implemented if it does not duplicate ONAC-owned mechanics;
- ownership and compatibility checks come before WNG adding its own version.

### 2.8 Tretonin / tritonin ownership boundary

**Do not implement a WNG duplicate.**

ONAC already owns tretonin/tritonin in the intended mod stack. WNG may recognize or integrate with the external drug if useful, but must not create a parallel competing version.

## 3. Research progression

Use the new Comparative Xenobiology branch as one of the prerequisite streams for appropriate biological/pharmacological technology.

Suggested structure:
- Iratus study and ordinary comparative biology establish foundational xenobiology;
- Wraith-specific medicines require Wraith biology/Life Force or enzyme research in addition;
- Goa'uld compounds require Goa'uld chemistry/technology access and compatibility ownership checks;
- Kassa agriculture can appear earlier than advanced Kassa processing;
- harder Kassa derivatives, sophisticated implants and gene/host-interface treatments sit later in the tree;
- the most powerful treatments should require multiple biological knowledge streams rather than a single cheap research project.

## 4. Goa'uld craft fuel — current explicit fallback rule

This section supersedes the September 11 rejection of a chemfuel fallback.

Vardath's current rule is:

**When ONAC is installed, WNG Goa'uld shuttles/craft that use the external liquid fuel pathway use ONAC's real liquid Goa'uld fuel Def. When ONAC is absent, those craft use vanilla Chemfuel instead.**

Implementation details:
- the supplied ONAC Def currently used by WNG is `ONAC_LiquidNaquadria` (described by Vardath in design discussion as liquid naquadah fuel);
- do not create a duplicate WNG liquid-naquadah/naquadria resource merely to avoid an optional dependency;
- the fallback exists so WNG-owned Goa'uld craft remain usable without ONAC;
- no hard XML/C# reference to an absent ONAC Def may break loading;
- where a craft's fuel configuration is conditional, choose ONAC liquid fuel when the mod is present and Chemfuel only when it is not;
- this rule applies to WNG-owned Goa'uld craft/shuttles using that liquid-fuel system; it does not automatically replace every Goa'uld construction ingredient, weapon resource or external ONAC system with Chemfuel;
- existing ONAC-owned systems remain ONAC-owned.

The design priority is interoperability:

**ONAC present -> use its authentic Goa'uld resource economy.  ONAC absent -> preserve WNG craft playability with Chemfuel rather than hiding or disabling the craft.**

## 5. Compatibility and implementation constraints

- Newer Vardath instructions override older plan/ledger statements rejecting the Chemfuel fallback.
- Do not duplicate ONAC tretonin/tritonin.
- Check ONAC/RimGate for equivalent Nish'ta, symbiote-poison or Goa'uld chemical systems before WNG implements them.
- Keep canon-derived substances clearly distinguished from WNG-original derivatives.
- Drug effects should be mechanically meaningful and carry proportionate addiction, overdose, withdrawal, diplomatic or Ideology consequences.
- Kassa must remain useful food as well as addictive contraband.
- Persistent Kassa demand should arise from actual dependency/trade state where feasible, not scripted guaranteed customers.
- Exact balance values, crop yield, nutrition, addiction chance, processing recipes and market prices remain tunable pending live testing.
