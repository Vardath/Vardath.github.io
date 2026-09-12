# WNG — Replicator Queen / Asuran recovery / controller design

Author/final design authority: **Vardath**.

This is a working first-build design contract, not an implementation checkpoint and not immutable canon. Vardath may alter any detail after testing.

**Implementation status must be determined from current public `Vardath/Wraith-Nanite-Gravtech-1.6` source. Do not use this document to decide that a feature is absent or to choose a “next pass.” The master plan and active corrections define the target.**

# Queen identity

Current exact Queen design:
- one unique human-form Replicator individual;
- female;
- age 13 in the current first-build design;
- `WNG_NaniteHumanoid` physical identity;
- unique innate sovereignty belongs only to that exact pawn;
- one exact pawn/state persists through storyline and capture;
- ordinary Asuran roles remain separate and do not gain Queen authority merely by sharing nanite physiology.

# Vault and release contract

Required behavior:
- neutral precursor-style Queen-vault world site;
- exact Queen physically held in a real vanilla `CryptosleepCasket` or equivalent real cryptosleep chamber;
- only the dormant exact Queen becoming physically spawned/released on the real vault map triggers her release state;
- she joins the player immediately on release/spawn;
- later map transitions cannot replay release or reset the first recovery sequence;
- synthetic Queen should not retain inappropriate ordinary cryptosleep-sickness residue.

Discovery timing must remain suitable for short campaigns and author-tunable. Never restore the old hard-coded day-84 schedule.

# First Asuran recovery/capture contract

The intended physical recovery flow is:
1. exact Queen is released;
2. a bounded, tunable recovery delay begins;
3. the recovery team arrives physically rather than teleporting beside her;
4. the intended first recovery team is an all-or-nothing four-operative Asuran/Lattice group unless Vardath changes the design;
5. recovery operatives use nonlethal subdual/carry/load behavior;
6. the same exact Queen pawn is physically carried to the real recovery craft;
7. she is transferred into that exact carrier/transporter;
8. stun/down/carry/load are **not capture**;
9. only the exact hostile carrier actually leaving the map with the exact Queen still aboard commits capture;
10. failed/interrupted departure leaves the same pawn recoverable/player-owned;
11. successful capture preserves exact pawn identity and faction/story state rather than creating a proxy Queen.

Counts, delays, ranges and similar balance values remain author-tunable.

# Recurring Queen recovery contract

Later recovery attempts:
- may target any player map physically containing the exact Queen;
- must not target a different player map while she is elsewhere, caravaning, off-map, dead or already captured;
- use real entry/raid/recovery behavior rather than teleporting beside her;
- retain the same physical subdual/carry/carrier-departure capture boundary;
- cadence remains tunable and non-spammy.

# Controller authority model

Block Replicator controller identity is a real state layer separate from faction alone.

Required authority classes are:
- autonomous / `None`;
- exact Queen authority;
- Sovereign Neural Lattice authority;
- Temporary Asuran intrusion;
- captured-retained-Queen remote sovereign access where the current implementation uses that consequence.

Same faction does not imply same controller domain.

A controlled block remains the same physical hierarchy/adaptation/matter pawn. Do not replace real control with a proxy pawn, outbreak count, abstract faction buff or fake mechanitor ownership.

Different controller domains must not casually recombine, coordinate, repair or share retaliation merely because their faction matches.

# Exact Queen authority

Required semantics:
- exact living WNG block targets;
- exact Queen reference plus persistent domain identity;
- pre-control faction/authority state preserved where needed for valid restoration;
- real faction/control transfer rather than descriptive flags only;
- authority validity tied to appropriate physical presence such as same map or same caravan unless current design changes;
- Queen EMP, block EMP and active containment can interfere;
- dedicated move/attack/Repairer/Burrower/recombine/release control surface where appropriate;
- upward recombination retains real hierarchy requirements;
- split/recombine conserves exact Queen domain, adaptations and stored matter;
- Queen human-form Nanite Reserve remains separate from block stored matter.

Ranges/caps are tunable design data. Do not treat older numeric values as immutable doctrine.

# Sovereign Neural Lattice authority

The **Sovereign Neural Lattice is a WNG-specific Stargate-derived extrapolation**, not a claim of a canon-named Stargate device.

Design purpose:
- physical implant/item giving a non-Queen bearer bounded, target-specific block-Replicator control;
- bearer is **not a Queen**;
- exact Queen should not create a second overlapping implant domain over innate Queen authority;
- authority type remains distinct from Queen and Temporary Asuran control;
- physical fabrication/progression should require actual Replicator/Asuran knowledge and materials;
- native surgery/install/remove mechanics should be used where faithful;
- removal returns/releases the physical implant/control domain where applicable;
- exact bearer reference/domain persists through save/load;
- EMP/containment remain real counterplay;
- split/recombine preserves exact implant domain;
- cross-domain merge/repair/coordination/retaliation remains prohibited.

Acquisition range, cap and EMP disruption duration remain author-tunable.

# Temporary Asuran lattice intrusion

This is a third distinct authority model, not Queen authority and not Neural-Lattice authority.

Required semantics:
- use `ReplicatorControlAuthority.TemporaryAsuran` or equivalent distinct current authority identity;
- temporary hijack only;
- ordinary Asuran rank/physiology does not confer permanent sovereignty;
- snapshot/preserve the exact prior authority/controller/domain/faction state;
- expiry/interruption restores that exact prior state rather than merely releasing everything to autonomous control;
- duration/range/cap/trigger behavior remains author-tunable;
- EMP/containment are real counterplay;
- split/recombine during the intrusion must preserve coherent temporary state plus restoration metadata;
- no cross-domain duplication/leakage.

# Captured-Queen sovereign consequences

Successful Asuran retention of the exact Queen must have a real consequence, not an arbitrary `+1 outbreak` or generic faction buff.

Intended consequence:
- suitable later Asuran/Lattice threats may gain genuine sovereign access to physical block Replicators while the faction retains the exact captured Queen;
- use real controller/domain state and mixed physical human-form + block threat composition;
- never create duplicate/proxy Queen state;
- if the Queen is recovered/lost/dead or sovereignty validity otherwise ends, consequences must follow actual state rather than a permanent ungrounded flag.

# Infiltration and Neural Interface relationship

The broader human-form branch must connect coherently to Queen/controller systems without collapsing identities.

Planned/current-design capabilities include:
- human-looking infiltration and reveal mechanics;
- recruit/imprison/enslave/copy/create-human-form Neural Interface operations where game/DLC rules permit;
- exact copied-person biography/name/skills/passions/XP/appearance/genome continuity where required;
- real resource costs and no free duplication loop;
- Quiet Lattice/player human-form variants where the master plan requires them;
- mixed human-form + block threats where appropriate.

Whether each item is already implemented must always be checked against current public source.

# Save/load and exact-identity rules

State that matters must survive correctly:
- exact Queen pawn identity;
- vault/release state;
- recovery/capture state;
- Queen/implant/temporary controller domains;
- prior state needed for temporary override restoration;
- split/recombine controller inheritance;
- exact captured/recovered Queen consequences.

At-most-once transactions must remain at-most-once through reload. No duplicate Queen, duplicate capture, duplicate restoration or double resource spending.

# Validation boundary

Compile/XML/API checks establish source sanity only. Live RimWorld behavior remains the final authority for gameplay behavior, save/load, UI, AI, transport/capture and balance.

Do not create checkpoint files or pass logs to track this design. Reconcile actual public source against the master plan when continuing work.
