# WNG rebuild — short primer for the next GPT

Snapshot date: **2026-09-11**  
Author/design authority: **Vardath**

# DO NOT USE THIS FILE AS THE PROJECT MEMORY

The one-time WNG history reconstruction is stored in:

**`CANONICAL_RECOVERY_LEDGER.md`**

The current mutable implementation state is stored in:

**`CURRENT_PUBLIC_STATE.md`**

The ledger preserves the recovered project history. `CURRENT_PUBLIC_STATE.md` prevents its original implementation snapshot from being mistaken for the live repo state. This primer is only the entry pointer.

## Mandatory recovery sequence

1. Read `STANDING_RULES.md`.
2. Read **all of `CANONICAL_RECOVERY_LEDGER.md`**.
3. Read **all of `CURRENT_PUBLIC_STATE.md`**.
4. Read `WNG_IMPLEMENTATION_CHECKLIST.md`.
5. Fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main`.
6. Compare current HEAD/state to `CURRENT_PUBLIC_STATE.md`; if the repo advanced, inspect the actual commits/files before coding and update the state file.
7. Read the active subsystem contract/plan append needed for the genuine next slice.
8. Continue implementation through `PLAN_EXECUTION_PROTOCOL.md`.
9. Update `CURRENT_PUBLIC_STATE.md` before ending the batch.

Do not reread weeks of raw WNG chat by default. Retrieve raw history only for a genuine ledger gap/conflict, repo-vs-ledger contradiction, or explicit Vardath request.

## Current repository authority

Implementation: public `Vardath/Wraith-Nanite-Gravtech-1.6` `main`.

Continuity: public `Vardath/Vardath.github.io/wng-rebuild/`.

Private/old WNG repos/builds: reference evidence only unless Vardath explicitly re-authorizes them.

There are **no known-good historical WNG builds**.

## Current public implementation checkpoint

Read `CURRENT_PUBLIC_STATE.md` for the maintained SHA. At this update its verified mod HEAD is:

**`ef04575fb88ed6300b7c681c32971eec0c98d253` — `feat: add System Lord Death Glider strikes`**

The canonical ledger's original `4af4f60...` checkpoint is historical state only. Always fetch `main`.

## Current broad implementation state

Present in the fresh public source/Defs:
- block Replicator hierarchy/specialists/adaptations/matter/containment/Child's Toy foundations;
- Wraith xenotype/castes, four Wraith factions, Life Force/feeding, strategic faction hunger, Mature-Hive ecology/retaliation, captivity/rescue and living-tech bootstrap;
- Wraith Dart culling/native retreat/exact captive persistence;
- Wraith stun staff;
- complete native Odyssey shuttle stacks for Dart, Wraith scout/strike craft, Wraith cruiser, Puddle Jumper and **Al'kesh**;
- verified CatCraft/ONAC/RimGate optional-integration identities;
- Goa'uld transport rings;
- Wraith and Asuran Odyssey-native gravship families;
- family-isolated power/fuel networking;
- Asuran Nanite Reserve/fabrication/workshop foundations;
- **Ha'tak Odyssey gravship family**, including pel'tac, ONAC liquid-Naquadria tanks/pipes, thrusters, power, shield, field projector and heavy plasma battery;
- **real Death Glider fighter/carrier relationship** using native shuttle + native gravship carriage rather than a decorative bay;
- **exact System-Lord/Jaffa Death Glider strike** using verified external factions/crew and real native withdrawal.

Major required unfinished branches currently recorded:
- human-form Replicator/Asuran infiltration + Neural Interface + exact Queen + sovereign/capture layer;
- mixed human-form/block raid integration tied to that layer;
- real hostile Ha'tak carrier/site encounter physically staging/deploying its Death Gliders;
- true cross-map/orbital Ha'tak bombardment distinct from the on-map heavy plasma battery;
- safe standalone Goa'uld craft/gravship resource/research route when ONAC is absent;
- final deliberate Ancient/Puddle Jumper power/fuel abstraction;
- professional final art/audio/directional-connection audit;
- broad live-game validation of the fresh current build.

## Critical reminders

- **WNG is a Stargate mod. Lore/function check before every implementation.**
- **Al'kesh exists and stays.** Rebuild/refine never means remove it.
- Ha'tak is now implemented as a real Odyssey gravship family; do not regress it because the old ledger snapshot predates those commits.
- Death Gliders are real native shuttle fighters physically carried by Ha'tak substructure, not decorative hangar tokens.
- Do not invent uranium/chemfuel or another unspecified Goa'uld fallback.
- ONAC supplied source uses `ONAC_Naquadah` and `ONAC_LiquidNaquadria`; exact IDs are recorded in the ledger/contracts.
- CatCraft owns Stargate network/dial/iris/receive behavior; WNG integrates around it.
- Ordinary Wraith Drain Life, strategic Wraith faction hunger, Mature-Hive feeding ecology and Mature-Hive retaliation are separate systems.
- Use **Wraith Grav Engine**, not obsolete Wraith Gravcore.
- No replacement/generated art unless Vardath asks.
- Current public state beats stale `next step` prose.

## Handoff rule

Do not create another independent giant primer. Maintain the historical ledger and the live `CURRENT_PUBLIC_STATE.md` so the next GPT can recover from settled history + actual current implementation state without making Vardath repeat anything.
