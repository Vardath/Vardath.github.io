# WNG — refresh memory and continue

Read this before touching the WNG 1.6 repository after any context reset.

# ⛔ THE RECOVERY WORK HAS ALREADY BEEN DONE

The broad WNG conversation/history reconstruction was completed on **2026-09-11** and consolidated into:

**`CANONICAL_RECOVERY_LEDGER.md`**

Do not make Vardath reconstruct the project again. Do not reread weeks of raw chat by default. Recover from the canonical ledger plus the actual current public repository state.

Retrieve older raw WNG chat only when:
- the canonical ledger explicitly flags an unresolved historical conflict/gap;
- current public repo evidence conflicts with the ledger; or
- Vardath explicitly asks for raw-history review.

When a raw-history issue is resolved, update the ledger so it never has to be solved again.

## Identity and authority

- Mod: **Wraith & Nanite Gravtech (WNG)** for RimWorld 1.6.
- Author/final design authority: **Vardath**.
- Active code repository: public `Vardath/Wraith-Nanite-Gravtech-1.6`.
- Durable continuity: `Vardath/Vardath.github.io/wng-rebuild/`.
- Private/old WNG repositories/builds are historical/reference evidence only unless Vardath explicitly re-authorizes them.
- There are **no known-good historical WNG builds**.

## Mandatory recovery order

1. Read `STANDING_RULES.md`.
2. Read **all of `CANONICAL_RECOVERY_LEDGER.md`**.
3. Read `WNG_IMPLEMENTATION_CHECKLIST.md`.
4. Fetch current public `main` and compare its HEAD/state to the ledger snapshot.
5. If `main` advanced, inspect the actual commits/files and update the ledger before relying on its current-state section.
6. Read only the active subsystem contract/master-plan append(s) needed for the genuine next slice.
7. Read `PLAN_EXECUTION_PROTOCOL.md` and implement through the checklist.
8. After the batch, update the canonical ledger before handoff.

`NEXT_GPT_PRIMER.md` is only a short pointer/snapshot. It never outranks the ledger or current `main`.

## Mandatory implementation order

**CANONICAL LEDGER -> STARGATE LORE -> CURRENT PUBLIC STATE -> ACTIVE CONTRACTS -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> UPDATE LEDGER/HANDOFF**

Do not code from memory or a stale assistant summary.

## Stargate-first rule

WNG is a Stargate mod. Before every implementation/addition/rebuild/correction, establish:
- what the feature actually is in Stargate;
- what it actually does, including limitations/scale/ownership;
- what Vardath's current decision is in the ledger/current conversation;
- what current public WNG already implements;
- what native RimWorld/Odyssey/Biotech already provides;
- what any optional Stargate integration owns;
- and only then the best faithful RimWorld implementation.

If it has become generic sci-fi rather than recognisably Stargate, redesign before coding.

## Critical state rules

- **Current public `main` is implementation state.** Old next-step/checkpoint prose can be stale.
- `next`, `unfinished`, `reconcile`, `correct`, `refine`, or `rebuild` never means delete a required existing feature.
- **Al'kesh is required and currently implemented; do not remove it.**
- Do not invent a Goa'uld uranium/chemfuel fallback or any other unspecified substitute.
- Supplied ONAC/RimGate/Stargates source identities recorded in the ledger/contracts are authoritative for optional integrations.
- Use **Wraith Grav Engine**, not obsolete Wraith Gravcore.
- Ordinary Wraith Drain Life, strategic faction hunger, Mature-Hive feeding ecology and Mature-Hive retaliation are separate systems.
- CatCraft owns Stargate network/dial/iris/receive mechanics; WNG integrates around them rather than replacing them.
- No replacement/generated art unless Vardath explicitly asks.

## Current public snapshot at creation of the canonical ledger

Current verified mod HEAD recorded by the ledger:

**`4af4f60c184f1971ee7bc7516b63e3b33142fea0` — `cleanup: remove temporary Wraith stunner validation workflow`**

This is only a checkpoint. **Fetch `main` every time.**

The fresh public rebuild has already advanced far beyond the old “Replicator foundation only” stage. The canonical ledger records current implemented Wraith, Replicator, shuttle, ring, Wraith/Asuran gravship and integration state, plus required unfinished human-form/Queen and Ha'tak branches.

## Handoff maintenance

Before ending any meaningful work batch, update `CANONICAL_RECOVERY_LEDGER.md` with:
- exact new public HEAD;
- what actually changed;
- implemented / unfinished-dependency / changed-by-Vardath / live-test-needed status;
- any newly superseded decision;
- the next genuinely unfinished slice derived from current `main`.

This update is part of completing the work. The objective is that Vardath can say **“refresh memory and continue”** and the next GPT can simply recover and continue without interrogation or reconstruction.
