# Occupation review — 0.2.3

Reviewed against debug(4).log, the current extension, published native X4 9.00 AI scripts and native interface/property documentation. There is no installed X4 executable/save available to run the repaired scripts here. The user reports that 0.2.2 boards actual passengers successfully; departure, the complete tour and final unloading are not yet demonstrated.

The new log directly reports an invalid `.count` after the boolean cargo illegality result, attempted materialisation of construction pseudo-entries, and a missing `order_vgo_tour` icon. Tour/patrol causes were additionally found in native control flow: move.generic does not undock the ship; order.fight.escort expects matching owners, creates AssignCommander orders for foreign escorts and can cancel its caller's default order. Those are concrete interface/semantic mismatches, not XML syntax errors.

| Occupation | Review / implemented repair | Still needs gameplay proof |
|---|---|---|
| Escort | Replaced the same-faction fleet escort call with a persistent commercial convoy contract and movement helper. Protection uses a separately queued temporary native Attack order, not a borrowed order script. Actual destination/proximity/duration gates still control the fee/reputation. | Cross-sector following, threat interception, return to the contract, one completed-arrival fee. |
| Taxi | Shared pickup/boarding retained. Explicit departure now covers same-sector destinations too. Drop-off requires the same accepted actors to be observed outside the ship in the real destination station context. | Complete pickup, departure, docking, all passengers leaving, one fare and saved partial unloading. |
| Scanner | Every surface-travel path now explicitly undocks; actual surface/LOS checks and native per-component scan verification remain. | Scan data changes on real loaded modules; no OOS physical scan claim. |
| Mapper | Shared approach now undocks. Real destination-set catalogue and guarded native/fallback transit are retained. | Actual anomaly destination data/traversal, gate distinctions, failed transit recovery. |
| Luxury tour | Successful boarding now selects the first real sight immediately. Approach explicitly undocks before reporting proximity success. Sites can serve several tour ships while each ship retains its own unique-site history. Final fare requires the booked itinerary AND all passengers disembarking. | Ten-site travel, dwell/progress, actual full unload and one booked luxury fare. |
| Crystal miner | Shared undocking fixes leaving docks and broker stops. Physical persistence uses the actual asteroid/crystal parent, never its sector. Existing real-deposit targeting, turret preflight and real-drop collection remain. | Deposit targeting/hits, harvested drop events, native collection and sale remain UNVERIFIED. |
| Lure | Shared departure; added a forward-laser requirement before trying the native shoot_at provocation. Pursuit/range/survival checks remain. | Real provocation, observed pursuit and retreat to defences. |
| Demolition | Shared departure and corrected physical persistence target; still requires actual destruction and times out ineffective fire. | Real destructible asteroids, suitable guns/arcs and actual debris collection. |
| Morale | Shared departure. Crew template skills, real observed improvements, limits and faction/target cooldowns retained. | Actual crew skill changes and corresponding reputation. |
| Inspection | Shared departure. Cargo/inventory `.illegalto` is consumed as a boolean, matching native property types. No neutral hostility is created by selection. | Timed proximity checks, legal/illegal examples, report/reputation under real jurisdiction. |
| Recruitment | Shared departure; ownership is verified before changing the captured ship's commander/orders. Float divisors retain morale/crew influence in the probability. Existing hull/equipment remain. | Protected exclusions, surrender probability, crew allegiance, target damage/equipment preservation. |
| Trade route patrol | Uses the same persistent real-trader convoy routine; no same-faction fleet escort subcall. Own temporary attacks are bounded and the original route is resumed. | Foreign/player traders, real corridor movement and interception, continued occupation after a threat ends. |

## Both passenger services

The same batch of at most ten actual cue actors is retained across pickup, travel and drop-off, bounded by free crew berths. Taxi travels directly to its destination; a tour first satisfies its booked distinct sites/sectors. Neither job can finish merely because docking occurred or a timer expired.

When visible, passengers receive native npc_move_to instructions to walk into the destination dock room. Stopped walks are retried; a walking actor is not constantly redirected. A passenger is counted only after current/persisted real room-context evidence proves it left the ship at the destination. The ship's passenger template is then removed, and the mission actor is cleaned up on the station. Other crew/templates are untouched. The whole manifest must have left before the delivery flag/fare can be armed.

Off-screen unloading attempts a supported transfer of the SAME cue actor to a real destination room with add_actor_to_room. This is an explicit custom equivalent to streamed walking, not a timer or new passenger. It checks the action result and actual station/outside-ship context before counting arrival. Failure retains the manifest and tries to restore the actor to a ship room where possible; no fare is awarded for failure. Room availability/streaming and NPC pathfinding still require in-game verification. If no valid room can be connected, it waits rather than inventing completion. Pickup uses the inverse verified same-actor room transfer outside rendered simulation, with actual ship context and native out-of-transit checks. Its existing visible walking branch is retained. Both alternatives need runtime confirmation in unloaded scenes.

## Default orders and preservation

No code forces an intentionally chosen Hold order back to an occupation. Reassign jobs already lost in earlier builds. New versioned root/default recovery keeps passenger manifests, itinerary progress, ownership, crew, equipment, native turret settings and unrelated queued orders. Temporary defensive Attack orders are separately identified; cleanup cancels only a still matching mod-created override, never an unrelated player order or the occupation default.

The pilot-seat guard is retained. Native documentation describes occupiedship as the pilot-seat ship; mere passenger presence was not established as a defect, and this update does not claim otherwise.

## Habitat and UI errors

Constructionplanentrydata is pseudo data. Native code reads `$CurrentPlan.{$index}.macro` directly, rather than assigning `$CurrentPlan.{$index}` to an entry variable. Yaki Habitats 1.23 follows that pattern and refuses expansion if any macro cannot be read. Existing station modules are not removed or moved. New icon aliases use native base-game order textures for the twelve new IDs. Existing icons/screens are not replaced; Protected UI remains enabled and the removed income panel is not restored.

Native sources inspected include the published 9.00 order.fight.escort.xml, order.fight.attack.object.xml, move.generic.xml, move.undock.xml and libraries/icons.xml at https://github.com/ArtByunex/x4-foundation-artbyunex/tree/e3e8a345e5624db118bff3eb171b60b0993fcc2c. The available native scriptproperties.xml and factionlogic_economy.xml also document/exemplify boolean illegality and direct construction macro access. No full native game implementation is redistributed.

Twenty-eight source constraints and thirty-one mocked Lua checks complement XML/API/reference/package checks. They do not execute X4 or demonstrate gameplay success. The log's partial save-header preview parse messages do not, by themselves, establish corrupted saves. No save file is edited by this update.
