# WNG Master Plan Append — Ring Transport, Goa'uld Fallback, Wraith Stunner

Date: **2026-09-11**  
Author/design authority: **Vardath**

# ⛔ CURRENT-STATE WARNING

This file records the design contract and the implementation snapshot **at the time this append was written**. Its old status/`Next implementation work` wording is **not current-state authority**.

Before acting on anything below:
1. read `CANONICAL_RECOVERY_LEDGER.md`;
2. fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main`;
3. verify whether the named feature already exists and what later commits changed;
4. preserve required existing features.

**`reconcile`, `rebuild`, `correct`, `refine`, `unfinished`, or `next` never means remove an existing required feature. Al'kesh is a required retained feature. Do not invent a uranium/chemfuel or other unspecified Goa'uld fallback.**

Newer explicit Vardath instructions and the canonical ledger override this snapshot.

## Mandatory continuity note

When working on Goa'uld transport/craft or Wraith capture weapons, read this append together with `CANONICAL_RECOVERY_LEDGER.md`, `MASTER_PLAN.md`, `CORRECTIONS_LOG.md`, the current public WNG repository, and the repository contract `Docs/WNG_RING_TRANSPORT_AND_WRAITH_STUNNER_CONTRACT_2026-09-11.md`.

## Goa'uld transport rings

Transport rings are now a required Goa'uld technology layer.

Current design:
- buildable ring platform: `WNG_GoauldTransportRings`;
- use RimWorld's native `CompTransporter` load-assignment/ThingOwner system rather than a fake WNG cargo list;
- may load exact people, animals, mechs and items;
- requires no Stargate dialing/address sequence;
- same-map transport is supported, including transport into sealed internal rooms/vaults/ship compartments;
- cross-map transport is supported between currently loaded maps;
- ring platforms may be built aboard gravships as ordinary carried buildings;
- exact loaded Thing/pawn identity must survive save/load and transport;
- no proxies/copies/deletion are permitted.

### More than two ring platforms

When a loaded sender activates:
- discover every other compatible powered ring platform on every currently loaded map;
- exclude the sender and unavailable/unpowered endpoints;
- present a destination list rather than guessing;
- identify each destination by map label plus ring coordinates;
- sort by map label, then map position;
- include same-map destinations.

This remains the deterministic fallback even if custom endpoint naming is added later.

### First-build transfer safety

- both sender and receiver must be powered and ready;
- outbound loading must be complete;
- receiver must not itself be holding/awaiting an outbound load;
- rematerialization stays within the receiving ring's room/near-ring area so sealed-room use cannot randomly eject cargo outside;
- successful pawn arrival refreshes native teleport position state;
- if a placement becomes impossible, unmoved exact cargo remains in the sender rather than being deleted;
- transport has a Def/comp-tunable recharge delay.

Unloaded world-site transport is explicitly a later exact-pawn/world-object problem and must never be faked through pawn recreation.

## Goa'uld Architect-category fallback correction

Older wording that implied WNG Goa'uld construction must simply disappear whenever ONAC is missing is superseded for **standalone-capable WNG-owned Goa'uld technology**.

Current rule:
- if ONAC is active and exact `ONAC_Architect` exists, WNG-owned Goa'uld buildables belong in the ONAC Architect category;
- if ONAC is absent (whether or not RimGate/CatCraft Stargates! are also absent), standalone-capable Goa'uld WNG buildables appear under WNG instead;
- this includes transport rings immediately and should extend to WNG-owned Goa'uld shuttle/gravship/infrastructure once their standalone resource/research route has been reconciled;
- WNG must not duplicate ONAC-owned factions, resources or systems when ONAC is installed;
- current ONAC liquid Naquadria integration must remain authoritative when ONAC exists;
- removing ONAC `MayRequire` from existing Al'kesh/Ha'tak content must wait until a safe standalone material/fuel/research fallback exists.

**This append does not define that standalone craft fuel/material fallback. Do not invent one.**

## Wraith stun staff

`WNG_WraithStunStaff` is a required ranged Wraith capture weapon.

Design:
- ranged staff/stunner identity;
- intended to incapacitate prey instead of kill it;
- no ordinary projectile health damage on a normal successful hit;
- use RimWorld's native `StunHandler` so native stun resistance/adaptation remains authoritative;
- player-looted examples remain normal usable equipment;
- Hunter, Warrior, Commander and Keeper are current automatic carrier castes;
- Queen and player-Wraith PawnKinds are not automatically forced to spawn with one;
- distinct from Goa'uld staff weapon, zat, Wraith Dart culling beam and Drain Life;
- dedicated Stargate-authentic art/audio remain a later production pass.

## Implementation status at the time of this append

Implemented in public WNG `main` during the 2026-09-11 pass:
- generic ONAC-or-WNG Goa'uld Architect router;
- standalone Goa'uld ring transport research;
- buildable powered ring endpoint;
- native `CompTransporter` loading;
- same-map and cross-currently-loaded-map destination listing;
- exact cargo transfer with room-constrained arrival and no proxy pawn creation;
- save-persistent ring cooldown;
- Wraith stun staff Def/projectile;
- custom non-damaging stun projectile path;
- Hunter/Warrior/Commander/Keeper stunner weapon budgets/tags.

Validation status at that time:
- ring slice compiled and XML/invariant checks passed in temporary Actions run **34543660172**; workflow removed afterwards;
- Wraith stunner initially exposed a C# 9 pattern-syntax mismatch against WNG's C# 8 project and was corrected to C# 8-compatible syntax;
- corrected stunner validation run **34544150092** passed compilation/XML/invariant checks;
- later current-state validation must be determined from current `main`/ledger rather than this old status paragraph.

## Historical next-work snapshot — DO NOT EXECUTE BLINDLY

The following was the next-work list **at the time of this append**. It is preserved as history, not current authority:

1. Confirm final combined validation after the ring power-guard correction and remove the temporary workflow.
2. Reconcile standalone Goa'uld shuttle/gravship resources and research so existing WNG-owned Goa'uld craft can use the ONAC-category/WNG-category fallback without requiring ONAC while also avoiding duplicated ONAC resources when it is present.
3. Extend the generic Goa'uld Architect marker to those standalone-capable shuttle/gravship buildables.
4. Continue the fresh Goa'uld Ha'tak gravship family using Odyssey-native gravship contracts and family-isolated Goa'uld fuel/parts.
5. Treat transport rings as expected internal Ha'tak equipment.
6. Later add authentic ring-rise/transport visuals and sounds and dedicated Wraith stunner graphics/audio without replacing the validated mechanics with decorative-only behavior.

**Current interpretation must come from `CANONICAL_RECOVERY_LEDGER.md` + current public `main`.** At canonical-ledger creation, ring/stunner validation/cleanup had advanced, Al'kesh remained fully implemented and ONAC-gated, no safe standalone Al'kesh/Ha'tak fallback had been specified, and the Ha'tak gravship family itself remained a required unfinished branch.
