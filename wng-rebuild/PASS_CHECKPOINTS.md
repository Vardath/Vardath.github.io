# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Wraith Growth Chamber validated on branch

## Public state

Public mod `main` remains:

**`b5cde48e3cbcb2d608edabc78758e5fe9e4aec39` — native energy-shield AntiShield integration.**

Growth Chamber remains branch-only at this checkpoint.

## Active branch

**`rebuild/wraith-growth-chamber-20260912`**

Validated clean branch HEAD:

**`6bbb804a81b06159a33729b877412859a6b7e60c` — `rebuild: bind Growth Chamber to Mature Hive demographic cap`**

Clean compare against public contains exactly four intended files:
- `Defs/ThingDefs/Wraith_GrowthChamber.xml` — added;
- `Defs/ThingDefs/Wraith_HiveHeart.xml` — description reconciled;
- `Source/WNG/Wraith/WraithGrowthChamber.cs` — added;
- `Source/WNG/Wraith/WraithMatureHive.cs` — bounded replacement-registration API added.

Temporary workflow/helper files are absent from clean branch HEAD.

## Implemented behavior

- `WNG_WraithGrowthChamber` is a real ticker building using ordinary RimWorld electrical power plus `CompRefuelable` restricted to `WNG_WraithBioSludge`;
- first-build Def tuning is centralized: 60,000-tick cycle, 60 bio-sludge per completed replacement, 0.35 Queen Life Force cost, 4,000W draw, 45% Hunter / 55% Warrior weighting, five-cell release search;
- chamber only operates beside an initialized same-map/same-faction Mature Hive Heart;
- chamber reads exact `FoundingPopulationCap` and `LivingDemographicCount` and resets growth progress at the cap rather than pre-growing expansion beyond it;
- exact local operational same-faction `WNG_WraithQueen` is required as genetic source;
- Queen Life Force must be available before a cycle may progress/complete;
- output is strictly `WNG_WraithHunter` or `WNG_WraithWarrior`;
- Hive Heart API independently rejects non-Hunter/Warrior registrations, duplicate pawns, wrong faction/map, non-Wraith or over-cap replacements;
- replacement pawn is generated/spawned/validated and registered into the exact Hive demographic list **before** bio-sludge and Queen Life Force are committed;
- failed generation/spawn/registration destroys the attempted pawn and commits no biomass/Queen cost;
- successful replacement joins the active Queen's existing Lord when available;
- progress and block reason are save-persistent;
- chamber does not interact with strategic faction hunger, ordinary feeding, Feeding Niche captive identity, Dormancy Vault reserve or mature-Hive retaliation.

## Mature-Hive site integration boundary

The chamber is **deliberately not yet inserted into generated hostile Mature Hive infrastructure**.

Reason: current generated Mature Hive sites have no grounded Wraith electrical-power source. Adding a 4,000W required chamber there today would create guaranteed inert infrastructure or force this pass to invent/restore a separate Wraith power-generator subsystem. That would violate the bounded Growth Chamber pass and the recovered requirement not to invent fake ZPM/Gravcore substitutes.

Therefore generated-site placement remains an explicit dependency on the later Wraith ground-power/bioelectric-energy reconciliation. The chamber itself is mechanically complete enough to function wherever a valid initialized Heart, Queen, power grid and bio-sludge supply genuinely exist.

## Validation

Initial validation wrapper run **`34612309236` failed before GitHub created a job**. This was a workflow-wrapper failure, not source/Def validation.

Because the same wrapper class had already occurred during AntiShield, the validation method was changed rather than retried unchanged: patch and invariant logic were moved into small temporary helper scripts and the workflow was reduced to a minimal runner.

Corrected run:

**`34612430265` — SUCCESS**

Passed:
- mature-Hive API patch application;
- Release C# build;
- all Def/Patch XML parsing;
- Growth Chamber / Heart population-cap invariants;
- Queen / Hunter / Warrior / Life Force / bio-sludge / power requirements;
- explicit no-Keeper clone invariant;
- explicit no-inert generated-site chamber invariant while no Wraith ground-power source exists;
- temporary workflow and helper scripts removed before clean branch HEAD.

This remains **source/Def validation, not live RimWorld validation**.

## Exact next pass

**Promotion-only pass:**
1. recheck public `main` remains `b5cde48...`;
2. promote clean tree `24114e331f752afdb607d98402cdd6c6ef75bd82` as one public commit without temporary validation history;
3. verify public diff is exactly the four intended files;
4. update `CURRENT_PUBLIC_STATE.md` and this checkpoint to exact promoted SHA;
5. remove Growth Chamber core behavior from missing-required debt but retain generated-Mature-Hive chamber placement as an explicit Wraith ground-power dependency;
6. only then reconcile the next required Wraith slice.

---

# PREVIOUS RECONCILIATION DECISION

Growth Chamber is a RimWorld-scale abstraction of the Wraith cloning-facility function from SGA `Spoils of War`: Queen-derived genetics, very high biomass/energy demand, and warrior production. WNG deliberately bounds that behavior to Hunter/Warrior demographic replacement up to an initialized Hive Heart's recorded founding population ceiling.

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

All completed public milestones were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
