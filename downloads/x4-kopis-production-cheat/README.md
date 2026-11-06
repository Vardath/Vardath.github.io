# v1.15 — Astrid equipment metadata

The supplied log flagged missing equipment-use and blueprint-licence fields on Astrid Tours wares. Added the supported metadata for those four wares only. Existing Forge ware definitions, special weapon assets and weapon recovery scripts are preserved. No equipment, crew or ownership is reset. In-game availability/equipment acceptance remains pending.

# v1.14 — Astrid braking null guard

The supplied log showed repeated brake polling errors while no ship was occupied. The controller now checks that the occupied ship exists before reading ownership or macro. Astrid Tours equipment, crew, speed and berth changes are retained. The Forge hull, special main gun and weapon recovery scripts are unchanged.

# v1.13 — Astrid Tours passenger space

Astrid Tours now has 32 berths, and newly spawned copies use 50% Yaki crew fill so a ten-passenger tour can fit. Existing crew and equipment are retained. The special Forge weapon and its recovery scripts are unchanged.

# X4 — Vardath Kopis Mobile Forge (v1.08)

[Current packaged ZIP](./vardath_kopis_production_cheat_TEST.zip) (GitHub Actions repackages on a source change). Install by replacing the complete `vardath_kopis_production_cheat` extension folder. Restart X4; **continue your existing save**.

**Kopis main gun:** fixed the missing equipment-use data logged by X4. The Forge Laser is **8,000 damage per hit (100x the vanilla Terran S Laser Mk2's 80)**. Existing player-owned Forges are scanned every game minute for missing primary weapons, with a weapon-only repair attempt. The experimental turret slot is not present.

**Other features:** 1 million m³ each container/solid/liquid storage, 250 crew seats, 512 drones, automatic slow resources, construction storage transfers, 10 starter Forges, and continual player-owned Astrid replacement.

**Sector Explorer:** The old optional script override has been **removed** because X4 rejected its `<diff>` root. The actual `fs_exp` script needs to use `blacklisttype.sectortravel`, not obsolete `blacklisttype.travel`. To correct an installed loose XML copy, run `fix-sector-explorer.ps1` with `-ExtensionsPath` pointing to the actual X4 `extensions` directory holding `fs_exp`. If Sector Explorer is only present in packaged CAT/DAT files, use an updated copy from its author or disable it; this helper does not edit packages. The helper backs up the original XML and changes only the obsolete token.

**Requirements:** X4 9.00, Cradle of Humanity, Tides of Avarice, and Vardath Living Factions & Builders. This is a resource-supply cheat ship, not a native XL builder. Runtime weapon mounting still requires an in-game check.

[Full extension documentation](./vardath_kopis_production_cheat/README.md)
