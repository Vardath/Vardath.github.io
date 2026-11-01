# Vardath — Yaki Terran Ring Habitats (v1.2)

Three habitation modules, **and only three**: exact S, M, and L copies of the Cradle of Humanity Terran circular ring habitats, recoloured red and black and configured for a distinct Yaki workforce.

Requires **X4: Foundations 9.00** and **Cradle of Humanity**. No dependency on Living Factions & Builders. The original Terran and Argon modules are not modified. Source and ZIP are statically validated; no claim of successful X4 in-game rendering or NPC construction is made until tested in the game.

## The three modules

| Build-plan name | Original Terran component and geometry | Yaki crew/workforce places |
| --- | --- | ---: |
| Yaki S Living Quarters | `hab_ter_s_01` / `hab_ter_s_01_data` | 100 |
| Yaki M Living Quarters | `hab_ter_m_01` / `hab_ter_m_01_data` | 250 |
| Yaki L Living Quarters | `hab_ter_l_01` / `hab_ter_l_01_data` | 500 |

Each component is a full clone of the original Terran ring, not a generic station piece. It retains its **four original snap connections**, original attachment positions and orientations, lighting/animation structure and waypoints. The size-dependent ring snap offsets are ±400m (S), ±600m (M), and ±800m (L) on the X/Z axes. Original meshes stay in the Terran DLC; none are redistributed.

Visual differences are limited to **black/dark hull, red surfaces and red lighting**. The mod includes separate material definitions and small dark/red DDS textures. Rendering remains subject to the X4 renderer.

Each housing module provides `workforce race="yaki"` with Terran MRE and medical-supplies provisioning. A custom Yaki workforce race and independent Yaki actor categories preserve vanilla Yaki story characters and let recruits use Yaki-appropriate characters. It takes time, supplies and available employees for a station to fill its workforce; the modules do not instantly create free marines or service crew aboard ships.

## Why the old modules looked disconnected

The old extension had copied the Terran meshes and snap coordinates, but it **did not register the custom components/macros in the asset indexes**. It also hard-replaced two Argon habitats in the existing Yaki wharf's fixed construction plan with Terran ring macros, without adjusting the geometry-dependent placement. The replacement layout was unsafe.

**v1.2 fixes both:**

- `index/components.xml` and `index/macros.xml` register the **three** independent component/macro pairs correctly.
- The unsafe `libraries/constructionplans.xml` override has been **deleted**. Vanilla Yaki station pieces and their original placement are preserved.
- New and existing games use one narrowly scoped Yaki-wharf retrofit script. Every ten in-game minutes, it checks an actual **Yaki-owned wharf**. When idle with no outstanding construction tasks, it requests whichever Yaki S/M/L rings are missing and uses X4's **native construction-sequence generator** with real Terran structural connector macros to find viable attachments. It queues normal faction-owned station construction, not free instant buildings.
- It checks the current station plan before requesting more rings, so it will not duplicate already planned S, M or L modules. A save upgraded from v1.1 with only the S ring can receive the M and L as normal construction work.
- Other factions' stations, Yaki story emergency bases and vanilla Terran habitats are left untouched.

**Limitations:** X4's sequence generator must find sufficient space and valid snap/connector geometry on the existing Yaki wharf. If it cannot, no new modules can be safely queued; the mod does not force overlapping modules. Yaki are not an ordinary sector-expansion faction, so this focuses on their actual wharf instead of promising that the faction will found new factories.

## Installation — important when replacing v1.1

1. Quit X4. Make a backup save.
2. **Delete** the existing `extensions/vardath_yaki_terran_habs` directory before extraction. Do not merge the new files into the old directory: doing that would leave the obsolete, unsafe `libraries/constructionplans.xml` override in place.
3. Extract `vardath_yaki_terran_habs_TEST.zip` so the installed path is:
   `X4 Foundations/extensions/vardath_yaki_terran_habs/content.xml`
4. Start the game and verify the extension is enabled.

## In-game tests

1. In a player station's Build Planner, locate exactly **Yaki S, M, and L Living Quarters**, one of each size. Each should preview as the correct Terran ring, recoloured dark red and black.
2. Preview each module and move it toward a compatible station snap location. Verify the ring shows **all four original connection options** and can attach where the vanilla Terran ring can.
3. Build one of each. In Logical Station Overview, confirm the Yaki workforce and its Terran MRE/medical-supplies demand. Verify that recruitable residents appear as Yaki when workforce grows.
4. Inspect a Yaki-owned wharf after it has no outstanding build tasks and an additional ten in-game minutes have passed. The faction should have queued some or all of the missing three Yaki ring variants through the ordinary construction system, provided the station plan has available attachment space. Deliver supplies and allow a construction vessel to work.
5. Reload a save and check neither duplicated construction nor broken vanilla Yaki wharf geometry.

**Older save caution:** If v1.1 already physically generated broken ring replacements in a wharf's build plan, simply updating the mod cannot safely reconstruct the wharf's already-saved station geometry. A backup taken before the earlier modification is the reliable comparison.

## Implementation

The three assets are:
`assets/structures/habitat/vardath_yaki_hab_{s,m,l}.xml` and `assets/structures/habitat/macros/vardath_yaki_hab_{s,m,l}_macro.xml`.

Their asset index registrations are in `index/components.xml` and `index/macros.xml`.
`libraries/races.xml`, `libraries/characters.xml`, and `libraries/wares.xml` provide Yaki workforce personnel and upkeep.
`libraries/modules.xml`, `libraries/modulegroups.xml` and the three wares expose the exact three build-plan items.
`md/vardath_yaki_habitats.xml` grants the three player blueprints.
`md/vardath_yaki_faction_habitats.xml` handles ordinary Yaki wharf expansion.
`libraries/material_library.xml` and `assets/textures/` provide colour materials.

X4 and Cradle of Humanity are Egosoft products. This mod references existing Terran DLC geometry without redistributing proprietary meshes.
