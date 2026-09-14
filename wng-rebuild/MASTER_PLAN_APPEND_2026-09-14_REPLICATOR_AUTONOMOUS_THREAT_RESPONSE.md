# WNG MASTER PLAN APPEND — AUTONOMOUS REPLICATOR THREAT RESPONSE / AI PRIORITY

Date: **2026-09-14**  
Author/final design authority: **Vardath**

## STATUS — ACTIVE WNGv1 IMPLEMENTATION DECISION

Active implementation remains `/mnt/data/WNGv1/Wraith-Nanite-Gravtech`.

## Autonomous blocks are matter-focused, not ordinary pawn-hunting raiders

The clean autonomous block Replicator AI must not use unconditional generic enemy acquisition as its normal high-priority behavior.

Current accepted priority for ordinary uncontrolled block forms is:

1. immediate bounded self-defense against a real recent aggressor;
2. bounded same-faction swarm retaliation for only a subset of nearby Replicators;
3. environmental matter/technology assimilation;
4. lower-priority Lord/incident duty where one actually exists;
5. wandering/idle fallback.

This preserves the intended machine-ecosystem identity: Replicators are dangerous because they consume and reproduce, while still defending themselves and responding locally when attacked.

## Current first-build response tuning

Historical later-build evidence is retained provisionally:

- direct self-defense memory: **900 ticks**;
- local swarm alert: **1,800 ticks**;
- responder chance: **24%**;
- response radius: **40 cells**.

These remain tunable, not immutable canon.

## EMP interaction

A Replicator currently disrupted through the shared native-EMP-backed interference state does not initiate or answer WNG threat-response jobs. No separate threat-response EMP timer is allowed.

## Save persistence

Personal recent-aggressor state and map-level retaliation alerts are save-persistent. The map-level response must use a real RimWorld `MapComponent` rather than an unsaved static dictionary.

Current WNGv1 only has autonomous same-faction block swarms, so map alerts are faction-scoped. When exact Queen/Lattice/controller domains are rebuilt, domain identity must tighten the existing alert compatibility rules rather than creating a second retaliation system.

## Rejected behavior

Do not restore an unconditional `JobGiver_AIFightEnemies` above assimilation for autonomous blocks. Do not make every nearby Replicator dogpile an aggressor. Do not let an ordinary hostile Lord duty silently outrank the consume-first behavior unless Vardath explicitly changes that design.

## Validation boundary

Static/API validation may verify ThinkTree priority, bounded deterministic responder selection, EMP suppression, and Scribe state. Live RimWorld combat/assimilation/raid/save behavior remains a separate required test.