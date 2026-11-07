# Reproducible tests — 0.3.0 development

**No actual X4 runtime test has been performed in this environment.** XML/API/reference checks and inventory/UI mocks are separate. Use a backup save, Protected UI enabled, the new extension installed, and a fresh debug log. Keep Inventory Collector and your normal mod load order.

## Hacker: full visible cycle

1. Use an AI-controlled player ship with an existing captain and preferably an idle service crew NPC. Record crew names, roles, counts, ownership and player hacking-tool inventory. Select Galactic Station Hacker, range 99, risk 2. Verify it stays assigned and chooses a real non-player dockable station in another sector.
2. Initially provide no hacking tools. Confirm it waits, does not fly off/hack/gain tools, and inventory is rechecked after **600 game seconds**, including at the expected SETA rate. Add the actual native tool, such as the Security Slicer or Security Decryption System required by the selected panel. The next scheduled check must loan actual tools without duplicating or touching unrelated inventory.
3. Accompany it so ship/dock/security or engineering interiors are loaded. Confirm docking, the SAME existing crew member leaving, traversing native paths to the actual panel and pausing at it. For a captain-only ship, verify the captain leaves and later resumes the same control post. No NPC clone should appear.
4. Compare the chosen panel and its native status before/after. Confirm the real requested effect, native cost and tool consumption. Watch the player's own controls/animation for unwanted effects from the remote native API. If that API refuses a remote invocation, record the reason; this is an unresolved acceptance case, not a successful hack.
5. Follow the same actor back through the dock into a ship room. Completion must wait for return. Confirm unchanged crew identity/role/owner/count, normal captain control, actual undocking and a new station in a different sector. No automatic hacker wage or positive reputation should appear.
6. Repeat with S/M/L/XL docking geometry and loaded/unloaded sectors. Off-screen native transit may differ; missing interiors must produce waiting/failure with no invented effect.

## Station context command

Select an AI player ship, right-click a non-player station, then Hack station. Confirm the native submenu populates real present panels, with active effects disabled. Choose one panel. A finite queued order must preserve the earlier queue and default behaviour, perform one matching hack, return the actor, then end and resume the previous default. Test an existing taxi/tour default with a real passenger manifest and verify its contract/configuration resumes unchanged. Player stations, the currently flown ship, unavailable docks and absent panels must not be hacked.

Choose multiple ships for the same panel: reservations must prevent duplicate costs/effects. Test a second panel later and a different station. The native transaction ledger must still open, search, page and graph normally.

## Hacker failure and save/load

Save/load before tools, during travel, with the actor ashore, after the native call and during return. Verify same actor/token/loan quantities and no repeated native charge. Issue direct movement/Hold orders at each stage. Direct orders must take priority; while ashore, the actor must wait for a restored station docking link and return physically. If the captain is ashore, restore that link with normal in-game controls; do not expect a replacement captain. Test station ownership changes, destruction, ship loss, missing panel, invalid room path and unavailable native bridge. Unavailable interior/panel geometry before deployment must defer after five minutes and try another station; it must not expire a ten-minute missing-tool wait or abandon an already deployed actor. No crew teleport, free tool, fake hack or unsponsored payment should occur. Capture any stalled path with its status and ship ID.

## Actual money tests

Record player credits before/after each completed sponsored contract. Verify native incoming ledger entry, `GO payment:` promised/actual/balance values, one `Vardath Payment` General receipt and the matching activity total. Activity/approach/sight visits are not payments.

- Escort: a foreign trader must reach its real station after meaningful protection; default fee 12,000 Cr.
- Taxi: all accepted actual NPCs must board, depart and disembark; 8,000 Cr per delivered passenger. Test 0/1/10 available berths and interrupted boarding/delivery.
- Tour: board actual NPCs, visit ten distinct sites across the connected galaxy (normally three or more sectors), dwell and disembark. Default fare 500,000 Cr per delivered passenger for ten verified stops. No partial-route/partial-manifest fare.
- Trade patrol: follow actual traffic and verify meaningful protection/arrival; foreign service 8,000 Cr, own trader 0 Cr. Save/load after completion must not pay twice. Previous zero-fee completions are not backpaid.
- Builders 1.75: observe its existing genuine contract/progress payment and the shared-cursor receipt; unchanged source still measures the actual credit delta. Do not count the private income journal as a second payment.
- Hacker, surveys, mapping, morale and other unsponsored tasks: no invented wage. Morale/service reputation requires an actual eligible improvement/completion and obeys cooldowns.

## All existing occupations

For each default verify selection, executable targeting/movement, actual effect, completion, next work, save/load, player-order interruption and invalid-target recovery in at least two sectors. Range 99 must use connected galaxy coverage. A safe deferred action or prerequisite wait is not a successful job.

- Crystal miner: test forward-only fighter, ordinary and missile turret ships, and L/XL; real deposit damage, accurate arcs, real drops consumed, matching immediate player-inventory increase and no captain/cargo restriction. Compare total item quantities with Inventory Collector active. Check no double collection and normal turret modes/armed states afterward. Repeat out of sector; no synthetic harvest may replace missing physics. See `CRYSTAL_REVIEW_0.2.5.md` for dedicated cases.
- Scanner: record individual module/component native scan level; approach a real surface and maintain line of sight. Verify a genuine level/information increase, resume large stations and defer unloaded geometry without marking it scanned. Default ship eligibility is S/M.
- Mapper: actual gate/anomaly destination records, invalid/mission exclusions, and permitted same-ship transit with equipment/crew retained.
- Lure: actual hostile attention and pursuit, valid friendly anchor, breakoff if not followed or outmatched; physical forward firing requires loaded simulation.
- Demolition: actual destructible rock damage/destruction, appropriate weapon/size and next target; no vanished-reference success.
- Morale: actual crew morale increase with limits and eligible faction reputation cooldown; maxed crews produce no improvement reward.
- Inspection: native scan, actual faction illegality, jurisdiction, noncompliance and no selection-only neutral hostility.
- Recruitment: hostile below 25%, actual capture eligibility, probabilistic failure/cooldown and success ownership transfer with original hull/equipment/crew safely retained.

Attach the new complete debug log and the observed ship ID/stage for any failed acceptance case. The older debug(6).log cannot verify new 0.3.0 actions.
