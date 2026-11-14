# X4 spacesuit/boarding incident — 14 November 2026

Source: user-supplied `debug(20261114-041309).log` (83,572 lines, 8.8 MiB), session starts 11:20:57 on November 14; analysis of the supplied file, not proof of native physical player state.
Static repository baseline before this update: Galactic Occupations 0.5.5 (UI script `vgo_spacesuit.lua` is inert, MD `VGO_Spacesuit.xml` clears only saved v46 pending requests).

## Observations

- `[=ERROR=]` records: 18,860.
- Around 12,192 missing-asset/load errors refer to `extensions/uncf_ameaterasu` (including ship, engine, shield and weapon macros), while `uncf_ameaterasu_steamgg` is installed. Likely missing/incomplete asset dependency. Do **not** invent placeholder macros or simply remove save-critical ship references.
- 2,795 instances of `md.Personal_Envoy_Full_Crew.EnsurePermanentCrew: Property lookup failed: $PilotActor`. An installed third-party crew script is repeatedly dereferencing an unavailable variable. The source was not available for an exact safe compatibility diff. This is not a Galactic Occupations cue.
- 507 `order.assign.commander` "commander is unreachable" errors, mostly not attributable to Galactic Occupations from the lines alone.
- 184 insufficient widget/table height errors, commonly exactly 615 available versus 732 required. Test UI scale at about 1.0–1.2 instead of 1.8, and close overlapping windows, before attributing this to a specific mod.
- 66 error pairs in `md.kuertee_chc.ResolveObjectToShipStation` regarding `$kCHC_object.trueowner` and `.toplevelcommander`; 65 missing `$MinTriggerTime` in `md.FactionLogic.XenonFactionLogic_KhaakCrisis.CheckConditions`; mission-ID and several other independent errors remain.
- `Personal_Envoy_Full_Crew`, `escape_teleport`, `kuertee_transporter_teleport`, `improvedspacesuit`, and `x4_rdnk_spacesuit` appear installed. The log does not identify the actual transition or lock on the player. The lack of a matching VGO player-movement diagnostic is **not** conclusive proof of which other mod or engine feature caused it.
- Missing `.sig` signature warnings on unpacked mods are generally expected and are not evidence of missing gameplay assets. Save-preview XML errors using `maxsize=0x1000` alone do not establish save corruption.
- No recorded `md.kuertee_emergent_missions.Bounties_UpdateLastKnown` errors in this file; not a reason to remove the previous compatibility guard.

## Changes in Galactic Occupations 0.5.6

The older 0.5.3 player safety rollback is retained: no menu confirmation interception, no delayed automatic teleport/eject, and no global recurring input changes.

New manual escape and recovery are added to the owned-ship Interact context menu:

1. `Emergency EVA (outside hull)`: only when actually aboard the selected owned **undocked** ship, not in a suit, conversation or transit. Uses X4 9.00 `teleport_player_to_spacesuit` with `emergency=true`, `instant=true`, `allowinhighway=false`. Native description says emergency placement is outside the current object's bounding box. A conventional exit can instead use an XS docking launch; this is intended as an explicit alternative in problematic ship geometry.
2. `Rescue: board this ship`: only when in a real spacesuit, targeting an owned ship in the same sector within **2km**, not in conversation or transit. Invokes `teleport_player object=$Target instant=true force=true control=false` to the native ship interior. `force=true` bypasses teleport research only for this explicitly requested nearby recovery. Does not create ships, alter docking requests or move any NPCs.
3. One-shot, two-second delayed native `unlock_all_flight_input` and `unlock_all_shooting_input` after manual rescue, not an always-on override. No player movement from observer/legacy cues.

The existing English and 12 translated X4 language tables all include labels and tooltips, now 64 IDs each. Save-safe: cue names retained; no crew, property, jobs, orders, fares or missions reset.

## How to test in X4 9.00

1. Exit X4; back up the save, then install the full 0.5.6 extension ZIP. Load the existing save. The XML/schema/Lua mock tests are not native game tests.
2. From an **undocked** owned ship interior, select that ship on the Map and right-click it. Use **Emergency EVA (outside hull)**. The player should appear outside the ship's bounding volume and regain suit flight inputs. Check whether the suit HUD and camera appear.
3. Within 2km of the same owned ship while in the suit, right-click the ship and use **Rescue: board this ship**. The player should arrive in the ship interior with walking controls, without being forced into the cockpit or automatic relaunch.
4. Also use the ordinary **Use Spacesuit** and **Shift+D** boarding via the XS airlock, plus a ship/station transporter and normal docking. Neither ordinary route is intercepted.
5. Restart and repeat after saving. In the next debug log look for `VGO manual EVA:`, `VGO manual board:`, `VGO manual transition:`. If there are no messages after actual clicks, inspect Interact menu load and UI event dispatch. These markers denote **requests**, not native success.
6. If control lock persists: test in a copy of the save with `escape_teleport` and `kuertee_transporter_teleport` temporarily disabled **one at a time**, with their documented disabling procedures. Then test `improvedspacesuit` / `x4_rdnk_spacesuit`. Confirm whether `kuertee_transporter_teleport` is configured to remove the Map Teleport option; it does so by default. Do not remove mods from a production save without a rollback backup.
7. Independently, repair or disable the broken `personal_envoy_auto` crew script based on its actual source and restore the `uncf_ameaterasu` assets required by active content. Those require their original mod distributions, not arbitrary replacements.

## Confidence

The code and menu tests confirm only a *bounded, explicit, schema-shaped* fallback. Without running the installed X4 binary and checking physics/control ownership in the saved game, this update **cannot guarantee that the engine transfers the avatar outside the hull or that all controls are restored**. That limitation is deliberate; the previous speculative automatic rescue was unsafe.
