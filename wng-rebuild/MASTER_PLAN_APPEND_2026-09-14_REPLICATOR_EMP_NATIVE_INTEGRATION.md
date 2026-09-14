# WNG MASTER PLAN APPEND — REPLICATOR EMP NATIVE INTEGRATION

Date: **2026-09-14**  
Author/final design authority: **Vardath**

## STATUS — ACTIVE WNGv1 IMPLEMENTATION DECISION

The active implementation remains:

`/mnt/data/WNGv1/Wraith-Nanite-Gravtech`

This append records how block Replicator EMP disruption is to be implemented in the clean WNGv1 rebuild.

## Native EMP remains authoritative

RimWorld 1.6 already provides the actual EMP damage/stun system through `DamageDefOf.EMP` and the native `StunHandler`. That native system owns:

- whether an EMP hit is accepted as a stun;
- EMP resistance;
- the native EMP stun duration;
- the native EMP adaptation window;
- save/load persistence of native stun/adaptation state;
- the standard disabled-by-EMP presentation/effect.

WNG must NOT create a second independent EMP stun/resistance/adaptation system for block Replicators.

## WNG-specific interference state

WNG may keep a narrow save-persistent disruption endpoint only so WNG-specific systems can answer a common question: “is this Replicator still disrupted by a real native EMP event?”

The WNG marker must only be extended after the pawn’s native `StunHandler` has actually accepted `DamageDefOf.EMP` and reports an EMP stun. It must not manufacture EMP by calling a second custom damage/stun path.

Current WNG-specific consequences of that native disruption are:

- autonomous environmental assimilation is suppressed;
- upward physical hierarchy recombination is suppressed;
- eligible donors that remain disrupted cannot be used for recombination;
- genuine downward destruction splitting preserves the remaining WNG disruption window so destroying a disrupted large body cannot cleanse the state by producing fresh lower bodies.

Future regeneration, specialist behavior, adaptive functions and controller layers may query the same interference utility when rebuilt, rather than creating separate EMP clocks for each subsystem.

## Transformation continuity

If a genuinely destroyed higher block form splits while its WNG disruption endpoint is still active, split-born children inherit the remaining endpoint. The clean implementation may also use RimWorld’s public `StunFor` API to keep those children physically disabled for the remaining interval.

Do not use reflection to copy RimWorld’s private EMP-adaptation dictionary merely to make hierarchy transformation imitate an internal implementation detail. Native adaptation remains native. If live testing later proves a concrete exploit or broken gameplay caused by adaptation not transferring across a split, solve that demonstrated problem then.

Upward recombination is already prohibited while disrupted, so it cannot be used to cleanse the state.

## Why this differs from old WNG

Older WNG work used a custom `empSuppressionTicks`-style state. The clean rebuild rejects that as the primary EMP mechanic because it duplicates a robust native RimWorld system and risks bypassing native resistance/adaptation behavior.

The clean rule is therefore:

**real EMP first; WNG behavioral consequences second.**

## Validation boundary

Static/API contract validation may verify that WNG only records accepted native EMP disruption and that relevant WNG systems query it. This is not live gameplay proof.

Required live tests when the real RimWorld compile/runtime environment is available include:

- EMP a Drone and verify normal native stun/effect;
- verify assimilation does not begin/continue while disruption applies;
- verify disrupted units do not recombine;
- destroy a disrupted Hunter/Bulwark/Titan/Siege Mass and confirm lower children preserve the remaining interruption rather than immediately acting/recombining;
- save/reload during EMP disruption;
- verify native EMP adaptation/resistance still behaves as RimWorld expects and is not overridden by WNG.

No claim of runtime proof is permitted until those tests are actually performed.