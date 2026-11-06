# Job startup and Logbook recovery — 7 November 2026

[Download all four changed mods](X4_Job_Recovery_2026-11-07.zip).

Fully exit X4, extract into the X4 installation directory, overwrite the four included extension folders, restart and load the existing save. Keep Protected UI enabled and other extensions installed. Reassign occupations to ships already switched to Hold Position; intentional Hold/direct orders are preserved.

| Extension | Version | Actual-log repair |
|---|---|---|
| Galactic Occupations | 0.2.2 DEV | Safe location evaluation, saved-order recovery/retry, guarded optional passengers/police/registries, bounded candidate searches and independent paid receipts in General Logbook. Crystal prerequisites report waiting; actual harvesting remains unverified. |
| Living Factions & Builders | 1.75 | Independent shared-cursor paid receipt writer, bounded recovery of latest twenty actual records, no duplicate money and unchanged rates/SETA/debts. |
| Kopis Production Cheat | 1.15 | Astrid-only equipment-use/licence metadata warnings. Forge special weapon, original Forge wares, all weapon assets and existing crew/equipment remain. |
| Yaki Terran Habitats | 1.22 | Supported indexed construction-plan inspection instead of invalid foreach; detects already planned habitats before additions. Existing modules are untouched. |

Clear vanilla Logbook filters, select General/All and search for **Vardath Payment**. New loaded-version and active-order entries help distinguish a running behaviour from completed work; paid receipts require actual journaled money. Ordinary vanilla trade income without a matching mod record is not relabeled as completed work. Native transaction controls remain untouched and no custom income panel returns.

**Crystal mining has not been verified in game.** Fixing the failing start is separate from observing real deposit targeting, hits, drops, collection and sales. Dedicated acceptance instructions are included. The supplied crash log ends during asset loading without identifying a fatal cause; sector density is not established as the cause.

See [review](REVIEW.md) and [seven-mod static report](ALL_MODS_STATIC_REVIEW.json). Source/XML/Lua/package checks cannot demonstrate gameplay, Protected UI runtime behavior or crash resolution.
