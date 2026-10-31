# Vardath — Yaki Terran Habitats

**Separate and independent extension for X4: Foundations 9.00.** Requires **Cradle of Humanity**. Does not require Living Factions & Builders. This is an experimental v1.1 release; tested by static XML/ZIP validation, not inside X4.

## What it adds

Three **new** station modules using the original **Terran** habitation shapes and connection points, with isolated copies of each Terran component XML and geometry references to the installed Terran DLC:

| Module | Yaki workforce | Original Terran size |
| --- | ---: | --- |
| Yaki S Living Quarters | 100 | Small |
| Yaki M Living Quarters | 250 | Medium |
| Yaki L Living Quarters | 500 | Large |

**Red-and-black visuals:** independently cloned, non-vanilla component IDs use **dark custom hull material**, **red panel and FX materials**, and red exterior light colours. Two small bundled DXT1 DDS maps supply the dark and red material colours. Vanilla Terran modules and existing station builds are untouched. The shape, animation, attachment points, dock/waypoint data, original normal/smooth maps and Terran construction-resource recipes are preserved. Appearance is contingent on X4 loading the custom material and DDS assets correctly and must be checked in-game.

**Yaki workforce:** adds a new `yaki` *workforce race* (not a new faction), the matching production method and busy/idle food recipes. Residents consume **Terran MRE and Medical Supplies**, matching standard Terran per-employee amounts. Recruiting from a station with this workforce is intended to generate Yaki personnel. This is separate from Terran workers or any original Yaki factions.

**Blueprints:** all three are automatically unlocked on starting or loading a game with this extension enabled, without paying the Yaki representative. They are selectable in the station build planner if the engine accepts the new module group.

## NPC Yaki faction integration (new in v1.1)

**New games:** The vanilla Yaki wharf's `yak_wharf` construction plan uses two Argon habitats in positions 13 and 15. This mod patches ONLY those two Yaki wharf entries to the new **Yaki M and Yaki L** equivalents, retaining the existing plan position and predecessor links. The original Terran and other Argon habitats are untouched. X4 must resolve the Terran macro attachment geometry in that fixed plan; this needs in-game visual testing.

**Existing saves:** the vanilla Yaki wharf was already generated before the new plan was installed. A narrow 10-in-game-minute MD check identifies a Yaki-owned operational wharf, checks its current planned module sequence, and—in the absence of an existing Yaki habitat—**queues a single Yaki S habitation** using X4's normal `create_construction_sequence` / `add_build_to_expand_station` workflow. It never expands story-only pirate bases, other factions, or player stations. It records successful scheduling in persistent MD save data to avoid duplicate queues after save/reload. If a new Yaki habitat is already present, the MD script records that instead of duplicating it.

**Important:** vanilla Yaki are not a normal expanding economic faction. This mod does not automatically make them colonise sectors, create factories, or buy construction ships. A queued retrofit needs construction materials and a construction vessel to finish; if no builder responds, it will remain pending. This also means future Yaki buildings not based on `yak_wharf` plans won't automatically add Yaki habitats. The Yaki emergency story plan is deliberately unchanged to avoid interfering with its mission scripting.

**Actual Yaki NPCs:** in vanilla, the Yaki faction's characters are internally assigned race `argon`. A new `libraries/characters.xml` provides independent, cloned Yaki actor categories using `race="yaki"` so the separate workforce race can select appropriately dressed/cybernetic Yaki characters. All vanilla actor IDs and Yaki story characters remain unchanged. Whether the new workforce actor pool recruits correctly still requires an in-game test.

### NPC tests

1. Begin a **new** game with this mod enabled and inspect the Yaki wharf: the M and L habitat positions should be occupied by black-and-red Yaki living quarters, not vanilla Argon modules. Check physical attachment, materials, and workforce.
2. Load a **backup of an existing** save that had the Yaki wharf before installing this mod; after ten in-game minutes inspect the station's construction plan. One S Yaki habitat should be queued, provided it can be connected safely. Supply build materials and an available NPC/player construction vessel so it can finish.
3. Save and reload before/during construction and check there is **only one** added S habitat. Confirm that missions involving Yaki story/emergency stations still behave normally.
4. Once built, verify Yaki workforce, Terran MRE and Medical Supplies, and Yaki-character recruitability.

## Install

Extract the ZIP so your game contains:

`X4 Foundations/extensions/vardath_yaki_terran_habs/content.xml`

Use **only one** copy of this mod. It can coexist with **Vardath Living Factions & Builders v1.3**, but compatibility with existing Yaki habitat packs (which may also define a `yaki` workforce race) is **not** assured.

This mod needs the **Cradle of Humanity** DLC to display the base Terran models and to supply MRE. Do not use it without the DLC.

## Verify in X4

1. Enable the extension and load or create a **backup save**.
2. After about 10 in-game seconds, open a station build planner. Look for the three newly named Yaki living quarters.
3. Preview each size; check that the dark hull material, crimson panels and red navigation lighting appear. X4's proprietary texture/material pipeline is not available in automated tests.
4. Build an S module on a player station. In Logical Station Overview confirm **Yaki workforce** and demand for **Terran MRE and Medical Supplies**.
5. Recruit a worker from the station and confirm the crew is **Yaki**. Check no other Terran habitats changed.
6. Save, reload and check that both habitat modules and workforce survive.

This mod does not create Yaki production factories or a new food ware. The Terran construction material costs are kept equivalent to the vanilla modules.

## Implementation

- `libraries/constructionplans.xml`, `md/vardath_yaki_faction_habitats.xml`: wharf plan replacement and existing-save retrofit. 
- `libraries/characters.xml`: native-Yaki-character clones selectable for the distinct Yaki workforce race.
- `libraries/wares.xml`: separate purchasable module wares and Yaki workunit recipes.
- `libraries/races.xml`: Yaki workforce race, modeled on the human workforce race definition.
- `libraries/modules.xml`, `libraries/modulegroups.xml`: separate build planner class.
- `assets/structures/habitat/macros/`: new S/M/L habitation macros with `workforce race="yaki"`.
- `assets/structures/habitat/`: copied/modified *component XML* and original DLC geometry references, no proprietary mesh files.
- `libraries/material_library.xml`, `assets/textures/`: custom DXT1 colour textures/materials; other original texture layers and shader properties are retained.
- `md/vardath_yaki_habitats.xml`: one-time blueprint unlock for newly loaded or existing save games.

Copyright: X4 and Terran DLC assets are Egosoft GmbH property. This mod references existing game geometry and adapts component metadata and materials; it does not redistribute the game's geometry.
