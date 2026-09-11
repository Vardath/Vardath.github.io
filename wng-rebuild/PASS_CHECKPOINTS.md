# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Wraith evidence-to-research bridge reconciled

## Public state

Public mod `main` remains **`9f45ebf18caacde671f015cdd1a25217eebb6838` — Replicator evidence-analysis bridge**.

No Wraith progression code was changed in this reconciliation pass.

## Exact evidence object

Use the existing **`WNG_WraithHiveHeart`** as the first Wraith living-technology evidence object.

Why this is the correct bridge:
- every generated `WNG_WraithMatureHive` already requires and spawns one exact Hive Heart before the site is accepted;
- Mature Hive discovery has no WNG research prerequisite, so the Heart genuinely exists before `WNG_WraithLivingTechnology`;
- the Heart is the central living biological population/control system of a mature Hive, making it direct evidence for understanding Wraith-grown machinery;
- a Mature Hive is neutralized by eliminating actual hostile threats, not by requiring Heart destruction, so a player can deliberately preserve the Heart for study;
- no new ruin/site/quest/timed event is required.

Rejected as the first gate:
- `WNG_WraithBioSludge`, because colony production of it is already gated by `WNG_WraithLivingTechnology` and would create circular progression;
- Living Forge/forge implants, because their normal colony acquisition/crafting is also behind the same research;
- shuttle/gravship evidence, because that would unnecessarily couple later flight progression into this short first Wraith bridge.

## Native analysis path

`WNG_WraithHiveHeart` is a 3x3 building, not a haulable item. Odyssey's native analyzable component supports `canStudyInPlace=true`; native `JobDriver_AnalyzeItem` then analyzes the building at its current position rather than trying to haul it to a bench.

Exact first implementation:
- add native `CompProperties_CompAnalyzableUnlockResearch` to `WNG_WraithHiveHeart`;
- use a stable WNG-specific analysis ID distinct from Replicator analysis;
- require one successful in-place analysis;
- do not destroy the Heart on analysis;
- colonist-only analyzer targeting;
- keep all existing Mature-Hive population component/tuning unchanged;
- keep `Fabrication` as the ordinary prerequisite for `WNG_WraithLivingTechnology`;
- additionally require analyzed `WNG_WraithHiveHeart` through native `requiredAnalyzed`;
- add no new incident, site, Quest, fixed-day gate or progression GameComponent;
- do not change Wraith shuttles, gravships, Growth Chamber power, strategic hunger, feeding ecology or retaliation.

Resulting chain: **Mature Hive discovery -> neutralize/preserve Hive Heart -> analyze living Hive system in place -> Wraith Living Technology -> colony reconstruction/growth.**

## Exact next short pass

Implement and validate only:
- `Defs/ThingDefs/Wraith_HiveHeart.xml`;
- `Defs/ResearchProjectDefs/Research_WraithBootstrap.xml`.

Validation must prove Release build, all Def/Patch XML, unique WNG analysis ID, `canStudyInPlace=true`, exact `requiredAnalyzed` target, unchanged Mature-Hive population comp settings, and no unrelated file changes. Use explicit cleanup paths or clean-tree reconstruction; never `git add -A` after building.

---

# PUBLIC MILESTONES

- `26680fe84...` — Temporary Asuran lattice intrusion.
- `9ce7137045...` — recurring exact-map Queen recovery.
- `0b8150f3ff...` — captured-Queen sovereign consequences.
- `8495b846c7...` — Neural Interface / exact reconstruction.
- `c7a9b46a3b...` — infiltration conceal/reveal.
- `87da0e5243...` — covert visitor impersonation.
- `b242dc72d1...` — Quiet Lattice society.
- `45e62cd7f5...` — native WNG backstories.
- `12590e8ea8...` — physical Replicator Grav adaptation.
- `b5cde48e3c...` — native energy-shield AntiShield integration.
- `e1a080c938...` — bounded Wraith Growth Chamber.
- `ff4f8dcb7b...` — paused strategic Wraith feeding-request UI.
- `9f45ebf18c...` — Replicator evidence-analysis progression bridge.

Broad live RimWorld validation remains outstanding.
