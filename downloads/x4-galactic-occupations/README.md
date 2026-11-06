# Galactic Occupations — 0.1.0 development build

Standalone X4 extension: [installable source](vardath_galactic_occupations), [ZIP](Galactic_Occupations_0.1.0_DEV.zip), [implementation report](vardath_galactic_occupations/IMPLEMENTATION.md), [runtime test instructions](vardath_galactic_occupations/TESTING.md), [static results](STATIC_TEST_RESULTS.json).

**All twelve occupations have executable AI implementations and native infinite-order declarations. None has been tested in X4 in this development environment. This is not a verified playable/stable release.** There is no installed X4 executable, matching game/DLC catalog set or live game log here. The crystal controller is an implementation of the documented direct turret interface; its physical firing behavior remains unverified. It does not add a native turret-menu enum.

Extract the ZIP into the X4 installation folder. Its `extensions/vardath_galactic_occupations/content.xml` must end up beside your other extensions. Enable Galactic Occupations, load an existing save and select an eligible ship's Behaviour → Default Behaviour. No new game is required by the implementation. See the included README for the expected order names and constraints.

Targets X4 9.00+. No DLC or third-party mod dependency. Existing X4 mods in this repository are unchanged.

Run `python tools/validate.py` from this directory for static checks, `python tools/package.py` to reproduce the archive, or `python tools/validate.py --reference /path/to/extracted/installed/X4` for matching installed AI signatures and full game-XSD validation. The latter requires `lxml` and the game's extracted `libraries` and `aiscripts` folders. Static success is not runtime success.
