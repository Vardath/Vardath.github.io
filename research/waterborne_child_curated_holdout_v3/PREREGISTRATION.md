# Waterborne-child curated validation v3 — preregistration

**Frozen:** 2026-09-17 (Australia/Brisbane), before v3 eligibility adjudication or F1/F2/F3 scoring.

## Purpose

Validate the waterborne-child / travelling-fingertrap result in a semantically clean corpus of genuine traditional narratives. V2 produced a strong combined F1+F2+F3 signal but its automated search universe admitted encyclopedic, media and adventure noise. V3 changes only corpus acquisition and eligibility. It does **not** change the target features, extraction windows, null model, endpoint, statistical test or pass threshold.

This is an **independent-acquisition curated validation**. It is not guaranteed to be narrative-identity-disjoint from v2 because the v2 corpus contains repeated traditional stories. Any known overlap must be reported; no overlap may be removed because of its F1/F2/F3 outcome.

## Frozen baseline eligibility

A record is eligible only when all are true:

1. It is a specific traditional narrative episode from mythology, epic, scripture/religious narrative, folktale, fable, oral tradition, or legendary biography.
2. A child, infant, newborn, or explicitly juvenile figure is physically transported by water/current/sea/river/flood or by a carrier moving through that water/current.
3. The transport is part of the narrative action, not a metaphor, title, commentary, catalogue tag, modern adaptation, film/game/book plot derivative, news report, medical/scientific item, or generic adventure summary.
4. The record can be tied to an identifiable traditional source or source tradition.

Eligibility is decided from baseline facts only. Curators must not use carrier enclosure, opposite-shore recovery, fosterage, identity change, exceptional destiny, or any other F1/F2/F3 outcome to decide inclusion.

## Frozen acquisition route

Candidate acquisition uses public web/source search with **baseline-only** concepts. Target-feature words such as basket, box, ark, chest, receiver, foster, adopt, destiny, king, hero, identity, rebirth, transformation, or return must not be required by the acquisition query.

Frozen English query families:

- `myth infant river`
- `myth child sea`
- `legend infant river`
- `legend child sea`
- `folktale infant river`
- `folktale child sea`
- `religious narrative infant river`
- `epic child river`
- `newborn carried river myth`
- `child transported by water folklore`

Source preference order for adjudication/scoring:

1. primary/translated traditional text;
2. scholarly or university-hosted source reproducing/describing the traditional episode;
3. reputable reference work with a source citation;
4. other source only when the traditional episode and provenance are explicit.

The candidate list must be frozen before target-feature scoring. Duplicate webpages for the same narrative identity are collapsed to one record using the best available source. Geographic/cultural variants count separately only when they are genuinely distinct traditional narrative episodes rather than copies of one source text.

## Frozen target features — inherited unchanged from v2

### F1 — enclosed flexible carrier

Child/infant is carried in an enclosure or bounded flexible/portable carrier such as basket, ark, box/chest/casket, reed container, bag/sack, drum, hollow bamboo/reed, vessel/boat/cradle or equivalent bounded carrier.

### F2 — receiving/recovering opposite boundary

The transported child is retrieved, received, found, rescued, adopted, fostered, taken in, or otherwise reaches a distinct receiving bank/shore/household/person after the water/current transport.

### F3 — correlated identity change / continuation sequence

After transport/recovery the narrative contains a clear continuation involving fosterage/adoption, changed identity/status/name, exceptional destiny/return, kingship/heroic role, or equivalent post-crossing identity continuation. Mere survival without such continuation is not sufficient.

## Frozen extraction windows

Use the same v2 windows where a source page supplies them:

- title;
- first 260 words of summary/context;
- first 700 words of source/narrative text.

For a primary traditional text without a separate summary, score the earliest contiguous passage containing the baseline waterborne-child episode, capped at 700 words. Do not search later in the text for missing target features.

## Frozen statistics — inherited unchanged from v2

Null for each target package: `p0 = 0.20`.

Primary endpoint: **F1 + F2 + F3 all present in the same eligible narrative record.**

Primary test: one-sided exact binomial test over eligible v3 records.

Frozen pass rule:

- `N >= 25`; and
- `K >= max(10, ceil(0.35 * N))`; and
- one-sided exact-binomial `p < 0.001` under `p0 = 0.20`.

Secondary descriptive endpoints, unchanged:

- F1 only;
- F2 only;
- F3 only;
- F1+F2;
- F1+F3;
- F2+F3;
- no target features.

No new threshold may be invented after seeing v3 results.

## Frozen decision rules

- If fewer than 25 eligible narratives survive semantic curation, v3 is **underpowered** and the primary holdout claim is not adjudicated.
- If N >= 25 but the frozen primary rule fails, the clean-corpus validation **fails** even if individual features remain enriched.
- If the frozen primary rule passes, report it as replication in a semantically cleaner independently acquired corpus, **not** as proof of a physical cosmology or common historical origin.
- All exclusions and ambiguous eligibility decisions must be preserved in an audit table.
- Known narrative overlap with v2 must be reported, not selectively removed.

## No post-hoc rescue

After this file is committed, do not:

- redefine F1/F2/F3;
- extend the extraction window because a desired feature appears later;
- lower the N floor;
- lower the K threshold;
- change p0;
- replace the primary endpoint;
- drop negative cases because the source seems atypical;
- add cases because they improve the result.

If acquisition fails to produce N >= 25, record that as an underpowered validation attempt and design a separate future test rather than rewriting this one.
