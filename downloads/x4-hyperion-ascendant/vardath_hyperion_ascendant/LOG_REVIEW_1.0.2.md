# Hyperion Ascendant 1.0.2 — 215715 log and builder/storage update

## Recording and confirmed previous fixes

`debug(20261109-215715).log`: **1,798,240 bytes / 11,357 lines**, SHA-256 `90445c5fd88d38d09e2887b0713ac0ec5fc7d0daf9f2c9648f36bf9332b33a40`. It loads Ascendant **1.0.1**, Occupations **0.4.8**, Compatibility **1.0.1** and X4 **9.00**. There are 1,057 error-tag occurrences, many repeated import/preset messages or initialization diagnostics sent through error loggers. No exact fatal/exception/access-violation/out-of-memory/crash-dump marker appears.

The previous delayed gate recovery is now observed in the actual game: at **44813.45** it prepares the Cloudbase Southeast scan; at **44814.49** the original native handler selects TYF-442 toward Third Redemption and our controller reports the resumed stage. No missing-listener, Ascendant ware-use/blueprint-owner or naming warning recurs. This confirms that boundary, not completion of the whole quest or the new builder/storage code.

The file contains **thirty uniquely keyed, balance-matched payments**: nineteen crystal sales **1,424,000 Cr**, eleven tours **54,000,000 Cr**, total **55,424,000 Cr**. Internal money fields are hundredths of credits; these totals are actual credits. There is no duplicate ship/service/invoice key. This records those completed services, not every occupation or the new capacity features.

## Requested implementation

| Capacity | Kopis Forge source | Ascendant 1.0.2 |
|---|---:|---:|
| Container cargo | 1,000,000 m³ | 2,000,000 m³ private bay |
| Solid cargo | 1,000,000 m³ | 2,000,000 m³ private bay |
| Liquid cargo | 1,000,000 m³ | 2,000,000 m³ private bay |
| Shared drone storage | 512 | 1,024 |
| Shared deployables | 5,000 | 10,000 |
| Countermeasures | 500 | 1,000 |
| Missiles | 5,000 | 10,000; no regeneration |
| Total crew berths | 250 | 700 as requested |
| Internal S storage | No added S bay | 1,000; original Hyperion pads retained |

Existing bays are never removed, so a legacy ship can retain a little extra container capacity and its original two S slots (1,002 total). Existing cargo, equipment/modifications, crew, orders, docked ships and ownership are not reset. Private new macros avoid increasing the original Hyperion, Forge or other ships’ capacities. The maintenance script uses the native `create_module` command for missing bays and checks real capacity afterwards. It does not pretend a rejected addition succeeded. A failed native attachment is latched rather than repeatedly creating parts; replenishment has its own independent root cue. Existing universal cargo is preserved instead of mixing incompatible multi-type and single-type storage.

Native module attachment to an existing ship, registration of the additional bays, and the resulting docking/launch flow remain **unverified in X4**. `create_module` and its parameters are present in the actual schema and act on an object, but the mock successful callback cannot prove the engine will accept this particular ship/macro combination. **Pending** in the log is a diagnostic requiring a new runtime log, not a completed upgrade. There is no destructive ship replacement fallback or claim that static validation proves migration.

## L construction capability

The actual native files were checked: both `order.build.find.task` and `order.build.deploy` require `primarypurpose="purpose.build"`, with no XL requirement. The ship-class defaults provide a construction-vessel connection to all ships. `loadoutrules.xml` explicitly supports construction drones on `ship_l ship_xl` with build/dismantling purpose. The right-click Build action also checks the build purpose rather than XL size. The Ascendant therefore remains class L and adopts the native builder type/build purpose, while retaining weapons, bridge, docks and its original carrier repair module.

Two narrow XML patches extend actual discovery: the station build-storage request’s existing XL/build-purpose search also includes L, retaining relation and purpose guards; optional Living Factions and Builders 1.75 payroll also includes L while retaining every real assignment, NPC station, time, payment and reputation condition. Native stock signatures are pinned and both selectors match once. No Builder mod source, rate, order implementation or UI is replaced. No new station progress, wares or fake construction payments are produced.

New ships start with 30 construction drones, 20 cargo drones and eight original repair drones. An older ship with no construction drones can receive one starter kit of up to 30 if there is room; existing stock is retained. Choose native **Find Build Tasks** or the normal station Build command. Real station resources, normal access, a pilot and actual construction work remain required. Live acceptance must verify assignment, drone work and module progress; the source checks do not establish those runtime effects.

## Slow replenishment

Every ten game minutes, checked once per minute: up to **five flares**, **one advanced satellite**, **one resource probe**, **one navigation beacon**, **one Friend/Foe mine**, **one cargo drone**, **one construction drone**. Native English text proves that Friend/Foe is `weapon_gen_mine_03_macro`; `_01` is the standard Mine and `_02` is Tracker. No guessing or substitution is used.

Each ship saves its own due time, which advances before adding anything. Save/reload and large clock jumps do not create catch-up batches. Ammo checks its actual shared free capacity; drones use `add_units`, because the native schema warns that `add_ammo` ignores unit limits. Requested/unavailable drones still reserve their stored units and are not treated as losses. Priority rotates when one slot remains. The script logs observed additions, not intended quantities. Only exact player-owned Ascendant macros are processed across the galaxy. Ship flight, orders, passengers and crews are not managed by this controller.

**No ordinary cargo, resources, credits, crew, missiles, normal satellites or repair drones regenerate.** Consumables are stored rather than deployed. Native creation/limits, SETA scheduling and save/load require in-game checks despite the successful mocked boundaries.

## Remaining log errors

No error block explicitly names the Vardath suite in this recording. Two native `order.trade.perform` transfers involving GRM-Kobayashi Maru fail with `0x100000`; the merged trade state is absent, so their cause is not guessed or suppressed. Other entries include 59 foreign failed/multiple selectors, 280 non-crafting/inventory-resource warnings, 84 obsolete construction-plan blocks, 30 ShipGenerator-related blocks, four invalid `player` race entries, 48 clipped `maxsize=0x1000` save-header XML messages and HeadHunter’s protected import, plus existing external mesh/engine/UI issues. Missing source stacks and effective catalogs prevent safe blanket edits. Removed/disabled preset dependencies are not reinstalled. Protected UI and Inventory Collector remain enabled; no Lua import is arbitrarily whitelisted.

## Failed GitHub run

For previous commit `3a5a1d1`, all three mod validation/audit workflows passed. Pages run **42703772950** built successfully but timed out after ten minutes in **syncing_files** during publishing. Retrying its failed jobs was authorized and performed; attempt two also failed. This is recorded separately from game tests. The downloadable GitHub ZIPs remain independent of Pages. New publication triggers a fresh deployment; final delivery must report its actual state, not claim that a retry alone fixed it. No unrelated site content or working mod tests are removed to hide the failure.

## Validation and acceptance

**42 source/mocked tests** pass with thirty pinned references, native action/attribute checks, XML/diff grammar, two native story selectors, two construction/payroll selectors, and ZIP/source comparison. The tests execute the actual service XML with explicit native callback mocks and reject unsupported expressions/actions. They cover caps, retained old data, repeated migration, rejected/throwing attachment, universal cargo, separate maintenance roots, saved due times, no clock-jump catch-up, in-flight inventory, rotating priorities, refused supply and exact ownership scope. No running X4 executable, user save or merged catalog is available.

1. Exit X4 and overwrite this extension, load the same save, and allow roughly two game minutes. Inspect the unchanged owned ship ID, gear/modifications, crew, cargo, docked S ships and orders. Check actual cargo/crew/drone/deployable capacities and the General Logbook **verified/pending** entry. A pending entry needs its native errors examined.
2. Dock/retrieve/launch S ships through the existing physical pads, including more than the former capacity. Check that earlier stored ships survive the retrofit. Test remote and player-present operation, save/load and a second owned Ascendant. There must be no duplicate added bays or replacement ship.
3. Assign native Find Build Tasks or a normal station Build order. Verify a real buildmodule assignment, construction drone work, actual station module progress and completion. With Builder Hire installed, verify its existing native ledger hiring/wage payments and reputation conditions on an eligible NPC project. Insufficient station resources must remain a real stall.
4. Note the initial inventories and wait ten game minutes, including SETA. Verify only the seven requested supply types increase at the stated rates. Test nearly full/shared stores, building/trading drones in flight, reloading immediately before/after the due time, selling/reacquiring a ship and different ships’ independent timers. No free trade wares or duplicate in-flight units may appear.
5. Recheck normal combat, player input, taxi/tour bookings and native gate investigation. The existing drive/brake/weapon definitions and other occupation sources remain. Attach the complete new log and the affected ship ID if any actual native capability is still pending or failed.
