# v1.73 — Main Transaction Log income details (2026-11-07)

**Current download: [ready-to-install TEST ZIP](./vardath_living_factions_builders_TEST.zip).** Extract its mod folder into X4's `extensions` directory and replace the existing copy. Existing saves and contract ledgers are retained.

The existing vanilla transaction list now displays verified builder payment labels/receipts through its normal search and page controls. The requested preview panel is retained too. Open the player Transaction Log for the new **Occupation & builder income** section under the graph. It records each new hiring fee, active-construction wage, standby wage and final settlement with ship, employer, station, game time and the actual credited amount. Switch to lifetime totals or filter individual payment history. Detailed history retains the latest 5,000 shared records; lifetime totals persist. Pre-update payments are not reconstructed.

The 200,000 Cr hiring fee, 100,000 Cr/hour active rate, 25,000 Cr/hour standby rate, SETA billing and existing reputation rules are unchanged. Either this extension or Galactic Occupations can supply the UI; enabling both creates one shared section. No new dependency or game is required. Menu behavior still needs in-game verification.

Earlier version notes follow.

# v1.72 — Builder payroll numeric-type correction (2026-11-06)

X4 treats `$Delta / 1h` as **time**, not a dimensionless float. Multiplication by `100000Cr` or `25000Cr` caused the logged `Invalid data types for arithmetic operation` errors and prevented accrued hourly payments. The expressions now explicitly cast the duration ratio to float using X4's `(... )f` syntax, preserving existing save ledgers, 200,000Cr hire fees, 100,000Cr/h active work, 25,000Cr/h standby, and SETA elapsed-time accounting. This is a source fix; confirm actual payout in game.

# X4: Foundations — Vardath Living Factions & Builders

**Historical v1.4 — experimental X4 9.00**

**[Download v1.4 ready-to-install ZIP](./vardath_living_factions_builders_v1.4.zip)**

Extract the `vardath_living_factions_builders` directory to your X4 `extensions` folder. Replace v1.3 in place. **Cradle of Humanity DLC now required.**

**[Full features, installation and test instructions](./vardath_living_factions_builders/README.md)**

Version 1.4 filters out **hostile NPC employers** at the request broker, native request acceptance and contract registration stages. Only factions that currently allow the player to dock can hire a builder. Once the ship has done actual construction and the employer's station build queue is fully completed, a one-time **+0.00064 internal relation** reputation reward is granted. It is recorded in the saved contract ledger; no reputation for accepting/canceling jobs or travelling. The initial hiring fee and hourly rates are unchanged.

Version 1.3 added a separate selectable New Game start: **Terran Shipwright — Yaki Company**, as a Terran woman wearing the white skirt/dress, aboard a player-owned Terran **Kyushu** builder with a veteran **Yaki** crew. The ship starts fully equipped with construction drones. This start is exclusive to a **new game** and requires **Cradle of Humanity DLC**.

Version 1.2 introduced a **200,000 Cr one-off faction hiring fee** plus **100,000 Cr per in-game hour constructing** or **25,000 Cr per hour awaiting construction**. A persistent, per-builder contract ledger records time already billed, debts and the employer. Wages are settled at hourly intervals and the final partial amount when the contract ends.

The v1.4 scripts are **structurally validated, but in-game payment and save/reload behaviour remain to be tested**.

Version 1.2 also fixed the active request broker's periodic reset and skips expensive faction station scans when no player builders are free. Version 1.1 ZIP is preserved for regression testing.
