# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-11 — native WNG backstories promoted to public

## Public implementation state

Public mod `main` is now:

**`45e62cd7f5ea18d2cf3f57df8b25beda1aabe1ad` — `rebuild: add native WNG backstories`**

Promotion used validated clean tree `04727e84ed76927eb760b50d15ccddc473ffc343` with parent `b242dc72...`, so temporary branch validation tooling did not enter public `main`.

Public diff contains only:
- `Defs/BackstoryDefs/Backstories_WNG.xml`;
- `PawnKinds_Wraith.xml` backstory-filter wiring;
- `PawnKinds_Asuran.xml` backstory-filter wiring;
- `PawnKinds_HumanFormSocieties.xml` backstory-filter wiring;
- `PawnKinds_ReplicatorQueen.xml` backstory-filter wiring.

## What is now public

- native current-schema WNG BackstoryDefs for Wraith and human-form synthetic identities;
- Wraith shared Hive origins plus Hunter / Warrior / Commander / Keeper / Queen / Player adulthood pools;
- synthetic/Asuran origins plus hostile Operative / Engineer / Soldier / Coordinator / Infiltrator / Quiet-Lattice / Player adulthood pools;
- every WNG backstory uses `requiresSpawnCategory=true`;
- each current PawnKind is wired through `backstoryFiltersOverride`, preserving race/xenotype, faction, PawnKind-role and biography as separate identity layers;
- exact Replicator Queen uses current synthetic-origin/player-independent categories without changing her exact age/story control systems.

## Reconciliation corrections

Historical `Backstories_WNG.xml` was not copied wholesale. It used obsolete dictionary-style skill XML. Current RimWorld 1.6 `BackstoryDef.skillGains` is `List<SkillGain>`, so the rebuilt public Def uses current `<li><skill>...<amount>...` entries.

Wraith biographies were tightened against Stargate lore to avoid asserting unseen detailed childhood institutions. Synthetic biographies distinguish canon-grounded Asuran/Replicator pattern/base-code/reconstruction concepts from WNG-created Quiet Lattice society roles.

## Validation

GitHub Actions run **`34608137484` — SUCCESS**:
- Release C# build passed;
- all Def/Patch XML parsed;
- current SkillGain schema passed;
- 25+ WNG BackstoryDefs present;
- all required Wraith/synthetic categories present;
- all WNG backstories require WNG spawn categories;
- all targeted current PawnKinds have expected childhood/adulthood filters.

This is source/Def validation, **not live RimWorld validation**.

`CURRENT_PUBLIC_STATE.md` is updated to exact public HEAD `45e62cd...` and removes native backstories from missing debt.

## Exact next pass

**Richer block Replicator Grav adaptation + broader AntiShield integration.**

Before implementation:
1. inspect actual current public Replicator state/adaptation/effect code and current shield/grav systems;
2. inspect recovered plan/history for intended evidence-learning and effect boundaries;
3. perform Stargate lore gate — do not turn “Grav” into generic telekinesis and do not confuse Replicator adaptation with ARG disruption;
4. map against native RimWorld/Odyssey movement/grav/shield mechanics and current WNG shield implementations;
5. preserve existing saved adaptation evidence/state and overlays;
6. implement only concrete real-system interactions and record unresolved external shield dependencies explicitly;
7. validate, checkpoint, then promote cleanly.

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

All were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
