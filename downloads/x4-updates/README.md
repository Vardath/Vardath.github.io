# X4 updates — 7 November 2026

[Download all three changed mods](X4_Updated_Mods_2026-11-07.zip).

Close X4, extract into the **X4 installation directory**, and replace the three existing extension folders. The archive contains `extensions/vardath_galactic_occupations`, `extensions/vardath_living_factions_builders`, and `extensions/vardath_kopis_production_cheat`. Other extensions stay installed. Load an existing save; no new game is required by the implementation.

| Extension | Version | Changes |
|---|---|---|
| Galactic Occupations | 0.2.0 development | Connected-galaxy work rotation; up to ten actual NPC passengers according to free berths; luxury passenger tours with ten distinct sites and a default 500,000 Cr fare each; corrected module surveys; Mine Crystals Loadout option and custom controller; verified payment labels/receipts in the existing vanilla Transaction Log, plus retained income preview. |
| Living Factions & Builders | 1.73 | Verified builder payment labels/receipts in the existing vanilla transaction list; income preview and lifetime totals retained. Existing hire/active/standby rates, SETA accounting and contract state remain. |
| Kopis Production Cheat | 1.13 | Astrid Tours remains a separate Yaki-crewed cheat yacht with dedicated 3× thrust and 1,000× weapon/turret projectile damage. Increased to 32 berths and 50% new-spawn crew fill to make room for ten passengers. The Forge hull, special weapon and recovery scripts are preserved. |

Use **Operating range 99** for the whole connected, accessible galaxy. Jobs honor native path/access/blacklist limits. Real boarding waits for actual NPC entry into the ship; a reserved passenger template does not count. The engine must stream the docking/ship interiors. Physical crystal harvesting, demolition and module raycasts depend on physical simulation; unattended OOS execution is not claimed.

Luxury tours pay after the required distinct visits and passenger drop-off: normally **500,000 Cr per passenger, up to 5,000,000 Cr**. Taxi pays **8,000 Cr per delivered passenger**. The existing main Transaction Log now shows job/employer descriptions, actual payment amounts, search and pagination. A receipt is explicitly marked if the native reward action supplies no matching detailed entry. The separate income section is retained for preview as requested. It does not change the account balance or fabricate internal engine transaction IDs.

Audit scope: all seven repository X4 extensions, including unchanged Yaki Habitats, Faction Invincibility, Station Auto Drones and Universal Cargo Teleport. XML/API/packaging checks, sixteen occupation source guards and thirty-six executable mocked UI checks are distinct from in-game testing. The two builder economy selectors were checked against published native 9.00 source and match. See [the full review](REVIEW.md) and [static report](ALL_MODS_STATIC_REVIEW.json).

**Runtime acceptance is pending.** There is no X4 executable, installed catalog set, save or live game log in the build environment. Menu rendering, real NPC pathfinding/boarding, turret hits, scan effects, recruitment, save/load and OOS gameplay must still be tested. Reproducible tests for every occupation are included in the Galactic Occupations extension.
