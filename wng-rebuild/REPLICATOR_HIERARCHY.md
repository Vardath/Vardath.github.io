# WNG — block Replicator physical hierarchy

Author/design authority: **Vardath**.

This file records the clarified physical size/combat hierarchy for the fresh 1.6 rebuild. It is a first-build implementation target and may be tuned later, but the behavior must not be silently omitted.

## What “the other hierarchy” means

Vardath clarified on 2026-09-10 that by the Replicator hierarchy he meant the actual **small-to-large physical Replicator ladder**, its upward recombination, its downward breakup on destruction, and the post-breakup delay that prevents apparently immortal Siege/Titan loops.

Current first-build ladder:

**Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass**

Current first-build upward recombination:
- several Drones combine into a Hunter;
- several Hunters combine into a Bulwark;
- several Bulwarks combine into a Titan;
- several Titans combine into a Siege Mass.

Current first-build downward breakup:
- Siege Mass destroyed -> operational Titans;
- Titan destroyed -> operational Bulwarks;
- Bulwark destroyed -> operational Hunters;
- Hunter destroyed -> operational Drones/base Replicators;
- Drone/base is irreducible.

The currently intended breakup count is two children per destroyed higher form, while the lower-tier upward combination counts can vary by tier. These are tunable Def values rather than permanent code doctrine.

## One-hour post-breakup recombination lockout

The important gameplay rule is that Replicators created by a destruction breakup **cannot immediately recombine upward**.

Current first-build delay: **2,500 ticks, approximately one in-game hour**.

This delay exists to prevent the experience where the player kills a Siege Mass or Titan, it breaks into smaller Replicators, and those children immediately recombine back into the same large threat so that the large unit feels effectively immortal.

The delay:
- applies to the split-born children;
- is save-persistent;
- prevents those children participating in upward recombination until it expires;
- is a gameplay mechanic, not an anti-regression/release rule;
- remains tunable through Def/component data.

## Recombination vs genuine destruction

Upward recombination intentionally consumes the smaller source bodies. That intentional `Vanish`/consumption must **not** trigger their death-breakup logic.

Genuine destruction of a higher body does trigger its configured downward breakup.

Material/adaptation/control state should transfer appropriately through both directions instead of being erased.

## Separate from adaptation/specialist branches

This physical hierarchy is distinct from the Replicator adaptation/specialist system. The fresh rebuild must also account for Controller, Repairer, Burrower, Artillery and adaptation roles including Ranged, Armor, Power, Grav and Shield/anti-shield development. Those branches do not replace the physical Drone-to-Siege ladder.
