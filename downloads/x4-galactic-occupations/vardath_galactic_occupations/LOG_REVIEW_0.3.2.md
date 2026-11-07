# debug(7).log review — 0.3.2

The supplied log predates 0.3.1. It contains 28,178 lines and 3,112 error-tagged records. The four screenshots show the same combination of successful tour/patrol work and other ships waiting or searching. The private log and screenshots are not republished here.

## Verified gameplay and money

The actual debug payment records contain before/after player balances, not only status text. Their differences equal the recorded payouts:

| Job | Verified work | Actual credits |
|---|---|---|
| Astrid Tours MRN-792 | All ten passengers disembarked after ten distinct sites in seven sectors | 5,000,000 Cr |
| Trade Route Patrol WIO-328 | Three new protected trader arrivals, with close-range samples | 8,000 Cr each; 24,000 Cr total |

The four payments total **5,024,000 Cr** in this log. Earlier unpaid patrol completions remain historical zero-fee work. The activity cards accidentally printed native money units (hundredths), so the tour appeared as `500000000`; this release displays actual Cr. Existing native ledger/receipt accounting was already denominated in credits and is not paid again.

This is evidence for these specific contracts, not every job. Two crystal miners report zero starts and zero items. No paid taxi-only or escort completion, successful scan/map/lure/recruitment/demolition/hack, or completed morale/inspection work is established here. Searching is not counted as success.

## Fixed from actual errors and source review

- **Two null sector-list errors:** an optional cache lookup could assign null to an existing `$sectors` variable. The old presence check regarded that variable as present, then failed at `.count`. Startup now verifies a non-null cache and clones it; both resume labels and the version patch explicitly repair missing/null lists. Null scope refill is also guarded. Native travel result and actual resulting sector are logged as `GO sector travel:` so failed travel can be distinguished from a changing destination label.
- **Hacker order parser warning:** X4 rejects specifying `default` and `immediate` together even when both literals are false. The queued order now omits both, using documented native defaults. Static validation and the cross-mod audit reject this pair. The 0.3.1 live-menu redraw/timeout repair is retained.
- **Passenger room search:** the off-screen path lacked the visible path's native transport-waypoint fallback. Searches through a container can also miss private room slots. A shared per-batch cached helper now queries actual rooms directly and tries actual NPC transport waypoints for boarding, exit and rollback points. Existing actor/context and full-manifest checks remain mandatory. No empty-room timer creates boarded passengers or a fare; missing real rooms can still cause a genuine wait.
- **Scanner prerequisites:** the existing survey task cannot use a capital ship or zero scan caps. These conditions are now reported before galaxy searching, including the native dependency on the player's discovery cap. It does not invent a scan level or mark unloaded modules surveyed.
- **Cargo trade recovery:** 1,423 native `order.trade.perform` failures are present, commonly with code `0x100000`. The repository's Cargo Teleport patch skips docking before native execution; this is a plausible contributor, not a proven explanation for every failure. Universal Cargo Teleport 1.01 adds one normal docking retry if an undocked native attempt fails with zero goods transferred. A rejected partner uses docking for one game hour. Native money/stock/escrow handling remains unchanged; no goods or payments are manually copied. The new fallback itself requires in-game confirmation.

Safe version recovery applies only while the occupation is the active default. Direct orders, passengers, histories and deployed hacker actors are retained. Jobs already intentionally changed to Hold are not overwritten.

## Other errors and unresolved evidence

- Eight saved AI-stack import records include blocked GO callers or incompatible finder contexts. Version recovery is retained; this log cannot verify the new recovery code.
- 56 saved construction-plan diagnostics reference missing removed Workshop extensions. Plans are not deleted or rewritten.
- 322 invalid mission-ID UI queries, 108 computer/NPC macro mismatches and 45 Terran frigate generator/job records occur. Their presence is recorded without guessing ownership or silently editing unrelated installed mods.
- Kuertee crime/rescue errors include null object resolution. HeadHunter errors access a destroyed/missing pilot. Those installed sources are not present in this repository.
- Native Yaki economy finalisation accesses missing `md.$EquipmentTable.{faction.yaki}`. NPC instantiation also encounters missing service slots. The effective faction/mod load order is unavailable; no speculative equipment table or station/crew deletion is applied.
- Five Auto Drones messages explicitly say `errors=0`; their error-tag severity is misleading, but they report completed scans rather than failed actions.

No crash cause is established. Most native trade failures remain un-attributed without a post-recovery log. The large error count is not a count of distinct bugs.

## Verification and next live checks

XML/command/reference checks, actual nullable-cache expression tests, money-unit tests, existing inventory/UI mocks, all seven source/archive audits and GitHub checks accompany the update. No matching X4 runtime/schema/save is available here. Static green checks do not prove that stalled ships have resumed.

After installation, inspect `GO sector travel:` and the updated General activity cards. They should show actual reached sectors, explicit scanner prerequisites, credit units, and passenger progress through valid points. A fresh log is required to verify those stages and the 0.3.1 crystal changes. The successful tour and three patrol payouts above are already proven by the supplied log and are not re-awarded.
