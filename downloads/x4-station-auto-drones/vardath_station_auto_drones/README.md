# Vardath – Automatic Station Drones and Managers v1.02

Automatic, no-toggle X4: Foundations 9.00 extension. Works with existing saves and new construction, applying requirements to **all player-owned stations every in-game minute**. Does not modify any other Vardath extension.

| Station | Cargo drones | Defence | Repair | Build |
| --- | ---: | ---: | ---: | ---: |
| Normal | 90% | 5% | 5% | 0% |
| Wharf or shipyard | 60% | 5% | 5% | 30% |

The percentages represent *shared drone/unit storage capacity*, NOT freight ware storage. The game rounds to whole drones. It does **not** spawn free drones: it sets the supply requirements shown in Logical Overview. The station must have enough funds/resources and access to supply to restock. Existing drones are preserved, so physical inventory may temporarily differ from target distribution. If a required category has no available compatible drone macro, the mod reports a diagnostic rather than silently claiming success.

**Managers:** once the first dock or pier is actually built and operational, create a player-owned manager if the manager post is vacant. Existing managers are never replaced. If a manager is dismissed, a new one is assigned on a subsequent pass.

## Fixes in v1.02
- Fixed **player blackboard calls** to use X4's Lua component ID rather than a 64-bit UniverseID. This was inconsistent with working X4 MD-to-Lua bridges and could suppress every station update.
- Fixed **requirements versus physical drone count**: percentages now set the intended Logical Overview auto requirements EVEN when the station's existing drone pool is full or unbalanced. No drones are destroyed, and the game cannot add replacements until actual slots become available.
- Accepts X4's alternate `ID: 12345` component reference format.
- Retains readback verification; if X4 rejects a requirement below already stored units, the mod reports the discrepancy instead of hiding it.

## Earlier fixes since v1.00

- One Mission Director-to-Lua event per galaxy-wide station roster, instead of potentially losing a burst of per-station events.
- Uses the supported player blackboard to transfer complete rosters.
- Adds an acknowledgement and explicit errors for inaccessible Lua, zero-capacity stations, missing drone macros, FFI failures and mismatched post-write requirements.
- Preserves unrelated supply orders (including missile overrides), existing drones and both automatic/manual quantity semantics.
- Reads the modified supply orders back from the engine to verify them; static success alone is not treated as proof.

## Installation / upgrade

1. Delete or replace the old **`vardath_station_auto_drones`** folder (do not install two copies).
2. Extract `vardath_station_auto_drones_TEST.zip` into the game's `extensions` directory. The installed file must be `extensions/vardath_station_auto_drones/content.xml`.
3. Enable the extension and fully restart X4. Load your existing save and allow at least two **in-game minutes** for the periodic scan.
4. Check Logical Overview on an existing station and then a wharf/shipyard.

If the UI/Lua bridge is not responding, an in-game notification appears after repeated unanswered sweeps. If an engine update fails, an error notification appears and the debug log explains which operation failed. Search the X4 debug log for **`[Vardath Auto Drones]`** or **`[VAD]`**. This is particularly relevant if **Protected UI Mode** is preventing a custom Lua module from loading. X4 9.00 has different Lua UI conditions depending on mod setup; do not change Protected UI Mode unless the diagnostic indicates a failure, and restart X4 after any change.

**Testing:** GitHub packaging, source checks and XML validation are automated. Full in-game execution cannot be verified remotely. Keep a backup save for this version.
