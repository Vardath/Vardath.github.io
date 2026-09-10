# WNG block Replicator foundation checkpoint — 2026-09-10

Author/final design authority: **Vardath**.

Implementation repository: `Vardath/Wraith-Nanite-Gravtech-1.6`

Verified implementation head before this checkpoint: `cba1f4febb32a7297ee62e7edfbe12846134c9c9`.

This checkpoint supplements `REPLICATOR_FEATURE_MAP.md`. Newer explicit Vardath instructions always override it.

## Verification

A temporary public GitHub Actions workflow was used only to verify the newly written implementation, then removed.

Final verification result before removal:
- RimWorld 1.6 C# assembly build: **SUCCESS**
- Def XML syntax parse: **SUCCESS**

The temporary workflow itself has been deleted; no permanent release-lock/audit bureaucracy was retained.

## Implemented in the fresh rebuild

- Physical hierarchy: Drone -> Hunter -> Bulwark -> Titan -> Siege Mass.
- Genuine-death breakup reverses the hierarchy so larger forms break down instead of disappearing.
- Intentional upward recombination does not trigger death splitting.
- Split-born children inherit state and receive the tunable ~2,500-tick / ~1 in-game hour recombination lockout. The reason is combat playability: killing Titan/Siege Mass must not instantly recreate the same threat and make combat effectively impossible.
- Learned adaptation state is cumulative rather than one-value-at-a-time and migrates the earlier fresh-save field where present.
- State transfer through split/recombine includes adaptation knowledge/evidence and stored replication matter. Matter is summed upward and divided among genuine-death split children rather than duplicated or lost.
- Assimilation targets useful technology/material preferentially and converts consumed material into a matter budget.
- Autonomous offspring growth spends matter and is bounded by a Def-tunable map population ceiling.
- Dangerous Replicator Matter can reassemble into hostile Drones, also respecting the population ceiling.
- EMP suppression blocks core autonomous systems including assimilation, recombination and regeneration, and specialist/adaptation active functions respect EMP.
- Regeneration is implemented; learned Power adaptation improves it through Def-tunable values.
- Armor adaptation reduces incoming non-EMP damage.
- Shield adaptation provides a rechargeable defensive pool.
- Ranged adaptation provides learned autonomous ranged fire distinct from the innate Artillery specialist role.
- Shield countermeasure evidence is separate from merely learning Shield; repeated shield evidence is required before AntiShield state is learned. Full interaction with later non-Replicator shield systems remains a dependency.
- All retained adaptation overlay graphics (Armor, Ranged, Power, Grav, Shield) are now connected to learned state and render when present.
- Controller behavior coordinates nearby same-faction autonomous Replicators onto a shared hostile focus.
- Repairer behavior seeks damaged same-faction Replicators and repairs them.
- Burrower behavior breaches hostile structures. Further tactical prioritisation of containment/path blockers is still being refined within the block foundation.
- Artillery has a real ranged support attack with Def-tunable range, warmup, damage and penetration.
- Autonomous faction combat roster now includes Drone, Hunter, Bulwark, Controller, Repairer, Burrower, Artillery, Titan and Siege Mass.
- Player-owned Replicators do not autonomously assimilate player assets and do not silently perform autonomous hostile-style recombination.
- Child's Toy is implemented as a player-owned mech branch. If it remains feral/outside valid player mech control for its tunable delay, it physically transforms into an ordinary hostile `WNG_ReplicatorDrone`; the replacement is spawned before the Toy is consumed so a failed transformation cannot silently delete it.
- A powered Replicator containment projector is implemented. Its field prevents hostile assimilation/recombination and freezes dangerous Matter reassembly while powered. Construction/research/power/radius values remain tunable.

## Explicitly unfinished dependencies — not forgotten

- **Grav adaptation gameplay effect:** learned state and retained overlay are implemented, but the real movement/grav effect must bind to WNG's actual later gravtech mechanics. Do not invent an unrelated placeholder buff.
- **Full anti-shield/countermeasure integration:** learning/evidence state exists, but interactions with later concrete WNG/other shield systems must be implemented once those systems are present.
- **Queen sovereign control domain:** later exact 13-year-old female human-form Replicator Queen from the recovery quest must provide genuine sovereign control/access over block Replicators. This cannot be faked as a modifier.
- **Asuran sovereign capture consequence:** Asurans physically carrying the Queen off-map is the only committed capture. Once captured, appropriate later Asuran threats gain genuine sovereign access to block Replicators.
- **Queen capture raids:** while the recruited Queen is physically present on any player map, Asurans may occasionally raid specifically to capture her. This is a later Queen/Asuran subsystem dependency, not part of autonomous block AI.
- **Mixed block + human-form raids:** remain planned for the later Asuran/human-form layer.
- **Broader player sovereign/control commands:** the block foundation currently prevents unsafe autonomous behavior; richer deliberate player control over block hierarchy/specialists belongs with the later sovereign/control layer.

## Immediate next work inside the Replicator foundation

Before moving to Wraith, continue refining tactical Burrower/containment behavior and do one more relationship-level reconciliation of the block foundation against `MASTER_PLAN.md`, `CORRECTIONS_LOG.md`, retained assets and current public source. Only after every remaining block feature is either implemented or explicitly dependency-recorded should the rebuild proceed to the next subsystem.
