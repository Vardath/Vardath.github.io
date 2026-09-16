# WNG Master Plan Append — D096/D097 Reconciliation Update + Third Asuran Statue Variant

Date: **2026-09-16**  
Design authority: **Vardath**  
Status: **ACTIVE CONTINUITY + NEWEST DESIGN AUTHORITY FOR THE ASURAN STATUE BRANCH.**

This append updates `MASTER_PLAN_APPEND_2026-09-16_LATE_REBUILD_RECONCILIATION_AND_ASURAN_STATUES.md` after another continuity review of the recent WNG conversation history and local rebuild state. Newest explicit Vardath instructions override older wording.

## 1. Reconciliation result

The recent D075–D097 conversation sequence was checked against the WNG continuity record and website planning layer. The important gameplay ideas from that sequence are represented durably rather than being left only in chat:

- Royalty-backed caste-sensitive Wraith telepathy;
- implant-like exact-pawn Iratus attachment, dangerous removal and later Anomaly study;
- ordinary-animal holding-platform containment and trace comparative xenobiology research;
- Queen / Sovereign Neural Lattice deployment of ten controlled Replicator Drones with deliberate feral release;
- Child’s Toy matter-consumption reproduction and irreversible Go Feral command;
- Goa’uld shuttle ONAC liquid-fuel integration with Chemfuel fallback when ONAC is absent;
- Kassa as nutritious addictive crop, harder derivatives and persistent repeat-customer demand;
- Wraith enzyme pharmacology, Roshna, Nish’ta, first-generation Hoffan treatment, Iratus-derived pharmacology and Iratus Queen restoration;
- Wraith retroviral humanisation/suppression, hybrid stabilisation, and high-risk feeding-independence therapy;
- Michael’s `Whispers` hybrid as blind, sound-hunting, fog-emitting experimental Wraith biology, with biopsy/research and derived hearing/mist technology;
- Tretonin/tritonin remains ONAC-owned and must not be duplicated by WNG.

Where older appends still call these ideas “future” or “planned,” the implemented local checkpoint history takes precedence.

## 2. D095 branch conflict is resolved

The earlier reconciliation correctly preserved two valid parallel D095 branches:

1. **Hybrid Stabilisation** — finite adjunct protection against relapse while Wraith retroviral humanisation/suppression is active; not a cure.
2. **Wraith Feeding Independence** — risky gene therapy that removes only `WNG_LifeForceMetabolism`, restores ordinary eating and forfeits Life-Force-powered feeding/regeneration while leaving the pawn otherwise Wraith.

That merge obligation is no longer pending.

**D096 merged both branches into one mainline tree.** Future work must retain both systems; no session should resurrect the earlier either/or conflict.

## 3. D097 status — first two Asuran statue traps are implemented

The first two statue concepts are no longer plan-only.

### 3.1 Awakening Asuran lattice sculpture

Implemented behavior:
- Asuran-source trade object rather than generic colony art;
- hidden save-persistent absolute timer rolled once between **5 and 60 in-game days**;
- moving/minifying/trading the exact statue does not reroll the deadline;
- once installed/spawned after the deadline, the physical statue is replaced by a hostile human-form Asuran / Replicator pawn.

### 3.2 Dark-feeder Asuran shadow sculpture

Implemented behavior:
- never transforms into a pawn;
- hidden **5–20 day** cycle advances only in sufficiently low light;
- light pauses progress;
- when mature it chooses a bounded nearby living flesh pawn, consumes that pawn/corpse as matter, leaves existing Asuran nanite slurry/residue, remains a statue and rolls another cycle;
- deliberate use in a dark prison or captive pen as a nanite-slurry source is an intended gameplay possibility, not an accidental exploit.

These two objects remain mechanically distinct.

## 4. NEW — third Asuran trade statue: Replicator reliquary

Vardath adds a third Asuran-made trap-statue variant.

### Required behavior

- It belongs to the same Asuran trade/artifact family as the other trap statues and must not be craftable through an ordinary generic sculpture bill.
- The exact physical statue receives a hidden, save-persistent transformation deadline rolled once between **5 and 60 in-game days**.
- Moving, minifying, storing, buying, selling or reinstalling the exact statue must not reroll that deadline.
- When the deadline expires and the statue is installed/spawned, the statue **breaks apart into five real Replicators**.
- First implementation target is five ordinary `WNG_ReplicatorDrone` pawns, not proxy effects and not five unrelated incidents.
- The spawned Replicators are hostile autonomous Replicators, using the existing Replicator faction/domain grammar rather than player-controlled drones.
- They should emerge at/around the statue’s actual map cell, with transactional placement/rollback safeguards where practical.
- The statue itself is consumed by the transformation.

### Explicit separation from the other variants

The Replicator reliquary:
- does **not** awaken as an Asuran human form;
- does **not** eat prisoners or manufacture nanite slurry over time;
- produces exactly **five Replicators** when it breaks down;
- uses its own 5–60 day timer/state.

The three Asuran trap-statue identities are therefore:

1. **Sleeper / awakening statue** → one hostile human-form Asuran after 5–60 days.
2. **Dark-feeder statue** → periodically consumes nearby flesh in darkness after 5–20 days and leaves nanite slurry, while remaining a statue.
3. **Replicator reliquary statue** → breaks apart into five hostile Replicator Drones after 5–60 days.

## 5. Provenance and trade rules

All three trap statues are intended to feel like attractive Asuran artifacts rather than obvious weapons.

- Asuran-only provenance is required. Ordinary factions should not gain generic manufacture rights merely because they have Art skill.
- Asuran trade/supply channels are the normal acquisition route.
- A later dedicated player-controlled Asuran fabrication interaction may be added, but it must verify appropriate Asuran ownership/biology/technology rather than exposing a universal sculpture recipe.
- Hidden timers must survive save/load and object movement.
- Trader rarity/value remain balance parameters rather than fixed lore facts.

## 6. Still-open late branches preserved by this reconciliation

The following ideas remain approved but are not displaced by the statue work:

- Reol recognition/memory manipulation, once the biological source/acquisition branch is coherent;
- symbiote poison, after ONAC/RimGate ownership and compatibility checks;
- broader Wraith diplomacy, client settlements and Queen/Hive favour;
- richer Ideology reactions, including potential consequences for deliberately feeding prisoners to a dark-feeder statue;
- Michael/Whispers laboratory sites and richer specimen encounters;
- later safer refinements of Hoffan treatment and Wraith feeding-independence therapy;
- further Comparative Xenobiology drugs, implants and organic–synthetic medicine where the source biology is explicit.

## 7. Continuity rule reaffirmed

Every new WNG gameplay idea introduced in chat must be written into durable continuity and the master-plan layer even when implementation is deferred. Once implemented, its status must be updated rather than left described as merely planned.

Static/API-reference validation remains evidence only; no checkpoint should be called compiled, Def-loaded, save-tested or live-playtested until RimWorld itself proves it.