# Spacesuit exit recovery and supplied-log review — 0.4.1

## Findings from the actual upload

Reviewed `debug(20261108-063558).log`: 6,678,696 bytes, 73,708 lines, SHA-256 `dbba6601c949ad253ef2c762ace4d280bc04ae13cffd3ee411b1120f97469585`. It differs from the previous two uploads. Its header says 8 November 2026, 15:45:21; simulation time runs from about 6098 to 8563 seconds. The loaded extension list includes Occupations manifest 40.

- **11,240 Astrid Tours braking errors**: 10,569 failed removals and 671 failed writes of `$Ship.$vardath_tours_stopdeadline`. Ships do not expose entity blackboards. Kopis/Astrid 1.16 moves the deadline to a persistent MD cue and explicitly stops assisting while the player is in transit, has a spacesuit or does not actually control the yacht. Ordinary flight-assist, input, autopilot and boost guards remain. No Forge equipment asset or weapon recovery script changes.
- **One Occupations parse warning**, line 9341: `entityrole.pilot` is not a native role. Cancelled-passenger recovery now checks the actual ship pilot identity and native service/marine roles, preserving recruited passengers and the player. Both validators now reject unknown role literals using the inspected native roles database.
- **No recorded error identifies this specific spacesuit transition.** The log does not timestamp the player's selection. Improved Spacesuit and Redneck Spacesuit Engine are both installed; their presence/signature notices are not evidence that they caused the failure. No third-party extension has been removed or edited.
- Separate errors include malformed XML while listing save headers, Kuertee CHC lookups on unavailable ship objects, VRO patch misses, missing Terran/other job ship groups and stale construction plans/loadouts. The save-list reads use a 4 KiB limit, so those parse messages do not by themselves establish full save corruption. Their causes are not proven or repaired by this patch.

The session contains **ten finite crystal sale completion records totalling 541,000 Cr**. Four direct service payment records show actual positive balance deltas: two escort payments of 12,000 Cr and two patrol payments of 8,000 Cr. Total recorded payments in those categories: **581,000 Cr**. A morale assignment also completes. These are new completion/payment lines, not sums of repeated activity snapshots. There is no completed taxi/tour fare in this log; a tour still reports `0/2` boarded and unavailable dock/ship room points. The review does not call passenger boarding fixed or every role runtime verified.

## What the new safeguard does

The existing vanilla **Use Spacesuit** confirmation remains responsible for normal exits. A small additive observer around `UserQuestionMenu.confirm` records only a confirmed transporter destination whose actual component is a zone, together with the enclosing source ship. It forwards the native confirmation exactly once and keeps its return values. It adds no screen, menu entry, ledger replacement or continuous forced-eject action. Missing observer APIs do not block the native action.

For that explicit request only, MD waits twelve game seconds. A healthy exit requires a real player spacesuit, both native control references pointing to that suit, and no remaining player room. Healthy exits immediately clear the request. Sitting down, changing room/ship/sector, docking the source, destruction or loading a save clears it too.

If the native handoff remains inconsistent, the player is not in native transit/conversation and the original context still matches, MD makes **one** native `teleport_player_to_spacesuit` call with `emergency=true`, `instant=true`, `launch=true`, `allowinhighway=false`. The documented emergency form positions the suit outside the current object's bounding box. The request is consumed before calling the engine. Two seconds later the logbook reports whether the actual suit/control/room state is consistent; an attempted action alone is not called success.

If the engine keeps the player marked in transit for thirty game seconds, recovery expires with a logbook notice instead of interrupting an active native transfer. A fresh explicit selection can arm a new request. The safeguard does not monitor every player movement, override camera functions, create another suit manually, change crew/control posts or change ship orders. An engine-side view-only fault with otherwise consistent script properties is not detectable by this check. Direct airlock triggers that bypass the vanilla confirmation are not intercepted.

## Verified interfaces and preservation

Inspected native 9.00 sources at `ArtByunex/x4-foundation-artbyunex`, pinned commit `e3e8a345e5624db118bff3eb171b60b0993fcc2c`:

- [Transporter menu](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/ui/addons/ego_detailmonitor/menu_transporter.lua): zone destinations open the existing UserQuestion confirmation.
- [Confirmation menu](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/ui/addons/ego_detailmonitor/menu_userquestion.lua): native `TransportPlayerToTarget` call.
- [Roles](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/libraries/roles.xml): `service`, `marine`, `passenger`, `prisoner`, `trainee_group`, `worker`, `unassigned`; captain is a control post/actual pilot, not an invented role.
- [Script properties](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/libraries/scriptproperties.xml) and extracted 9.00 `common.xsd` command metadata: suit, room, controlled object, entity transit and native suit teleport attributes.

Requires X4 9.00 as before. Keep Protected UI and Inventory Collector. Replace the Occupations and Kopis extension folders in place, restart X4 and load the existing save. No new game or equipment reset. Builders, habitats, drone stocking and cargo teleport source remain unchanged. All 0.4.0 delayed crew/passenger recovery remains present.

## Validation and live checks

Static XML/API/reference/archive checks and mocked native-boundary tests pass. There are 348 Python contracts, including 21 new spacesuit/braking/role checks, the promoted-captain retention case and 24 survey/boarding contracts, plus 91 Lua mocks including 13 new confirmation observer checks. These exercise the actual shipped XML/Lua, refused native actions, interrupted requests and component state; they cannot prove engine camera, collision or mod-load-order behaviour. The source now also repairs the passenger blockers and extends the scanner; see [SURVEY_BOARDING_0.4.1.md](SURVEY_BOARDING_0.4.1.md). **No X4 executable or matching installed save/catalogs are available here. The new recovery is not live verified.**

1. On the existing save, restart with Occupations 0.4.1 and Kopis 1.16. Keep the current UI protection and spacesuit mods. Check a fresh debug log: no `entityrole.pilot` warning or Astrid component-blackboard errors.
2. In an undocked S/M ship and then Astrid Tours, use the normal transporter's **Use Spacesuit** confirmation. A normal exit should happen once with suit controls, suit HUD and no forced second exit after twelve seconds. Re-enter normally. Repeat from an L/XL airlock using the confirmation flow where available.
3. If the reported partial transition recurs, do not move to another ship while the safeguard checks it. After twelve game seconds, verify one native recovery and its General logbook result. Verify actual space movement, equipment use, oxygen HUD and normal re-entry; a positive script-state result alone does not prove the camera works.
4. Select another transporter destination, cancel the confirmation, take the pilot seat, teleport elsewhere or reload during the wait. None should eject the player later. Emergency ejection and direct airlock actions retain native handling. A permanently in-transit case should log expiry, not loop.
5. Fly Astrid Tours at full travel speed. With flight assist on, release flight input: stop target is 2.5 seconds plus the 0.1-second polling interval. Verify input, boost, autopilot and flight assist off prevent the assist. Exit into the suit during this test: neither the suit nor a cached occupied yacht should be braked.
6. Retest the existing cancellation/crew-return sequences in [RECOVERY_POLICY_0.4.0.md](RECOVERY_POLICY_0.4.0.md). Promote a booked passenger to captain, then expire a cancelled booking: preserve the captain. Verify actual departures, no cancellation fare and native ledger receipts for completed work.

If already trapped before installing, this code does not guess an old exit request. Use the existing **Teleport To** action back onto a ship if available, then retry the confirmed Use Spacesuit flow. Capture the resulting debug log if the native transfer remains stuck.
