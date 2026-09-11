# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-11 — native WNG backstories validated on branch

## Public implementation state

Public mod `main` remains:

**`b242dc72d139910172e8de3290530b505fcfa823` — Quiet Lattice human-form society.**

Native backstories are branch-only at this checkpoint.

## Active branch

**`rebuild/native-backstories-20260911`**

Validated clean branch HEAD:

**`c28562be20c441bd1587fe78125cfef503a78356` — `rebuild: wire native WNG backstories to current roles`**

Validated clean tree:

**`04727e84ed76927eb760b50d15ccddc473ffc343`**

The branch contains no temporary validation workflow in the final tree.

## What this pass implemented

Added:
- `Defs/BackstoryDefs/Backstories_WNG.xml` — a substantial native current-schema WNG backstory pool.

Wired current PawnKinds:
- all Wraith Hunter / Warrior / Commander / Keeper / Queen / Player Wraith roles;
- Asuran Operative / Technician / Commander / Infiltrator;
- Quiet Lattice generalist / engineer / soldier / coordinator;
- player human-form Replicator;
- exact Replicator Queen.

Current backstory categories now distinguish:
- Wraith origin;
- Wraith Hunter / Warrior / Commander / Keeper / Queen / player adulthood;
- synthetic/Asuran origin;
- hostile Asuran operative;
- synthetic engineer / soldier / coordinator;
- infiltrator;
- Quiet Lattice;
- player/independent human-form Replicator.

Identity layers remain separate: xenotype/race, PawnKind/caste-role, faction, and biography/backstory are not collapsed.

## Historical / schema reconciliation

Historical `Backstories_WNG.xml` was used only as requirement/reference evidence.

A concrete incompatibility was found and corrected: historical backstories used dictionary-style skill XML such as `<Melee>2</Melee>`, while current RimWorld 1.6 `BackstoryDef.skillGains` is a `List<SkillGain>`. The rebuilt file uses current list entries with `<skill>` and `<amount>`.

Every WNG backstory sets `requiresSpawnCategory=true`, preventing WNG-specific biographies from leaking into unrelated pawn generation.

Wraith origin text was tightened against Stargate lore: it describes Hive-raised life, living technology, feeding, culling, dormancy and Queen hierarchy without claiming detailed canonical childhood institutions that the series never establishes.

Synthetic backstories are grounded in Asuran/Replicator pattern construction, reconstruction, collective/base-code knowledge, divergence, technical roles and impersonation while distinguishing WNG extrapolations such as Quiet Lattice society from canon-named factions.

## Validation

GitHub Actions run:

**`34608137484` — SUCCESS**

Validated:
- XML patch wiring applied to all required current PawnKinds;
- Release C# build passed;
- all Def/Patch XML parsed;
- current RimWorld 1.6 list-style `SkillGain` schema used;
- no legacy dictionary-style skill entries remain;
- at least 25 WNG BackstoryDefs present;
- all required Wraith/synthetic role categories present;
- every WNG backstory requires its WNG spawn category;
- every targeted current PawnKind has the expected childhood/adulthood `backstoryFiltersOverride`.

This is **source/Def validation, not live RimWorld validation**.

## Exact next steps

1. Recheck public `main` is still `b242dc72...`.
2. Promote clean validated tree `04727e84...` to public `main` as one clean commit with no temporary workflow history.
3. Verify public diff contains only the backstory Def and four current PawnKind files.
4. Update `CURRENT_PUBLIC_STATE.md` and this checkpoint to the exact promoted SHA.
5. Move to the next reconciled debt: **richer block Grav adaptation + broader AntiShield integration**, after checking current Replicator adaptation source, shield/grav dependencies, recovered history and Stargate behavior.

---

# PRIOR PUBLIC MILESTONES

- Temporary Asuran lattice intrusion: `26680fe84b95a0bfd5a23841b714fdba9cde1a98`.
- Recurring exact-map Queen recovery: `9ce713704505a220d357f8a6f234fb6e040e0b2e`.
- Captured Queen sovereign consequences: `0b8150f3ff6ca7138482ba9a604847f5967fc48b`.
- Neural Interface / exact reconstruction: `8495b846c7dd31c079db6d4f007be490df3247f3`.
- Infiltration conceal/reveal: `c7a9b46a3bef9393301d153e3f56c3c44c7ce95c`.
- Covert visitor impersonation: `87da0e524324190584ac31e1830265db76688fae`.
- Quiet Lattice human-form society: `b242dc72d139910172e8de3290530b505fcfa823`.

All promoted milestones were source/Def validated before public promotion; broad live RimWorld validation remains outstanding.
