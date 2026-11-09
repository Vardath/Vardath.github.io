# Compatibility review — 1.0.1, 10 November 2026

Input: `debug(20261109-150118).log`, **15,061,244 bytes, 75,369 lines**, SHA-256 `84f0a4fa7f1fa72ab3c85d61ad2afe059f11a0e0590f1ec14fb5b46e49699c80`. It records Occupations 0.4.7, Compatibility 1.0.0 and X4 9.00. There are **2,306 error-tag occurrences**, including repeated diagnostics and three successful drone updates logged through an error logger. Exact fatal/exception/access-violation/out-of-memory/crash-dump signatures were not found. “Exceptional” in equipment names is not an exception stack.

## Newly corrected boundaries

| Logged error | Count | Source-confirmed correction |
|---|---:|---|
| `MC_Management.Thread_Manager_Cleanup`, missing `$Submissions.{2}` | 1 | The native loop counts the original list, then invokes cleanup synchronously. That callback can shrink the list before the next index is read. Clone a work list, use a private counter instead of the callbacks' `$i`, skip unavailable cues and remove only the added temporary variables. Native reward actions and other cleanup actions remain unchanged. |
| `inventorycollector`, undefined `$debugchance` | 23 | The collector declares no such local but installs native common handlers. Add a guarded zero default at init and start/search loop entries, including already-running saved contexts. Retain existing explicit values. The log does not identify which included handler emitted line 131; this initializes the missing shared-handler input. Collection, blacklist, visits and deposit code remain unchanged. |
| `HeadHunterMD.WatcherExpire`, null pilot/tracking fields | 3 | Expire orphaned watchers safely and remove flags only from a real pilot when present. Preserve expiry diagnostics when its pilot/timestamp exists. The bounty/death watcher is unchanged; no reward is replayed. |
| Emergent Missions, late rescue `End2` signal | 3 | Add the waiting-state guard already used by other branches in the author's source, and tolerate a listener consumed before same-frame deferred delivery. Do not reset cleanup or grant rescue credit. |

Original 1.0.0 guards remain. The earlier incompatible-ammo, null academy/HQ actor, mismatched trade-pair and wrong invasion-exit signatures do not recur in this file. This is evidence for this recording, not proof of universal correctness. The new mission index error is a different failure from the two previously guarded callbacks.

## Sources and checks

The actual author Workshop catalogs were inspected, with their embedded MD5 verified:

- Inventory Collector `ws_2063916598`, folder `fs_inv`, **1.25**, 2026-03-06.
- Head Hunter `ws_2992233767`, folder `chillheadhunter`, **2.08**, 2026-10-30.
- Emergent Missions `ws_3627916728`, folder `kuertee_emergent_missions`, **9.02**, 2026-10-13.
- Native 9.00 and the six original sources retain the pinned references in `TESTING.md`.

`tools/sources.json` records immutable URLs, catalog MD5 and normalized-LF SHA-256. Thirteen references are checked. All nine diffs validate against native diff grammar and all **29 operations** apply to one expected node each. Fifteen contracts cover missing objects, preserved original logic, synchronous list mutation, late callbacks, optional upstream fixes and exact multi-entry Workshop CAT/DAT extraction. ZIP members and bytes match source. No full native-game or merged-installed-schema execution is claimed.

## Live acceptance

1. Resume Inventory Collector through searching, collecting, depositing and save/load. The missing debug variable must stop recurring; inventory and collection rules must remain unchanged.
2. Finish/abort a native multi-part mission. Cleanup must handle multiple submissions when callbacks remove entries. Ordinary rewards occur once; failed chains acquire no reward. Test save/load and late callbacks.
3. Let a HeadHunter-tracked enemy die, lose its pilot or be captured. An orphaned watcher must close without null-property/removal errors. Valid bounties retain the original death handling. Keep Protected UI: this patch does **not** unblock the unsupported Lua import.
4. End/abort an Emergent Missions rescue and allow late docking/undocking updates. The named cleanup warning should not recur; rescues and rewards still require actual native completion.
5. Retest the original six boundaries using `TESTING.md`: compatible/incompatible ammo, real captain/HQ eligibility, same-ware trades and faction defence.

## Other findings

The file records **623 balance-matched occupation payments**: 418 crystal sales (26,504,000 Cr), 198 tours (967,500,000 Cr), and seven patrol payments (56,000 Cr), totalling **994,060,000 Cr**. Ship/invoice or ship/service/contract identities are unique within each family. These prove those recorded changes, not every occupation or the new capital transport code.

The station scanner's one inactive-physics surface call is corrected in **Occupations 0.4.8**. The original Hyperion story repair belongs to **Hyperion Ascendant 1.0.0** and follows the actual modded network, including relocation out of a sector without a real scan gate. The latest file has no new Hyperion stack; the user's confirmed symptom, earlier cache failures and the sector mod's changed connections informed that recovery.

Still unresolved: 21 missing Koha engine candidates; 62 ShipGenerator requests without candidates; 59 unrelated failed/multiple selectors; external ware/character/construction-plan data; 334 truncated save-header metadata messages; stale UI queries without caller stacks; and HeadHunter's Protected UI import. These require the actual merged data/caller or save state for safe repairs. Signature diagnostics alone are not a proven crash cause. No essential mod is removed and no arbitrary UI import is whitelisted.
