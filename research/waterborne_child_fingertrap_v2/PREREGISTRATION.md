# Waterborne-child / travelling-fingertrap test v2 — preregistration

Date frozen: 2026-09-14

## Research target

This v2 test is designed around the actual Vardath Cosmology prediction:

> If the travelling-fingertrap reading is more than free resemblance, waterborne-child stories should disproportionately use **woven, hollow, tubular, sealed, flexible or reopenable enclosures**; they should disproportionately terminate at a distinct boundary or receiver; and the stories should disproportionately pair transport with **changed household, changed identity or second-birth language**. Those features can be frozen before a multilingual corpus search and tested against exposed-child stories that do not involve water.

The intended discovery domain is worldwide myth, legend, folktale, epic, fable, religious tradition and scriptural story material involving babies, infants or children, including Moses/Sargon/Karna/Romulus-type narratives. The test does not assume those canonical examples are the whole corpus.

## Why this is v2

The earlier v1 series drifted toward a broad `exposed child` search and then spent several runs repairing transport defects. v2 preserves those runs as diagnostic history but redesigns discovery around the original question rather than retuning v1 after seeing its results.

## Twenty independent language shards

Exactly 20 language editions of Wikipedia are searched independently:

English, French, German, Spanish, Italian, Portuguese, Dutch, Polish, Czech, Russian, Ukrainian, Greek, Turkish, Arabic, Hebrew, Persian, Hindi, Bengali, Japanese and Chinese.

Each language receives two frozen discovery banks:

1. **waterborne-child discovery** — native-language searches combining baby/infant/child + river/water + myth/legend/religious-story concepts;
2. **non-water exposed-child discovery** — native-language searches combining abandoned/exposed/foundling child + myth/legend/folklore/religious-story concepts.

Each bank contains five queries per language. The waterborne searches deliberately do **not** contain basket, ark, woven, hollow, tubular, sealed, receiver, adoption, fosterage, rebirth or equivalent predicted-feature terms. The control searches likewise avoid those dependent features.

Each shard stores local titles, Wikidata QIDs, English sitelinks when available, discovery query hits and whether the record came from the water-search bank, control-search bank or both. No confirmatory scoring occurs inside the shards.

## Merge and evidence extraction

After all 20 shards complete, the merge stage deduplicates records by Wikidata QID (or normalized English title if no QID exists), then fetches the first 5,000 characters of full English plaintext for each unique English counterpart. Full articles are requested **one title per TextExtracts request** so the API cannot silently collapse a multi-title batch to one full extract.

The English text is used only to hold confirmatory lexical coding to one language. Multilingual discovery remains the mechanism for finding culturally distributed stories.

## Eligibility

A record is eligible when the first 5,000 characters contain:

- a baby/infant/child anchor;
- an exposure/abandonment/setting-adrift anchor within 1,000 characters of the child anchor;
- mythic, legendary, folkloric, epic, scriptural or religious context;
- at least 250 characters of usable prose.

Modern real-world pages and irrelevant search results should therefore fall out unless their opening text genuinely describes a mythic/religious narrative.

## Target and control groups

An eligible record is **waterborne** when a water term is within 1,000 characters of child/exposure anchors and a transport/exposure relation connects the child and water episode within the frozen windows.

An eligible record is a **non-water control** when there is no water term anywhere in the 5,000-character coding window.

Eligible records containing water but failing the local waterborne relation are **ambiguous** and excluded from the confirmatory comparison.

Discovery-bank membership does not itself determine group assignment; the text does.

## Frozen predicted features

### F1 — travelling-fingertrap-compatible enclosure geometry

Two levels are recorded.

**F1 broad enclosure/carrier:** basket, wicker/reed basket, woven object, ark, chest, box, casket, coffer, cradle, barrel, drum, bag, sack, jar, pot, vessel, trough, coracle, bamboo, tube, hollow/sealed/enclosed/wrapped carrier.

**F1 strict geometry:** basket/wicker/reed/rush/papyrus basket, woven/weave, bamboo, tube/tubular, hollow, sealed, enclosed, wrapped, flexible, reopenable or coracle wording.

The strict geometry score is the confirmatory F1 measure because it most directly expresses the cosmology paragraph rather than generic transport.

### F2 — boundary / receiver termination

Shore, bank, reeds, weir, net, ashore/landing, finding, catching, rescue, retrieval/recovery, fisherman, washerwoman, water-drawer, temple, palace, household or equivalent receiving language within the frozen proximity window.

### F3 — changed household / changed identity / second birth

Adoption/fosterage, being raised/reared/nursed by another, naming/renaming, orphan/foundling identity, new family/household, recovered parentage, rebirth/second birth, or equivalent social-identity transfer within the frozen proximity window.

### Negative-control family

Horse/equestrian, weapon/sword/spear, musical instrument, furniture/chair, garment/clothing. Comparable enrichment here flags generic narrative richness rather than the predicted package.

## Confirmatory tests

### T1 — primary structural-package test

Outcome: at least **two of F1-strict, F2 and F3** occur in the record.

Prediction: waterborne > non-water controls.

Pass rule:

- at least 25 waterborne targets and 25 non-water controls;
- risk ratio >= 1.50;
- two-sided Fisher exact p < 0.05.

If the sample-size floor is not reached, T1 is formally **UNDERPOWERED** regardless of effect size.

### T2–T5 — component tests

- T2: F1 strict geometry enriched in waterborne targets;
- T3: F2 boundary/receiver enriched;
- T4: F3 identity/second-birth enriched;
- T5: full F1-strict + F2 + F3 package enriched.

Pass rule for T2–T5: RR >= 1.50 and Benjamini-Hochberg q < 0.05 across those four tests.

### T6 — negative-control check

A confound flag is raised if the unrelated negative-control family has RR >= 1.50 and Fisher p < 0.05.

## Retrieval audit

The merge reports whether the discovered corpus includes several well-known audit cases that motivated the research question: Moses, Sargon of Akkad, Karna, Romulus and Remus, Danaë and Perseus. These are **coverage checks only** and are not force-added to the scored corpus.

## Interpretation

A positive result means the preregistered narrative grammar is enriched in this multilingual discovery corpus. It does not by itself prove common historical transmission or a physical cosmological mechanism.

A null adequately powered result counts against the strong textual prediction as formulated. An underpowered result remains unresolved.

No search terms, feature lexicons, distance windows, sample floor, statistical test or pass threshold may be retuned after the run. A materially changed design becomes v3.
