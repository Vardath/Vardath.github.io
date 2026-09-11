# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Wraith Growth Chamber promoted to public

## Public state

Public mod `main` is now:

**`e1a080c93893ff5742f5aa91bc00fd7ecc1699f7` — `rebuild: add bounded Wraith Growth Chamber`**

Promotion used clean validated tree `24114e331f752afdb607d98402cdd6c6ef75bd82` with parent `b5cde48...`. Temporary validation/helper history did not enter public `main`.

Public diff is exactly:
- `Defs/ThingDefs/Wraith_GrowthChamber.xml` — added;
- `Defs/ThingDefs/Wraith_HiveHeart.xml` — bounded replacement description reconciled;
- `Source/WNG/Wraith/WraithGrowthChamber.cs` — added;
- `Source/WNG/Wraith/WraithMatureHive.cs` — exact bounded replacement-registration API added.

## Public behavior now

- real powered Wraith Growth Chamber with Def-tunable cycle timing, bio-sludge biomass, Queen Life Force cost and Hunter/Warrior weighting;
- only links to initialized same-faction Mature Hive Heart;
- reads exact founding population cap/current living demographic count;
- cannot exceed the recorded cap;
- requires a living operational same-faction Wraith Queen;
- only Hunter/Warrior replacement output;
- exact replacement pawn is validated and registered into the Heart demographic list before biomass/Queen cost is committed;
- failed generation/registration consumes no cycle resources;
- no coupling to ordinary feeding, strategic hunger, Feeding Niche exact captives, Dormancy Vault reserve or retaliation.

## Explicit retained dependency

Generated hostile Mature Hive sites do **not** yet receive the chamber because current generated Hives have no grounded Wraith electrical-power source. Adding guaranteed inert 4,000W infrastructure, inventing a fake ZPM or restoring Gravcore was rejected. Generated-site placement waits for explicit Wraith ground-power/bioelectric-energy reconciliation.

## Validation / consequence-mirror process correction

Initial temporary workflow run **`34612309236`** failed before a job existed. This was another workflow-wrapper failure, not a source failure.

Because that failure class had already occurred during AntiShield, it was treated as a repeated process defect under the Consequence Mirror rule rather than retried unchanged. Patch/invariant logic was moved into small helper scripts and the workflow reduced to a minimal runner.

Corrected validation run **`34612430265` — SUCCESS**:
- Release C# build passed;
- all Def/Patch XML parsed;
- Growth Chamber/Heart cap, Queen, Hunter/Warrior, Life Force, bio-sludge and power invariants passed;
- explicit no-Keeper clone invariant passed;
- explicit no-inert generated-site chamber invariant passed;
- temporary validation files were removed before promoted tree.

This remains **source/Def validation, not live RimWorld validation**.

`CURRENT_PUBLIC_STATE.md` is updated to exact public HEAD `e1a080c...` and removes Growth Chamber core behavior from missing-required debt while retaining the generated-site power dependency.

## Exact next pass

**Strategic Wraith hunger involved-Wraith count/names UI reconciliation only.**

1. inspect current strategic-hunger state/request UI code and exact faction ownership;
2. recover the intended two-stage decision flow from history;
3. first modal remains feeding-stock/subject decision only — never a Wraith selector;
4. second stage shows count/names of the actual involved Wraiths;
5. decision sequence remains paused until completed;
6. ordinary Drain Life, local Mature-Hive feeding stock and retaliation remain fully separate;
7. inspect native RimWorld window/dialog APIs and checkpoint the exact UI/data-flow before implementation.

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

All completed public milestones were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
