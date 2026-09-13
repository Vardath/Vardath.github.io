# Masonic ladder / sky / lattice validation — v2

Preregistered 2026-09-13 after the first 20-shard pilot was found to be underpowered and retrieval-contaminated. The pilot result is preserved and is not overwritten.

## Why v2 exists

The pilot searched for `masonic + ladder` in the retrieval query. That produced only 15 matched pairs and admitted irrelevant hook-and-ladder/road material. V2 therefore retrieves a broad Masonic symbolic-art corpus first and only then classifies ladder/ascent, celestial, lattice-structure and axis language independently.

## Primary question

Within broad Masonic/Freemason visual records, are ladder/ascent records more likely than matched Masonic non-ladder records to contain explicit celestial context?

## Frozen families

- Ladder/ascent: ladder, ladders, stair, stairs, stairway, staircase, steps, rung, rungs, Jacob's ladder, ascent, ascending.
- Celestial: sky, heaven/heavens/heavenly, star/stars/stellar, sun/solar, moon/lunar, celestial, firmament, zodiac, constellation, cloud, vault, canopy, astral.
- Lattice structure: rail, rails, rung, rungs, crossbar, crossbars, parallel, grid, lattice, mesh, net, network, interlace, woven, crossing, transverse, framework, trellis.
- Axis: pillar, column, rod, staff, tree, tower, obelisk, axis, axial.

Negative controls: portrait/bust, horse/equestrian, furniture, garment/costume, landscape.

## Acquisition

20 Wikimedia Commons shards. Each shard has one broad Masonic/Freemason symbolic-art query and one neighboring non-Masonic symbolic-art query. Retrieval queries do not contain the word `ladder`.

Target records must contain an explicit Masonic/Freemason label in title/description/category text. Control records containing such labels are excluded.

## Matching and endpoints

Primary comparison: Masonic ladder-positive records matched 1:1 to Masonic ladder-negative records by description-length bin and nearest available year.

Primary endpoint: celestial-context rate. Positive criterion: RR > 1.5 and two-sided Fisher p < 0.05.

Secondary endpoints:
1. lattice-structure language;
2. celestial + lattice structure;
3. axis language;
4. celestial + axis;
5. external check: celestial-context rate in Masonic ladder-positive records versus non-Masonic ladder-positive records.

A minimum of 25 matched Masonic ladder-positive records is required for a conclusive primary test. Below that threshold the result is labelled underpowered even if point estimates are large.

The query map, vocabularies, matching rule, thresholds and endpoints are frozen before the v2 results are inspected.