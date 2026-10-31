# Vardath — Yaki Terran Habitats

**Separate and independent extension for X4: Foundations 9.00.** Requires **Cradle of Humanity**. Does not require Living Factions & Builders. This is an experimental release; tested by static XML/ZIP validation, not in X4.

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

- `libraries/wares.xml`: separate purchasable module wares and Yaki workunit recipes.
- `libraries/races.xml`: Yaki workforce race, modeled on the human workforce race definition.
- `libraries/modules.xml`, `libraries/modulegroups.xml`: separate build planner class.
- `assets/structures/habitat/macros/`: new S/M/L habitation macros with `workforce race="yaki"`.
- `assets/structures/habitat/`: copied/modified *component XML* and original DLC geometry references, no proprietary mesh files.
- `libraries/material_library.xml`, `assets/textures/`: custom DXT1 colour textures/materials; other original texture layers and shader properties are retained.
- `md/vardath_yaki_habitats.xml`: one-time blueprint unlock for newly loaded or existing save games.

Copyright: X4 and Terran DLC assets are Egosoft GmbH property. This mod references existing game geometry and adapts component metadata and materials; it does not redistribute the game's geometry.
