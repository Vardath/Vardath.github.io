# Waterborne-child v1 — acquisition correction after diagnostic merge

Date: 2026-09-14

Run `34815573919` was the first execution in which all 20 shards and the merge completed successfully. It immediately exposed an implementation-level acquisition defect:

- raw multilingual discoveries: 2,651;
- records reported as having English extracts: 25;
- English shard alone discovered 145 pages but returned only 6 English extracts;
- the six English extracts corresponded to approximately one extract returned per API batch.

The cause is the MediaWiki `prop=extracts` API default limit. The retrieval code requested batches of titles but did not explicitly set `exlimit`, so the API returned only a limited subset of extracts from each batch. This violated the preregistered acquisition intention to store English plaintext for every resolvable English counterpart.

The diagnostic merge consequently contained only four eligible records (2 waterborne, 2 non-water) and T1 was correctly labelled UNDERPOWERED. Those numerical outcomes are preserved as a failed/invalid acquisition checkpoint and are not treated as evidence for or against the scientific prediction.

Correction before the valid confirmatory run:

- fetch English extracts in batches of 20 titles;
- set `exlimit=max` explicitly;
- leave the same 20 language shards, the same search queries, discovery limits, eligibility rules, feature lexicons, distance windows, sample floor, statistics and pass criteria unchanged.

This is a retrieval-completeness repair, not a hypothesis or threshold retune. The corrected run remains the preregistered v1 analysis; the incomplete diagnostic run remains preserved in GitHub Actions history.
