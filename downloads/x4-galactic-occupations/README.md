# Galactic Occupations — 0.2.0 development build

[Download the extension](Galactic_Occupations_0.2.0_DEV.zip) · [Installation and occupations](vardath_galactic_occupations/README.md) · [Implementation report](vardath_galactic_occupations/IMPLEMENTATION.md) · [In-game tests](vardath_galactic_occupations/TESTING.md) · [Static results](STATIC_TEST_RESULTS.json)

This update corrects local-sector work starvation, adds real passenger boarding for taxi and luxury tours, improves component surveys, supplies a Mine Crystals Loadout option backed by custom turret control, and adds payment descriptions and earnings by job to the main Transaction Log. The builder extension also gains the income section: [latest builder ZIP](../x4-living-factions-builders/vardath_living_factions_builders_TEST.zip).

**In-game verification remains pending.** XML/API/source checks and executable Lua tests with native-shaped mock widgets cannot certify X4 gameplay, NPC navigation, turret aim or UI compatibility with your installed version. The environment has no X4 executable, installed catalogs, save or live error log.

Extract the Galactic Occupations ZIP into the X4 installation folder. Its `extensions/vardath_galactic_occupations/content.xml` must be beside the other extensions. For the separate builder TEST ZIP, extract its mod folder into `extensions` as before. Load an existing save; no new game is required by this implementation.

Set **Operating range = 99** for the entire connected, accessible galaxy; 0 restricts work to the home sector and 1–98 impose a jump radius. Jobs rotate sectors after assignments. Tours select from a global landmark catalogue. Physical passenger boarding waits for actual loaded interiors; surveys and harvesting require the relevant physical objects to be simulated.

Default tour: up to ten passengers according to free crew space, ten distinct sites, at least three sectors where available, then drop-off. Default fare: **500,000 Cr per passenger**, up to **5,000,000 Cr**. Taxi fare: **8,000 Cr per delivered passenger**. Service and crystal-sale payments are journaled after actual crediting. The main Transaction Log's income section offers individual payments, descriptions, job filters and lifetime totals. Recent detailed history is capped at 5,000 records; lifetime totals persist.

X4 9.00+. Galactic Occupations has no required DLC/third-party mod and does not change Kopis or other ship assets. Builder DLC requirements are unchanged. Inventory Collector can remain enabled; crystal collection uses real drops.

Developer checks:

```sh
python tools/validate.py
python tools/tests/source_contracts.py
lua5.1 tools/tests/ui_contracts.lua vardath_galactic_occupations
python tools/package.py
```

The optional `--reference /path/to/extracted/X4` validator mode checks matching installed native signatures and full game schemas. It requires `lxml` and extracted `libraries`/`aiscripts` folders.

Vanilla-ledger follow-up: payment labels and verified receipts now appear directly in the existing transaction list, with native search/time-window/pagination. The separate income preview is retained at the user's request. Native IDs, amounts and account graph data are preserved; internal engine database metadata is not fabricated.
