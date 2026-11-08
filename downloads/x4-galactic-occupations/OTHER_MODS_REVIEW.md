# Existing X4 mod review — 6 November 2026

Reviewed the source currently in Vardath/Vardath.github.io, plus the separately added Astrid Tours work. This was a code/static/package review, not a running X4 session. No fresh game log was available. No claim is made that an earlier gameplay bug is fixed merely because files parse.

| Extension | Checks and findings |
|---|---|
| Living Factions and Builders | 12 XML files, including 8 diffs; manifest, MD/AI command attributes, referenced custom definitions and package/source identity passed. Native build/faction XPath targets require the installed 9.00 merged data to prove applicability. Existing payment implementation was inspected; no unrelated rewrite made. |
| Yaki Terran Habitats | 18 XML files, including 8 diffs; identity, XML, custom-reference and archive checks passed. Habitat connection geometry and faction population/build use remain runtime questions; unchanged in this update. |
| Kopis Production Cheat | Original 23 XML files parsed and package matched source before changes. The special main-weapon assets, Forge component/macro and weapon-recovery scripts were preserved. Added the separate Astrid Tours yacht, six supporting custom equipment/projectile/hull macros, explicit loadout, local Yaki crew definition and spawn/stop MD cue. |
| Faction Invincible | 2 XML files; manifest, command interfaces, duplicate-name/custom-reference and package checks passed. Its repeating protection effects need runtime confirmation; unchanged. |
| Station Auto Drones | 3 XML files plus Lua; XML and package checks passed. Lua parsed successfully using Lua 5.3's compiler; this is not a LuaJIT 5.1/UI/FFI runtime test. Existing UI event handling remains dependent on the installed game interfaces; unchanged. |
| Universal Cargo Teleport | Both native trade/ware-exchange diff scripts and metadata inspected. XML parses and documented action attributes passed. Patch selectors and actual transfer/trade accounting require the effective installed native scripts and runtime; unchanged. |

The existing five-mod audit returned zero errors and zero warnings before the Astrid addition. A command-interface pass over all locally available existing MD/AI files found no missing required or unknown documented command attributes. These checks cannot resolve every patch against absent 9.00/DLC files, validate every expression, prove UI FFI calls, test geometry, or confirm save/load behavior.

Galactic Occupations adds only its own namespaced AI/MD/order definitions and no vanilla diffs. It does not depend on removed mods or replace Inventory Collector. The initial delivery changed Kopis for the requested independent Astrid Tours copy. The 0.2.0 follow-up also updates Builders to 1.73 for the requested main Transaction Log payment descriptions and earnings section. Its payroll rates/timing and existing contract state remain intact. Its existing normal Astrid maintenance cue remains separate.

Appropriate reputation rewards are implemented for verified custom escort/taxi completion, actual morale improvement, completed commercial-route escort, genuine contraband reports and accounted crystal broker sales. A shared faction cooldown prevents stacking. Sightseeing, discovery, demolition and ownership transfer do not reward mere proximity.

See `vardath_galactic_occupations/TESTING.md` and `../x4-kopis-production-cheat/vardath_kopis_production_cheat/ASTRID_TOURS.md` for reproducible in-game checks and explicit limitations.

## 8 November 2026 — current 0.3.8 follow-up

The dated sections above describe earlier reviews, not the current patch inventory. The full latest log is now reviewed in [LOG_REVIEW_0.3.8.md](vardath_galactic_occupations/LOG_REVIEW_0.3.8.md), including 27 confirmed Occupations errors and other attribution limits. Occupations includes the previously documented narrow native AI/MD and optional-extension attribute diffs; it is no longer accurate to describe its current release as having no vanilla diffs. Only Occupations source changes in this follow-up. Auto Drones 1.02, Cargo Teleport 1.01, Builders 1.75, Kopis/Astrid 1.15 and Yaki Habitats 1.23 retain their published source hashes. All seven packages are re-audited without claiming runtime certification. No third-party source or old save plan is silently removed.

## 8 November 2026 — 0.3.9 crew-return follow-up

Only Occupations source changes. All companion sources retain their 0.3.8 published hashes and are re-audited. The new log confirms physical/off-screen crystal money and identifies eleven Occupations import/parameter/result errors; its other 1,151 error records are separately identified rather than claimed fixed. No third-party source or saved plan was deleted. See [the current report](vardath_galactic_occupations/LOG_REVIEW_0.3.9.md), including the unresolved 0/2 tour boarding wait.
