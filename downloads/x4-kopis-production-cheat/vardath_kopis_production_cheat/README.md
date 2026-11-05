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
