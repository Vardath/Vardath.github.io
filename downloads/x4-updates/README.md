# Native transaction screen repair — three changed mods

[Download all three changed mods](X4_Updated_Mods_2026-11-07.zip).

**Fully exit X4 before updating.** Extract into the X4 installation directory and replace the three existing extension folders. Restart and load the existing save. Keep Protected UI Mode enabled and other extensions installed. The updated Lua overwrites the broken old income code at its existing path; a full restart clears its already-loaded wrappers.

| Extension | Version | Current fix |
|---|---|---|
| Galactic Occupations | 0.2.1 development | Removed the extra income panels and all native transaction rendering overrides; optional text-only callback labels actual monetary rows. Fixed rejected component-state writes, event sources, migration polling and visible-only firing. |
| Living Factions & Builders | 1.74 | Removed the income UI; labels actual native hire/wage/settlement payments through the same optional callback. Rates, debts, SETA and reputation rules retained. |
| Kopis Production Cheat | 1.14 | Guarded Astrid braking when no player ship is occupied. Forge special weapon/assets/recovery and Astrid Tours equipment/crew retained. |

The normal transaction screen keeps its list, graph, controls, account selection and monetary totals. Descriptions are attached only to actual, unambiguous native payment IDs; no synthetic financial rows or re-paid history. With the optional UIX callback, normal search can find jobs and ships; the description shows the service/employer and lifetime earned total for that job. If Protected UI or the installed callback does not permit labels, native labels remain generic. Detailed new payment receipts also appear in the ordinary Logbook, which is a separate vanilla screen.

The connected-galaxy range, ten-capacity actual passenger system, ten-stop luxury tour and crystal/scanning mechanics remain included, with the documented physical-simulation limits. This repair does not turn pending gameplay tests into verified features.

The supplied `debug(2).log` was reviewed for actual failures. Static XML/API/reference/archive checks, seventeen source guards and thirty-one mocked Lua contracts are available; real X4 execution and post-fix logs are still needed. See [review](REVIEW.md), [static results](ALL_MODS_STATIC_REVIEW.json) and the included occupation acceptance instructions.
