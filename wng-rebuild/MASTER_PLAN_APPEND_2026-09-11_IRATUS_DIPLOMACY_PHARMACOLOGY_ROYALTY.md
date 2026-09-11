# WNG MASTER PLAN APPEND — IRATUS ECOLOGY, WRAITH DIPLOMACY, PHARMACOLOGY + ROYALTY

Date: **2026-09-11**  
Author/design authority: **Vardath**

## STATUS

**PLANNED CONTENT. DO NOT IMPLEMENT THIS APPEND AS PART OF THE CURRENT HA'TAK SLICE UNLESS VARDATH EXPLICITLY MOVES IT FORWARD.**

This append records design decisions and approved directions from the 2026-09-11 planning discussion. It supplements `MASTER_PLAN.md` and `MASTER_PLAN_APPEND_2026-09-11_ANOMALY_AND_IDEOLOGY.md`.

WNG requires the full RimWorld DLC set and may use the most appropriate native mechanics from Royalty, Ideology, Biotech, Anomaly and Odyssey.

---

# 1. IRATUS BUGS — REAL WILD ANIMALS

Iratus bugs are intended to exist as actual biological animals, not abstract research tokens.

Current design targets:
- rare wild spawning on suitable maps rather than common pest frequency;
- substantially higher encounter likelihood near Wraith worlds, Wraith laboratories, Iratus nests and hybrid-experiment sites;
- not ordinary tameable livestock by default;
- can be captured alive and kept for study/containment;
- can provide biological samples/extracts through controlled handling;
- can escape and create real colony hazards.

## 1.1 Attachment attack

The signature Iratus attack should be preserved:
- bug attacks and attempts to attach around the target pawn's neck/upper body;
- successful attachment becomes a persistent attached-organism state rather than an ordinary bite disappearing into a Hediff with no physical source;
- victim suffers extreme pain followed by severe movement loss/paralysis;
- attached bug feeds/drains the host over time;
- attached bug regenerates strongly while feeding;
- forcible removal risks harming the host;
- ordinary combat damage against the attached bug should carry host risk where mechanically feasible;
- medical removal can be attempted but is dangerous;
- salt water is a valid canonical repellent/removal aid and should be represented if a clean gameplay implementation can be made.

The same exact bug should remain the source of the attachment where identity/state matters; do not silently replace it with a proxy effect.

## 1.2 Iratus queens

Iratus queens should be rarer and substantially more valuable alive.

Potential roles:
- high-tier xenobiology specimen;
- source for rare restorative biological compounds;
- dangerous nest/encounter objective;
- extreme Wraith medical treatment path inspired by Wraith use of a queen to restore otherwise terminally ill Wraith;
- possible hybridisation/reversion complications if used on humans or hybrids.

Capturing a queen alive should be a meaningful strategic choice rather than merely harvesting meat.

---

# 2. WRAITH DIPLOMACY, PATRONAGE AND HUMAN CLIENT STATES

Wraith politics should not reduce to universal permanent hostility.

Stargate lore includes:
- Wraith worshippers who actively serve Wraith Hives;
- humans conditioned or socially integrated into Hive service;
- human settlements making survival deals with Wraith;
- communities surrendering outsiders/refugees/feeding subjects in exchange for being spared;
- pragmatic cooperation that is not necessarily religious worship.

WNG should therefore support two distinct broad relationships:

## 2.1 Wraith worshippers

Human groups who regard a Hive/Queen as legitimate, sacred or superior authority.

Possible functions:
- court attendants;
- spies/informants;
- tribute brokers;
- Stargate contacts;
- prisoner/feeding-stock handlers;
- human auxiliaries;
- intermediaries between ordinary settlements and a Hive.

## 2.2 Tributary/client settlements

Human groups who may dislike or fear the Wraith but maintain a survival agreement.

A settlement/client-state record may include:
- patron Hive;
- tribute type;
- feeding quota or prisoner transfer expectation;
- protection status;
- diplomatic intermediary status;
- current compliance/breach state.

Attacking such a settlement may anger its Wraith patron. Helping it escape patronage may improve human relations while worsening Hive relations. Supporting the arrangement may improve Hive standing while creating Ideology consequences.

## 2.3 Player relationship ladder

Do not model Wraith relations as generic gift spam alone.

Possible conceptual ladder:

**Prey -> Tolerated -> Useful -> Accord -> Favoured -> Allied**

Exact names/mechanics are not locked.

Faction-specific direction:
- **Sable Brood** — effectively irreconcilable predatory Hive; hostility should be permanent or nearly permanent unless Vardath changes it.
- **Cinder Court** — aggressive and Queen-centred but may grudgingly recognise strength, honour agreements or temporary mutual interest.
- **Veiled Hive** — strongest pragmatic diplomacy/secret-accord branch; capable of trade, intelligence exchange and selective coexistence.
- **Pale Covenant** — easiest route to sustained coexistence/trade if feeding needs can be met without breaking the relationship.

## 2.4 Strategic hunger remains active during friendship

Friendly Wraith do not stop needing to feed.

The existing strategic hunger system should later support friendly/neutral accord behavior:
- hungry friendly Hive can request feeding access/subjects under an existing accord;
- player may provide hostile captives, condemned prisoners, willing donors if such a later system is approved, negotiated substitutes, or another agreed source;
- refusal should not automatically flip a high-goodwill faction to war, but repeated hunger plus broken commitments can erode trust and raise attack pressure;
- honouring agreements should build standing/favour;
- ordinary Drain Life remains separate from strategic faction hunger.

---

# 3. ROYALTY — WRAITH PSYCHIC / COURT LAYER

Royalty should be used where its native systems fit Wraith lore instead of treating it as merely an orbital-bombardment dependency.

## 3.1 Wraith telepathy through psycast grammar

Wraith psychic abilities should use Royalty's native psychic/psycast machinery where practical while remaining biological Wraith telepathy in lore, not supernatural wizardry.

Potential WNG-specific psychic abilities:
- **Hive Sense** — detect nearby Wraith/hybrids or sense Hive-linked minds;
- **Mind Probe** — extract information/reveal traits or states;
- **Predator's Presence** — fear/panic/mental pressure;
- **Compulsion** — bounded temporary influence;
- **Queen's Command** — stronger Hive/hybrid command available only to appropriate sovereign Wraith;
- **Shared Sight** — temporary sensory sharing through another Hive-linked pawn;
- **Psychic Beacon / Hive Call** — attract or coordinate Wraith attention;
- **Gift Sense** — weaker Wraith-detection/sensitivity available to suitable human/hybrid gene carriers.

Queens should have the strongest natural access. Keepers and selected castes may have intermediate capability. Humans/hybrids with appropriate Wraith ancestry may have limited access.

Do not give every Wraith identical psychic power.

## 3.2 Hive favour / Queen court standing

Royalty's honour/favour/permit grammar is a useful native inspiration for a separate Wraith court-standing system.

This should not literally make the player an Empire noble or rename Wraith society into imperial titles.

Potential ways to earn Hive favour:
- honour feeding accords;
- rescue/return captured Wraith;
- recover Wraith technology;
- defeat a rival Hive;
- defeat Replicators/Asurans threatening the Hive;
- provide intelligence;
- assist a Queen;
- keep prior agreements.

Potential favour requests/permits:
- Dart extraction;
- Wraith military escort;
- intelligence on threats/sites;
- temporary sanctuary;
- Wraith biological treatment;
- trade audience;
- feeding exemption/renegotiation;
- permission to enter selected Hive facilities;
- later orbital/ship support where lore and balance support it.

Goodwill and Hive favour should be allowed to differ: a Queen may value a colony's usefulness without considering it equal.

---

# 4. WRAITH / IRATUS PHARMACOLOGY

Wraith and Iratus biology should support a meaningful medical/drug economy tied to actual research/specimens rather than generic reskinned RimWorld drugs.

ONAC owns **tretonin/tritonin**. WNG must not duplicate or replace it.

## 4.1 Raw Wraith Enzyme

Canon-derived combat stimulant harvested from Wraith enzyme biology.

Intended effects:
- dramatic short-term boost to consciousness/physical performance;
- movement/melee improvement;
- pain tolerance;
- increased resistance to incapacity/stunning;
- improved survival/healing support.

Risks:
- extremely addictive;
- overdose can cause aggression, instability or irrational behaviour;
- severe dependence/withdrawal can become medically dangerous;
- supply creates moral/prisoner pressures because living or dead Wraith can become sources.

The drug should feel genuinely powerful enough to tempt the player rather than being a trivial +10% stat consumable.

## 4.2 Refined Wraith Enzyme

Processed controlled formulation:
- lower peak than raw enzyme;
- safer dosing;
- still addictive;
- suitable as a deliberately manufactured military/medical stimulant after research.

## 4.3 Wraith Enzyme Weaning Serum

Controlled treatment for enzyme dependency:
- expensive;
- may require small measured enzyme doses;
- gradually reduces dependency rather than instantly deleting addiction.

## 4.4 Life-Enzyme emergency concentrate

WNG-original medical derivative based on the biological role of Wraith enzyme in keeping prey alive during feeding.

Potential function:
- temporary anti-shock/emergency survival medicine;
- raises consciousness long enough for rescue/treatment;
- delays collapse from extreme trauma/blood loss;
- does not heal the underlying wound;
- retains some dependency/adverse-effect risk.

## 4.5 Iratus paralytic

Extracted from captured Iratus biology.

Potential uses:
- anaesthetic/tranquilliser;
- high-risk incapacitation drug;
- later capture-weapon ammunition/compound;
- overdose can suppress consciousness/breathing or become lethal.

## 4.6 Iratus rejection/removal agent

Emergency treatment for an attached Iratus bug:
- weakens attachment/feeding;
- assists medical/salt-water removal;
- does not magically despawn the bug.

## 4.7 Iratus Queen Restorative

Rare high-tier compound/treatment derived from living Iratus queen biology.

Possible effects:
- exceptionally powerful restoration on Wraith;
- limited use for severe disease/biological damage;
- dangerous on humans/hybrids;
- may trigger stronger Iratus/Wraith expression, mutation or reversion rather than being universally beneficial.

## 4.8 Hybrid stabiliser

WNG-original treatment for unstable Human-Wraith hybrids/partially transformed subjects:
- suppresses reversion spikes;
- reduces feeding instability/mutation risk;
- requires ongoing dosing where appropriate;
- not automatically a cure.

## 4.9 Wraith retrovirus + suppression cocktail

Treat as two separate treatment layers:
- **Wraith Retrovirus** — initiates suppression/transformation toward human form;
- **Wraith Suppression Cocktail** — recurring maintenance treatment preventing Wraith characteristics from reasserting themselves.

Stopping maintenance can cause gradual reversion.

This can interact strongly with Anomaly containment/rescue content.

## 4.10 Wraith gene therapy / feeding-independence treatment

Late high-risk xenobiology research aimed at restoring ordinary digestion/removing the need to feed.

Early versions may cause catastrophic illness. Later refinement may become a genuine route toward feeding independence.

Do not treat this as guaranteed safe cure technology from the start.

## 4.11 Hoffan serum

Canon-derived anti-Wraith feeding treatment.

Design principle:
- treated humans resist the feeding interaction;
- Wraith attempting to feed can be poisoned by the treated victim;
- early formulations should retain severe mortality risk rather than being softened into a trivial buff;
- later research can reduce recipient mortality;
- use may create major diplomatic consequences with Wraith factions, especially if given to agreed feeding populations under an accord.

---

# 5. STARGATE DRUG / CROP CONTENT OUTSIDE WRAITH BIOLOGY

## 5.1 Kassa — REQUIRED DESIGN DIRECTION

Kassa should be implemented later as a **farmable crop/food**, not merely a trade-only drug item.

Current Vardath direction:
- farmable;
- extremely addictive;
- nutritionally dense enough that a pawn can survive primarily/entirely on Kassa;
- attractive as emergency or cheap staple food;
- addiction is the strategic cost;
- prolonged dependence should make colonies vulnerable to supply disruption;
- raw crop and/or prepared Kassa food can be considered during implementation;
- should support Lucian-Alliance-style trade/crime content later without requiring that entire faction branch immediately.

Gameplay identity:

**Kassa solves hunger while creating dependency.**

A poor colony may intentionally feed everyone Kassa because it is efficient and abundant, then discover that food security has turned into drug-supply dependence.

## 5.2 Reol secretion

Future Stargate infiltration/intelligence drug concept:
- alters recognition/memory so a stranger can be accepted as someone familiar;
- suited to disguise/infiltration/social manipulation mechanics;
- should only be implemented if its source/species/content branch is handled coherently.

## 5.3 Hathor-style Goa'uld pheromonal control

Possible Goa'uld-specific chemical-control content:
- potent pheromonal/loyalty manipulation;
- should integrate with ONAC/RimGate-owned Goa'uld systems rather than WNG claiming ownership of duplicate Goa'uld infrastructure.

---

# 6. IDEOLOGY INTERACTIONS WITH PHARMACOLOGY AND DIPLOMACY

The earlier Anomaly/Ideology append remains authoritative. Additional precept interactions to consider:

## Wraith-derived medicine
Possible positions:
- Abhorrent;
- Emergency use only;
- Acceptable;
- Valuable;
- Sacred gift / biological mastery.

## Drug dependency
Kassa and Wraith-enzyme dependence can interact with ordinary Ideology drug attitudes, but WNG may need more specific precepts if vanilla categories are too broad.

## Wraith patronage
Possible positions:
- Never submit to Wraith;
- Pragmatic accords acceptable;
- Client status acceptable for survival;
- Hive service honoured;
- Wraith worship/reverence.

The same political arrangement should produce different mood/opinion outcomes depending on colony ideology.

---

# 7. CROSS-DLC OWNERSHIP

Preferred native-system mapping:
- **Biotech** — Wraith/hybrid genes, biological identity, transformations;
- **Anomaly** — capture/containment/study of dangerous xenobiological specimens;
- **Ideology** — moral meaning of feeding, patronage, medicine, hybridisation and synthetic life;
- **Royalty** — Wraith psychic ability grammar, court/favour inspiration, native orbital systems;
- **Odyssey** — gravships, orbit, shuttle transport and world-layer behavior.

Do not implement DLC usage merely to tick a checkbox. Use the native DLC system only where it genuinely matches Stargate function.

---

# 8. IMPLEMENTATION ORDER — LATER

This append is approved planning content, not the immediate active coding slice.

When Vardath moves it into implementation, a sensible staged order is:
1. Iratus animal + physical attachment/paralysis/removal;
2. Iratus capture/study and basic extracts;
3. Wraith enzyme pharmacology;
4. Kassa crop/food/addiction loop;
5. advanced xenobiology drugs/treatments;
6. Wraith diplomacy/client-state persistence;
7. Royalty telepathy/Queen court mechanics;
8. Ideology precepts/ritual/role integration after the underlying gameplay systems exist.

Do not use this suggested order to override a newer explicit Vardath priority.
