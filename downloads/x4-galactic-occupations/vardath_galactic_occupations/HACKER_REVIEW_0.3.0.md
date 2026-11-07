# Hacker and supplied-log review — 0.3.0 development

7 November 2026. Reviewed uploaded `debug(6).log` (24,309 lines; 2,096 error-tagged records). The private log is not included in this public repository.

## What the log actually establishes

- Four `GO completed:` entries verify Trade Route Patrol arrival/proximity completion for WIO-328. The source passed `0Cr` into the convoy worker, so those completions genuinely had no service payment. This release changes future verified foreign-trader arrivals to **8,000 Cr**. It does not invent historical receipts or backpay based on diagnostic counters.
- Twenty crystal activity entries show the obsolete deployed-beam preflight and zero attempts. They are evidence from the older build, not proof that the 0.2.5 all-size weapon/inventory correction harvested anything. This release retains that correction unchanged.
- The log does not verify a completed paid taxi/tour/escort contract. Activity messages and visits are not delivery or payment evidence. Some ships remain seeking work or waiting for interiors; one tour reports 73 task cycles without a completed passenger contract. None is relabelled successful here.
- Nine AI import errors involve old saved GO/native call stacks (blocked caller with no child, or incompatible child/caller context). Versioned default wrappers and the current runtime recovery cue use the native editable home parameter to restart eligible active defaults once. They do not replace intentional Hold/direct orders, erase passenger history, or restart a hacker while its actor is deployed ashore.
- No additional post-import GO AI/MD runtime exception was identified. That does not establish correct gameplay: the log still contains idle/waiting/incomplete work.
- Forty-four Kuertee script errors, Khaak/Xenon computer-vs-NPC macro errors, missing Terran frigate shield assets, station-defensibility and Khaak-production messages, and vanilla slider-limit errors remain outside the editable extension sources here. They are not patched speculatively.
- Nine `PathingManager::AddOrder` errors occur at the same timestamp with vanilla/VRO trading context nearby. The log does not establish which caller caused them. No crash cause is proven. The Auto Drones lines containing `errors=0` are diagnostics, not failed drone actions.

## Implemented changes

- Default `VGO_hacker`, worker job 13 and finite queued `VGO_hackonce`, with additive native station submenu. Range 99 retains unlimited connected-sector scope; autonomous hacking defaults to risk 2 but requires actual docking permission and matching dock size.
- Query actual station rooms for supported native control-panel types. The native panel API determines the exact slot/type, required inventory wares, amount and price; the submenu uses actual panel names. Already active effects cannot be selected again.
- Use an existing available service/marine NPC, otherwise the existing captain. Preserve identity, role, owner and control post. Temporarily protect the actor from disposal; release that temporary reservation on return. No cloned/disposable substitute, crew-template removal, ashore room teleport or forced crew ownership change.
- Retrieve actual tools from player inventory before travel; measure source removal and destination credit, roll back partial failures and retain failed returns. Missing tools recheck in ten **game** minutes. Native consumption is serialized with other autonomous tool loans.
- Native `npc_move_to` travels from ship to actual room/panel position and back through the dock. A four-metre room/proximity check and ten-second dwell gate the call. Completion requires native-call acknowledgement, the requested native station effect, actual deployment and the same actor back in a ship room.
- Per-operation persisted tokens, request checks, station reservation, callback cancellation, safe tool returns and ship-destruction cleanup. A direct order remains higher priority; an ashore actor waits for a restored docking link rather than being teleported.
- Future successful foreign-trader patrol arrivals pay 8,000 Cr; own traders stay unpaid. Payment tracing records promised/actual credits and exact before/after balances. General receipts share the existing cross-mod cursor; no duplicate UI or financial rows are added.

## Actual interface and remaining uncertainty

Native X4 9.00 `ego_targetmonitor/targetmonitor.lua` declares `ControlPanelInfo`, `GetControlPanelInfo` and `GetControlPanelRequiredWares`; `ego_detailmonitor/menu_userquestion.lua` calls `StartControlPanelHack(UIComponentSlot, paneltypeid)`. The function has **no NPC actor parameter**. The implemented bridge invokes the same player-attributed native action only after the existing crew actor reaches the actual panel. Whether remote invocation away from the player is accepted, and whether it affects the player animation/control state, must be checked in the game. It is not represented as a verified NPC-only engine API.

Native room searches/control-panel properties, `npc_move_to`, interaction-point transforms, post-location restoration and actor tools are evidenced by the published native scripts and command metadata. No generic whole-station `set_object_hacked`, fake timer effect, tool creation or periodic payment stands in for a panel action.

This environment has no X4 executable, matching installed XSDs, live station interiors, game save or effective mod load order. Physical security-office traversal, off-screen native NPC transit, remote panel invocation/costs, captain return/control, hostile docking, default/one-shot UI registration, save/load interruption and actual new payouts are **runtime-unverified**. Missing geometry/path/API is visible waiting/failure, not a claimed completed hack. If the ship undocks while its captain is ashore, autonomous redocking may be impossible; restore the docking link in game. This limitation is not hidden by spawning a captain or teleporting crew.

## Validation performed

- Static XML, documented command attributes, custom/native script parameters, localisation, icons, order registration and correctly nested ZIP/source parity.
- 42 existing source contracts, 8 actual crystal-forwarding XML inventory mocks, 18 hacker source/tool-accounting tests, 32 existing Lua mocks and 30 hacker menu/native-bridge mocks.
- All seven repository extensions audited for manifests, XML, documented command attributes, references and source/ZIP parity; runtime verification is explicitly false.
- CI checks Lua 5.1 and LuaJIT syntax and runs the mocks. None simulates the X4 engine or proves an in-game success.

The [runtime checklist](TESTING.md) gives reproducible acceptance tests. Existing mod sources outside Galactic Occupations are unchanged. The installable bundle includes Builders 1.75, Kopis/Astrid 1.15 and Yaki Habitats 1.23 unchanged.
