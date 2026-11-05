# v1.07 — Automatic main weapon restoration (2026-11-06)

The main gun is now **8000 damage per hit**, exactly **100× the vanilla Terran S Laser Mk2's 80 damage** (not an additional multiplication of the previous Forge damage).

**Existing saves and ships:** the new `VardathKopisAutoMainWeapon` Mission Director script runs once per in-game minute. It discovers all player-owned ships across the galaxy (true owner, including off-sector ships), checks each Kopis Mobile Forge, and if it has *zero main weapons*, uses a weapon-only `create_loadout` to equip the exact `weapon_vardath_kopis_laser_macro` on its standard `con_weapon_01` mount. The action uses `flags="add weapons"`, leaving other equipment and cargo untouched. It then repeats, so a lost gun is replaced again without a new game. Already fitted primary weapons are not overwritten.

The startup spawn fallback now uses the same explicit weapon-only template. The earlier v1.06 one-shot repair script remains solely for save compatibility; v1.07 is independent of it. The nonfunctional dorsal turret socket remains removed. **Restart X4 after updating the extension; do not start a new game.** In-game verification is still required.

# v1.06 — Primary weapon restoration (2026-11-06)

**Fix for the v1.05 unarmed Forge regression.** Restores the pre-v1.05 equipment-ware setup for the original Forge Laser and Forge Beam. The v1.05 update added `<use threshold="0"/>` to these two weapon wares; this change has been reversed without reverting the turret removal, the Builder fixes or the Sector Explorer patch.

- Retains the actual Terran-compatible `con_weapon_01` main gun mount and the original `weapon_vardath_kopis_laser_macro` in the saved starter loadout.
- The startup script now checks whether each newly spawned Forge has a gun; if missing, it retries the original loadout with `apply_loadout flags="add weapons"` (no other equipment or cargo changes).
- A **new, one-time savegame cue** finds player-owned Forges left unarmed by the previous update and applies only the missing weapon. It does **not** overwrite equipped main guns or alter shields, cargo, drones, engines, crew or other equipment.
- The broken dorsal turret socket remains removed. Legacy turret definitions remain available for older saves.
- Static packaging and XML verification are not substitutes for an X4 in-game test; check existing ships after restart.

# v1.05 — repairs and optional Sector Explorer compatibility

- Removed the Kopis Forge's nonfunctional experimental dorsal turret SOCKET and initial turret loadout; the ship continues to use its main gun.
- Kept the older optional turret macro/equipment ware as legacy compatibility data so existing saves with it fitted are not forced to load an unknown macro. New Kopis Forges have no turret connection.
- Corrected the invalid startup cue quote and added missing `use` metadata to all three custom equipment wares.
- Optional compatibility patch for Sector Explorer (`ws_2074838459`): rewrites the old blacklist lookup whose type resolves to null (log: `sectorexplorer` line 86) to use explicit `blacklisttype.sectoractivity`. This is version-specific, not a copy of the entire third-party script, and loads after the dependent mod when present.
- Requires restart; back up saves. Static validation cannot guarantee that X4 applies another mod's script override. If Sector Explorer's logging persists, its installed script may have a different version.

# Vardath — Kopis Mobile Forge (v1.03, experimental)

An **X4: Foundations 9.00** cheat logistics ship extension. Requires **Cradle of Humanity**, **Tides of Avarice** and the **Vardath Living Factions & Builders** extension (as declared in `content.xml`). Does not modify the vanilla Kopis or require Yaki Habitats. This ZIP's structure/XML are tested by GitHub; engine runtime, shipyard availability, movement and cargo behaviour remain unverified. **Back up your save**.

## What the ship is

**Kopis Mobile Forge** is a new **small Terran ship**, duplicating the Kopis mineral-miner geometry and most component geometry and physics. The source X4 model geometry is referenced from the installed Cradle of Humanity DLC; it isn't redistributed.

| Attribute | Design |
| --- | --- |
| Normal speed | **Dart-inspired target ~540 m/s** with an equivalent base engine; actual speed depends on installed engine, ship mods, and X4's physics |
| Speed tuning | Kopis forward drag reduced **3.8 → 0.6**, mass **8 → 1.6**, lateral drag adjusted; vanilla Kopis unaffected |
| Container hold | **1,000,000 m³** |
| Solid hold | **1,000,000 m³** |
| Liquid hold | **1,000,000 m³** |
| Crew | **250 total seats** across captain, service and marines; X4 allocates the crew categories, not independent 250-person caps |
| Drone capacity | **512 units** total, including cargo, building and repair drones |
| Deployables/missiles | **5,000 deployables**, **500 countermeasures** and **5,000 missiles** (subject to game equipment restrictions) |
| Hull | **20,000** |
| Main gun | New **Kopis Forge Laser Mk2+**; same Terran S Mk2 laser projectile/effects but **90 damage vs. 80** (+10, not 10×) |
| Turret | No physical turret slot (removed in v1.05); legacy custom turret definition retained solely for older saves |
| Standard ship | Original Kopis remains unchanged |
| Purchase | New ship ware is offered to **Terran/Pioneer** factions via wares owner entries, average base ship price **8,500,000 Cr**, plus fitted equipment |
| Blueprint | Ship, laser, beam and turret blueprints automatically granted; the startup cue spawns **10 player-owned Kopis Forges** on first activation |

The mod includes a `vardath_kopis_factory_kit` named loadout in its `libraries/loadouts.xml`, with a Terran S engine and shield, Forge Laser, no turret, 120 building drones, 120 cargo drones and 30 repair drones. Whether the high equipment preset actually selects this loadout automatically is unverified; equipment can be selected at a ship dealer if the game exposes it.

## Automatic Astrid replacement (v1.03)

The Astrid cue now **checks continuously every one in-game minute** on new games **and existing saved games** (approximately every 10 real seconds with 6× SETA). It searches the **entire galaxy** for *any* Astrid whose true owner is the player, including an Astrid away from your current sector. If one is found, it creates nothing. If none remains—for example because it was **destroyed, sold, transferred or otherwise lost**—the script creates exactly **one** vanilla Astrid (ship_gen_m_yacht_01_a_macro) owned by the player, **around 3 km from the player's current ship**, with a Yaki pilot and an 85%-filled Yaki crew template. The next poll sees the new ship and stops spawning replacements until the player owns no Astrid again.

The periodic monitor uses a **new Mission Director cue name** so it activates when upgrading an existing save even if the earlier one-time startup Astrid cue already finished. The previous one-time cue has been replaced, not supplemented. It does **not** remove existing Astrids or change their crews, and it does not produce one per minute when an Astrid is already owned. A player ship and valid sector must exist before a replacement is created. The Astrid model requires *Tides of Avarice*, already a mandatory DLC for this mod.

**Static checks verify the XML structure and intended safeguards. X4 runtime behaviour, including the spawn placement, needs an in-game test.** Back up an existing save before upgrading.

## Built-in slow production

An X4 Mission Director cue scans **player-owned** Kopis Mobile Forge ships every **10 in-game minutes**. It attempts to add **one unit of every available ware** categorized as container, solid or liquid cargo from `lookup.ware.list`. That covers known economic resources from enabled DLC and third-party wares that use these transports. Cargo is **real inventory** and limited by each hold's actual free capacity; no continuously accrued currency and no instant filling. Some ware types (equipment, deployables and inventory items) do not qualify. This is deliberately very slow: **six units of each eligible ware per in-game hour**.

Ship production applies automatically, whether piloted or AI-controlled. It is linked to the unique ship macro, so it does not affect vanilla Kopis or other ships.

## Deliver to nearby build storage

Every **2 in-game minutes**, a player-owned Forge within **35 km** of an existing player/friendly NPC station with a genuine queued or active construction project automatically supplies up to **25 units of each recognized construction material** from its own cargo into the **real station build storage**:

- Energy cells, hull parts and claytronics
- Computronic substrate, metallic microlattice and silicon carbide
- Field coils, advanced composites and smart chips
- Turret, shield and weapon components

It only processes the **first eligible nearby station per ship per tick**, to limit unexpected transfers. It transfers actual ship cargo, records each result and refunds excess units if build storage cannot accept them. Moving the ship away stops automated delivery. The method does not create free cargo in the station—everything delivered comes out of the ship's cargo first.

**Important engine limitation:** X4 does not attach native **build storage to a small ship**. The “build storage” function here is a **direct feeder into station build storage**. Although the ship has large drone capacity and the included loadout specifies cargo and building drones, **there are no visible cargo-drone flights** for these MD cargo transfers, and the ship **cannot act as a native XL construction vessel** or accept Find Build Tasks. Building drones in an S-class ship do not make it an XL builder.

## Installation

1. Download `vardath_kopis_production_cheat_TEST.zip`.
2. Extract the single `vardath_kopis_production_cheat` directory into your X4 `extensions` directory, **not into either existing Vardath mod**.
3. Restart the game, enable the extension and keep a backup save.
4. For the intended **10-ship Kopis Forge startup spawn**, begin a **new game**: the Kopis startup cue runs once, around 10 game seconds after the player enters a zone. Upgrading an existing save does not replay that completed Kopis cue. **The Astrid replacement monitor is separate and runs on existing saves**, checking every one in-game minute. The Forge is also registered as a Terran/Pioneer S ship ware.
5. Visit a Terran/Pioneer wharf and check the restored **advanced S weapon socket** for Terran weapons; the custom S turret also uses matching compatibility tags. To test resource production, park a Forge within 35 km of a station building modules and inspect cargo after 10 minutes.

Typical Steam location:

`C:\Program Files (x86)\Steam\steamapps\common\X4 Foundations\extensions\vardath_kopis_production_cheat\content.xml`

## Engine testing / troubleshooting

Test normal speed using a **Terran S all-round Mk1** to compare with the stock Kopis's baseline. The Dart reference is ~540.8 m/s using an Argon S all-round Mk1, so the physics estimate may need iteration. Test how cargo holds combine, cargo drone equipping, crew seats, custom weapon appearance/damage, and whether X4 accepts the additional S turret on a class S model. Test a save/reload during slow production and auto-transfer: the repeat cues use in-game time and do not retroactively credit time missed while unloaded.

Monitor X4's debug log for invalid XML properties or MD expressions and inspect station build storage to verify actual delivery. The XML parser does not validate X4's custom engine semantics.

**Limitations and cautions:** This is a cheat ship: the high cargo storage and resource production will affect the economy. The factory loop visits all matching game wares every 10 minutes per Forge, and the delivery loop examines stations in the ship's sector every two minutes. Keep the number of Forge ships modest if the galaxy is already mod-heavy. The build transfer is an instant scripted action, not physical drone AI. Extra turret geometry/crew on a small hull is experimental.
