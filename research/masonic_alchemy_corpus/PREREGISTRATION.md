# Freemason + Alchemical Visual Grammar Test — Preregistration

**Project:** Vardath Cosmology  
**Date preregistered:** 2026-09-13  
**Status:** predictions fixed before the 20-shard corpus run

## Research question

If the projection grammar proposed by Vardath Cosmology is genuinely similar to the symbolic grammar used in Freemason and alchemical visual/document traditions, then those traditions should not merely contain isolated familiar symbols. They should disproportionately combine several of the model's predicted structural families in the same record, and the pattern of combinations should differ between Freemason and alchemical material in a pre-specified way.

This test is about **symbol-package structure in a large corpus**, not proof of historical transmission or proof that the cosmology is physically correct.

## Corpus plan — 20 shards

The run is split into 20 independent acquisition/analysis shards in GitHub Actions.

### Visual-art channel — Wikimedia Commons, shards 0–9

Broad topic retrieval only; no cosmology motif words are used as target retrieval keys except where they are part of the tradition name itself.

Freemason-family target shards use broad queries such as:
- freemasonry
- masonic
- freemason
- masonic lodge
- masonic symbolism

Alchemy-family target shards use broad queries such as:
- alchemy
- alchemical
- alchemist
- alchemical manuscript
- alchemical illustration

Each target shard also retrieves a preassigned stylistic/content control topic such as heraldry, non-Masonic fraternal orders, architecture drawings, ceremonial dress, Christian symbolism, historical chemistry, astronomy, botany, medical illustration or emblem books. Controls containing explicit Freemason/alchemy target labels are removed.

### Document channel — Open Library, shards 10–19

The same broad target families are retrieved from book/document metadata (title, subtitle, subject headings and descriptive fields where available), with controls chosen from neighboring historical genres. Publication year is retained where available.

## Record text used

Wikimedia Commons:
- file title
- file-page wikitext / description
- category names available in the returned page text

Open Library:
- title
- subtitle
- subject headings
- author names only for descriptive context, not motif scoring

The target words `freemason`, `freemasonry`, `masonic`, `alchemy`, `alchemical`, `alchemist` and close spelling variants are **not** themselves motif families.

## Predicted Vardath symbol families

The lexicons are fixed before the corpus run.

1. **axis** — axis, pillar, column, staff, rod, pole, tree, tower, obelisk, mountain, vertical support.
2. **gate / ladder** — gate, door, portal, arch, threshold, ladder, stair, steps, passage, entrance.
3. **serpent / braid** — serpent, snake, dragon, ouroboros, caduceus, entwined/intertwined/braided/plaited forms.
4. **enclosure** — circle, ring, globe, sphere, egg, oval, mandorla, halo, enclosing boundary.
5. **central node / radiance** — eye, star, sun, moon, solar/lunar disk, rosette, radiant/rays, jewel, flame, central light.
6. **four / eight geometry** — fourfold, square/quadrate, four-part, quatrefoil, eightfold, octagon, eight-pointed/eight-rayed/eight-lobed.
7. **water / vessel** — water, river, sea, ocean, fountain, vessel, cup, chalice, flask, retort, alembic, bath.
8. **paired polarity** — pair/twin/double/opposed, sun-and-moon, king-and-queen, male-and-female, two pillars/two columns, black-and-white.

## Negative-control families

Chosen to detect generic rich-description / ornament effects rather than cosmology-specific structure:
- portrait / bust
- horse / equestrian
- musical instrument
- furniture
- landscape
- garment / costume

If these rise to the same degree as the predicted families, the result favors a generic description/genre effect.

## Primary endpoint

For each record, count how many of the eight predicted families are present.

**Primary prediction:** after exact/near matching within source channel on century bin (when known) and description word-count bin, Freemason + alchemical targets will have a higher rate of **3 or more distinct predicted families in one record** than controls.

Report:
- target and control rates
- risk ratio
- odds ratio with Haldane correction
- two-sided Fisher exact p-value
- Benjamini-Hochberg FDR q-value across declared tests

The primary effect is treated as practically interesting only if RR > 1.25 as well as q < 0.05.

## Secondary package predictions

### Freemason material
Predicted strongest combinations:
1. axis + gate/ladder
2. enclosure + central node/radiance
3. four/eight geometry + central node/radiance
4. axis + paired polarity

### Alchemical material
Predicted strongest combinations:
1. serpent/braid + axis
2. enclosure + central node/radiance
3. water/vessel + enclosure
4. paired polarity + central node/radiance

### Shared cross-tradition core
Both traditions are predicted to exceed matched controls in:
- axis + enclosure/node organization
- multi-family package density
- a small recurring set of projection classes rather than arbitrary one-off symbol lists

## Stronger model prediction

The model predicts a **division of labor around a shared geometry**:
- Freemason imagery should emphasize architectural/axial/gate and radial-node organization.
- Alchemical imagery should emphasize transformation/polarity/serpent/vessel around the same enclosure-axis-node grammar.

A result in which the two traditions are indistinguishable on all families would be less supportive than a shared core plus the predicted specialization.

## Confound test

Results are weakened if:
- negative-control motifs are enriched as much as predicted motifs;
- the effect exists only in very long descriptions;
- one source channel drives the whole result;
- the primary >=3-family effect disappears under matching;
- results are produced mainly by retrieval-query words rather than independent descriptive fields.

## Fixed stopping rule

The 20 declared shards are run once under this protocol. The merged report uses all successfully retrieved records from those shards after deduplication and stated exclusions. Retrieval terms, motif lexicons and primary endpoint are not changed after seeing results. Any later refinement is a new test/version.
