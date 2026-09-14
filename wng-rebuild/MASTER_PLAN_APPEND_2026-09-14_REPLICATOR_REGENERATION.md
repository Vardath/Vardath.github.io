# WNG MASTER PLAN APPEND — BLOCK REPLICATOR SELF-REGENERATION

Date: **2026-09-14**  
Author/final design authority: **Vardath**

## STATUS — ACTIVE WNGv1 IMPLEMENTATION DECISION

Active implementation remains `/mnt/data/WNGv1/Wraith-Nanite-Gravtech`.

## Base self-repair contract

Block Replicator self-regeneration is separate from the future Repairer specialist's ally-healing role.

Current first-build base tuning, recovered from later historical implementation evidence and retained provisionally:
- repair interval: **600 ticks**;
- repair amount: **0.20 injury severity per pulse**;
- target: the most severe non-permanent `Hediff_Injury` on the same pawn.

The base self-repair does not reconstruct missing parts and does not heal allies.

## EMP integration

Do not create a regeneration-specific EMP clock. Regeneration queries the shared WNG Replicator interference state backed by real native RimWorld EMP handling. If a repair pulse becomes due while the pawn is disrupted, that pulse is skipped.

Skipped pulses do not accumulate for catch-up healing later; the next repair interval is scheduled before the EMP/injury check.

## Power adaptation seam

Historical evidence increased regeneration speed/strength after Power adaptation. WNGv1 deliberately does **not** embed those adaptation multipliers until the learned-adaptation system is rebuilt.

When Power adaptation is implemented, it should modify the existing regeneration interval/heal seam rather than creating a second self-repair component.

## Validation boundary

Static/API validation may verify the component uses native `Hediff_Injury.Heal`, ignores permanent injuries, scribes its next-pulse timer, and queries the shared EMP utility. Live RimWorld injury healing, save/reload and balance remain separate required tests.