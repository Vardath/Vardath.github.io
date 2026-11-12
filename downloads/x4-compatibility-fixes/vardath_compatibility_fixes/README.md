# Vardath Compatibility Fixes 1.0.4

Eleven targeted XML compatibility patches; 1.0.4 makes four Terran Cadet Chapter 2 long-range-scan yellow help panels dismissible when input progress stalls, retaining all DLC storyline/scan conditions.  1.0.3 extends the Fly-by Looting ammo condition to exclude large capital-class ships that reject native collect_drop for X4 9.00. Install this folder under `extensions`, enable it and load your existing save. Keep Protected UI and Inventory Collector enabled.

Includes the GalaxyTrader destroyed-ship sector-name guard plus the original six guards and Inventory Collector's missing common-handler debug default, HeadHunter's absent-pilot expiry cleanup and Emergent Missions' late rescue callback. Native mission cleanup also takes a stable snapshot before invoking immediate callbacks that can change its source list.

No Lua/UI replacement, ship assets, reward replay, ownership transfer or forced player order cancellation. This extension does not require the new Hyperion. Third-party dependencies are optional and use the installed folder names recorded in the supplied log.

See `REVIEW_1.0.1.md` for current scope and live checks. `TESTING.md` documents the historical 1.0.0 review. Fifteen source/mocked contracts, native diff grammar, 29 unique selector applications and archive/source checks pass. Terran scan input binding and in-game menu state are not changed or runtime tested. New engine paths are not tested in a running X4 instance.
