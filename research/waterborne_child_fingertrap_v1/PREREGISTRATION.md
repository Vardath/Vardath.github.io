# Waterborne-child / travelling-fingertrap test v1 — preregistration

Date frozen: 2026-09-14

## Question

The current Vardath Cosmology section predicts that stories in which an exposed or endangered child is carried through water should disproportionately preserve a three-part structural package:

1. **carrier / enclosure** — woven, hollow, tubular, sealed, flexible or reopenable transport objects, represented in narrative text by baskets, boxes, chests, arks, barrels, drums, bags, tubes, bamboo, vessels, troughs, cradles, rafts/boats or explicit enclosing/sealing language;
2. **boundary / receiver** — a shore, bank, reeds, weir, net, landing place, temple/palace/household, or an explicit finding, catching, rescue, retrieval or recovery event;
3. **changed household / identity / second birth** — adoption, fosterage, being raised by another household, naming/renaming, foundling/orphan identity, recovered parentage, rebirth/second-birth language or an equivalent transfer of social identity.

The prediction is stronger than the generic exposed-child hero motif. The claim to be tested is that **waterborne exposure** is unusually associated with this combined transport package when compared with **exposed-child stories discovered by the same search procedure that do not contain a water episode near the exposure event**.

## Corpus and discovery protocol

One GitHub Actions run will use exactly **20 parallel shards**. Each shard is assigned one language edition of Wikipedia and runs three native-language discovery queries for the broad exposed/abandoned/foundling-child motif. The discovery queries are deliberately forbidden from containing the dependent-feature concepts: no water/river/sea terms, no basket/ark/container terms, no rescue/shore terms and no adoption/foster/rebirth terms.

Frozen language shards:

0. English
1. French
2. German
3. Spanish
4. Italian
5. Portuguese
6. Dutch
7. Polish
8. Czech
9. Russian
10. Ukrainian
11. Greek
12. Turkish
13. Arabic
14. Hebrew
15. Persian
16. Hindi
17. Bengali
18. Japanese
19. Chinese

Each shard requests up to 50 results per discovery query from the corresponding Wikipedia search API, resolves Wikidata QIDs when available, resolves an English Wikipedia counterpart when available, and stores the English introduction text for confirmatory coding. The 20 shards therefore perform multilingual discovery while the confirmatory feature coding is held to one language so that differences in stemming/translation rules do not create 20 different classifiers.

Records without an English counterpart may be counted in discovery totals but are excluded from the confirmatory lexical test. Duplicate discoveries across languages are deduplicated by Wikidata QID; where no QID is available, the normalized English title is used.

## Eligibility filter

The English introduction must:

- contain at least one child/infant anchor;
- contain at least one exposure/abandonment/foundling anchor;
- contain at least one mythic/religious/legendary context anchor;
- contain at least 250 characters of usable prose.

Modern real-world child-abandonment pages may therefore be discovered but should fail the mythic-context criterion unless the introduction explicitly places them in myth, legend, folklore, epic, scripture or religious tradition.

## Waterborne target versus non-water control

Coding is restricted to the first 5,000 characters of each eligible English introduction.

A record is **waterborne target** if at least one frozen water term occurs within 900 characters of a child or exposure anchor.

A record is **non-water exposed-child control** if no frozen water term occurs anywhere in the 5,000-character coding window.

If water terms occur but not within 900 characters of a child/exposure anchor, the record is marked **ambiguous** and excluded from the confirmatory comparison rather than forced into either group.

## Frozen feature families

The implementation will use fixed English substring/phrase lexicons for the following families.

### F1 — carrier / enclosure

Examples include: basket, ark, chest, box, casket, cradle, barrel, drum, bag, sack, bamboo, tube, vessel, trough, boat, raft, container, wicker, reed basket, woven, hollow, sealed, enclosed, wrapped, leather bag.

A hit must occur within 1,200 characters of a child, exposure or water anchor.

### F2 — boundary / receiver

Examples include: shore, bank, reeds, weir, net, ashore, landing, found, discovered, caught, rescued, retrieved, recovered, fisherman/fisher, washerwoman, water-drawer, temple, palace, household.

A hit must occur within 1,500 characters of a child or water anchor.

### F3 — changed household / identity / second birth

Examples include: adopt/adopted/adoption, foster, raised by, brought up by, named/renamed, foundling, orphan, new family/household, recovered parentage, reborn/rebirth/second birth.

A hit must occur within 1,800 characters of a child anchor.

### Negative-control family

Unrelated motifs: horse/equestrian, weapon/sword/spear, musical instrument, furniture/chair/throne, garment/clothing. This family is not part of the Vardath prediction. Strong enrichment here flags generic narrative-description richness or genre confounding.

## Confirmatory tests

### T1 — primary combined-package test

Outcome: record contains **at least two of F1, F2, F3**.

Prediction: waterborne targets > non-water controls.

Pass rule:

- at least 25 waterborne targets and 25 non-water controls;
- risk ratio **>= 1.50**;
- two-sided Fisher exact **p < 0.05**.

If the sample-size floor is not reached, T1 is formally **UNDERPOWERED**, regardless of effect size.

### T2 — carrier/enclosure

Prediction: F1 is enriched in waterborne targets.

Pass rule: RR >= 1.50 and Benjamini-Hochberg q < 0.05 across T2–T5.

### T3 — boundary/receiver

Prediction: F2 is enriched in waterborne targets.

Pass rule: RR >= 1.50 and BH q < 0.05 across T2–T5.

### T4 — changed household/identity/second-birth

Prediction: F3 is enriched in waterborne targets.

Pass rule: RR >= 1.50 and BH q < 0.05 across T2–T5.

### T5 — full three-family package

Prediction: all F1+F2+F3 occur together more often in waterborne targets.

Pass rule: RR >= 1.50 and BH q < 0.05 across T2–T5.

### T6 — unrelated negative-control check

The unrelated negative-control family should not show an enrichment comparable to the primary package. A confound flag is raised if negative controls have RR >= 1.50 and Fisher p < 0.05.

## Secondary robustness checks

1. Repeat the main proportions after restricting both groups to records with 500–5,000 characters of text.
2. Report results by discovery language and the number of distinct languages contributing waterborne targets.
3. Report duplicate QIDs discovered independently by multiple language shards.
4. Report the highest-scoring target and control records so classification can be inspected manually.
5. Report an extract-length-stratified Mantel-Haenszel odds ratio using four frozen length bins: 250–749, 750–1499, 1500–2999, 3000–5000 characters.

These robustness checks do not replace T1.

## Interpretation rules fixed before acquisition

- A positive result establishes enrichment of the preregistered **narrative grammar in this discovery corpus**. It does not by itself establish a shared historical source or physical cosmological cause.
- A null result counts against the strong textual prediction as currently formulated.
- If F1 is positive but F2/F3 are not, the result supports only the narrower claim that waterborne exposure preferentially uses enclosures/carriers.
- If F2/F3 are also high in non-water controls, that would fit the ordinary exposed-hero motif and weaken the claim that water adds a distinctive gate/second-birth package.
- If the negative-control family is similarly enriched, the result is treated as confounded.
- No lexicon, threshold, language list, query set, distance window, sample-size floor or pass criterion may be retuned after the run. Any materially changed analysis becomes v2.

## Output

The merge job will require all 20 shard artifacts and write:

- `research/waterborne_child_fingertrap_v1_results/summary.json`
- `research/waterborne_child_fingertrap_v1_results/records.csv`
- `research/waterborne_child_fingertrap_v1_results/2026-09-14_report.md`

The result artifact will preserve the complete merged coded corpus for inspection.
