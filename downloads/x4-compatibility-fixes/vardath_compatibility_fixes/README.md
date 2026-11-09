# Vardath Compatibility Fixes 1.0.0

Optional, separate X4 9.00 compatibility extension. Install alongside Galactic Occupations 0.4.7; no new game is required. Exit X4 before copying this folder into `extensions`.

Patches six source-confirmed invalid operations: incompatible Fly-by Looting ammo pickup, GalaxyTrader academy entries without captains, Research Blueprints' missing HQ actor, mismatched native trade offers, stale invasion entry points, and late mission-thread cleanup callbacks. See `TESTING.md` for the exact scope, upstream versions and live acceptance tests.

Keep Protected UI and Inventory Collector enabled. This extension has no Lua/UI replacement and does not modify your other mod folders, ships, equipment, crew, payments or ownership. Third-party patches activate only for matching extension folders. Missing engine/ship assets, saved Hyperion quest state and the actual crash cause remain unresolved.

Validated statically and against pinned source/mocked guard scenarios. Not tested in a running X4 instance.
