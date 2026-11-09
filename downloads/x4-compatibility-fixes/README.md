# Vardath Compatibility Fixes 1.0.0

[Download the installable ZIP](Vardath_Compatibility_Fixes_1.0.0.zip) · [Technical findings and live checks](vardath_compatibility_fixes/TESTING.md)

Six small XML patches for errors in `debug(20261109-083003).log`. This is a separate extension for X4 9.00, used alongside Galactic Occupations 0.4.7. It does not replace any existing mod folder.

| Error | Correction |
|---|---|
| Fly-by Looting collects incompatible missiles | Check capacity for the actual ammunition ware before calling `collect_drop`; leave incompatible drops in space. |
| GalaxyTrader academy reads a null pilot's name | Require a real captain before building the training entry. |
| Research Blueprints registers a null HQ conversation actor | Filter the actual conversation event against the current assigned HQ manager, after a real event arrives. |
| Native trade routine pairs different wares | Discard the bad offer references and retry through the native delayed search, before creating trade orders. |
| Cached invasion gate exits into the wrong sector | Revalidate a local entry-point list before use. Preserve native defence planning and the original invasion descriptor. |
| Late native mission-thread callbacks | Update only a live mission thread and signal cleanup only while it is waiting; tolerate the documented deferred-signal race. |

Exit X4. Extract the ZIP into the game directory so it creates `extensions/vardath_compatibility_fixes/content.xml`. Enable **Vardath Compatibility Fixes**, keep **Protected UI** and **Inventory Collector** enabled, and load your existing save. No new game is required. The three third-party mods are optional; their patches target the installed folders `fbl`, `galaxy_trader` and `researchblueprintsmod`. Workshop dependencies control load order, while nested patch paths use those folder names. Renamed folders need corresponding path changes.

This extension contains no UI code, ship assets, inventory grants, direct payments, ownership changes, quest resets or forced order cancellation. Galactic Occupations, Builder Hire, Kopis Forge/Astrid and the other companion mod files are unchanged. It prevents specific invalid calls; it cannot reconstruct already-missing equipment or repair saved story progression from a debug log alone.

Validation applies all **22 diff operations** to exact pinned upstream references, checks native diff grammar and relevant engine metadata, executes **nine source/failure-boundary contracts**, and compares ZIP contents to the shipped extension. Full sources are downloaded for validation, not redistributed. **No in-game runtime test was available.** See the testing document for the remaining errors and reproducible acceptance steps.

## Remaining errors

Missing Koha engines, ShipGenerator/loadout candidates, outdated selectors in other mods, Hyperion story state and the HeadHunter import rejected by Protected UI remain unresolved. These need the affected installed extension files and, for the story issue, the relevant save/mission state. The supplied log has no crash stack, so this is not a verified fix for the crash. Failed cargo-teleport probes already take the existing docking fallback; that system is unchanged.

## Reproduce validation

```sh
python -m pip install 'lxml>=5,<7'
python downloads/x4-compatibility-fixes/tools/validate.py
python downloads/x4-compatibility-fixes/tools/package.py
```

The validator downloads checksum-pinned references. `--source-cache PATH` reuses a local cache; `--zip PATH` checks an archive. CI performs the same source and packaging checks. See `tools/sources.json` for exact upstream URLs and hashes.
