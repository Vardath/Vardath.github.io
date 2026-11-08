# Tour defaults, timeout extension and log review — 0.4.5

Reviewed 9 November 2026, Australia/Brisbane.

## Requested changes

- Newly assigned Galactic Sightseeing Tour orders default to **10 stops**, with the existing editable 10–20 range.
- A booked active tour's task watchdog and its own native docking deadline receive **one additional game hour**. The controller remembers the extended absolute value, so polling or saving/loading does not repeatedly pad that same deadline. A subsequent helper-issued deadline gets its own one-hour allowance. Other jobs and player/direct orders are excluded.
- Genuinely cancelled tours receive **one hour above their previous duration-based grace**: minimum **3 game hours**, or the previous measured/scaled estimate plus one hour if longer. Existing saved pending cancellation deadlines gain exactly one hour once, using a persistent marker. Already-disposing or already-departed passengers are not recreated.
- Taxi cancellation stays thirty minutes; stranded-crew recall stays twenty minutes. Active/queued/default tour retention still protects the party through combat, lockboxes and temporary player orders.

Accepted bookings keep their promised stop count, route, passenger identities and fare. Existing orders explicitly configured for twenty stops also keep that setting: change **Tour stops** to ten in Behaviour for later bookings, or assign a new tour order to use the new default. An already-booked twenty-stop trip still needs its twenty verified stops. The default **500,000 Cr per delivered passenger** is retained, including new ten-stop bookings; no fare is awarded before full destination departure.

No mass worker restart, order cancellation or itinerary reset is used. Runtime 42 is retained. The tour wrapper version changes from 10 to 11 for the new default/missing-parameter migration; valid saved settings are preserved. The additional MD time budgets apply on loading the existing save and on subsequent normal controller polls. A deadline already over an hour past its old limit can still expire, and ordinary target/ownership/docking failure recovery remains active.

## What this log establishes

`debug(20261108-232701).log`, 6,086,304 bytes / 34,831 lines; SHA-256 `30bed0b56377d36cc9d95c6f055159fa6cfb0348446bf59e36166ab21a825b10`. Loaded Occupations **0.44** and the same companion versions.

| Recorded new payments | Count | Confirmed credits |
|---|---:|---:|
| Stock-backed off-screen crystal sales | 193 | 12,493,000 Cr |
| Completed full luxury tours | 4 | 16,500,000 Cr |
| **Total** | **197** | **28,993,000 Cr** |

Every logged payment matches its own before/after balance change; no repeated recorded payment IDs were found. The four tours complete twenty actual stops and destination departure: ZBI-439 carries ten passengers through sixteen sectors, IBM-187 seven through seventeen sectors, JAX-879 seven through fifteen sectors, and OEA-953 nine through seventeen sectors. Payments are 5,000,000 / 3,500,000 / 3,500,000 / 4,500,000 Cr respectively. These are evidence for those completions, not a claim that every assigned tour finished. Fifteen scanner station visits also complete.

One actual unpaid cancellation evacuation is logged: Envoy **TNH-332**, contract 1, eight passengers removed at game time **16427.80**. Its Scanner order starts at 15973.14, before that evacuation. The log also has repeated activity reports mentioning timed-out assignments; repeated snapshots cannot be counted as distinct failures. The file does not show active-tour evacuation for every reported premature return, or establish the original cancellation-clock start. The requested extension therefore covers both active booked-tour task/dock budgets and the genuine-cancellation grace, with separate guards and no fabricated completion.

An ordinary task watchdog aborts/retries the current task; it must not clear the passenger contract. The cancellation controller still requires the persistent/current/queued service to be absent before beginning evacuation grace. Resuming the service before expiry keeps the same party and itinerary.

## Other errors and gameplay limits

The log has **1,724 error-tagged entries**, with **zero error blocks explicitly naming this suite**. The earlier cold-start ship registry, explicit-null loadout and bare-faction Auto Trade Subscriptions errors do not recur. CHC and character-model floods are also absent.

Remaining notable messages:

| Group | Recorded entries | Finding |
|---|---:|---|
| Stale mission UI queries | 354 | Invalid mission IDs in native UI calls; originating addon is not identified. |
| Head Hunter speaker callback | 18 | `md.HeadHunterMD.Speaky` passes a null `$FactionRep` to `start_script`. |
| Ship loadout equipment | 7 | `koha_macro` has two engine slots but no compatible available items. |
| Missing ship generators | 24 | Includes Fallen Families plunder ships and Riptide/loanshark military ships with no matching candidate. |
| Third-party patch failures | 59 | Includes the previously named installed patches; an error's patch path does not prove which other mod changed its target. |
| Save-header XML parsing | 108 | Reads capped at `maxsize=0x1000`; not proof by itself that a whole save is corrupt. |

These do not provide a verified merged asset catalogue or the full external callback scripts needed for a safe repair here. No speculative Head Hunter, ship-equipment or global UI patch is added. Protected UI and Inventory Collector remain supported. New visible crystal-drop collection, a physical trader round-trip and every other occupation's complete native loop are not established by this file. No explicit access-violation/out-of-memory crash trace is identified.

## Validation and install

**400 Python contracts** pass, including thirteen new timeout/default cases. Tests execute the shipped budget/grace XML for active and saved deadlines, repeated polling/load-state copies, a new leg, native docking, direct orders, another queued occupation, missing/disposing passengers, estimates longer than two hours, legacy cancellation migration, expiry and re-cancellation. Both controller call sites apply the extra budget before their expiry checks. The old twenty-stop booking/fare remains intact while new defaults are ten. Retained coverage is **91 Lua mocks**, nine native XPath matches across five diff files, and the source/archive audits. These are source/mock checks, not an X4 runtime result.

1. Exit X4, overwrite `extensions/vardath_galactic_occupations` from 0.4.5 and load the existing save. Keep Protected UI and Inventory Collector; companion extension sources are unchanged.
2. Assign a new Tour order: Behaviour should show ten stops. For an existing order still configured for twenty, set Tour stops to ten for its next booking; preserve the current accepted booking. Verify its actual route and final destination departure before payment.
3. Load an active long tour near an old task/dock deadline. Verify it gets one extra hour and keeps the same party/visited sites. Save/load and wait through repeated controller checks: that absolute deadline must not keep moving. Issue a direct order and confirm it retains priority.
4. Remove a persistent tour service while passengers are aboard. Verify at least three game hours (longer measured estimates also gain an hour). A saved pending old grace should gain exactly one hour once. Resume before expiry and confirm the same booking survives; cancel again to start a fresh grace. Temporary interruptions with the service retained must not start evacuation. Taxi remains thirty minutes.
5. Test genuine expired cancellation: no fare or reputation, and retained recruited crew stays aboard. Already departed/evacuating passengers must not be recreated or paid by the migration. Complete a normal new ten-stop tour and check native credits, one vanilla ledger receipt and a General payment notice.

No X4 executable, current save or merged installed catalogues are available here. The new timeout/controller integration remains runtime-unverified; the supplied log predates this change.
