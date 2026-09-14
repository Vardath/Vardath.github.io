# Waterborne-child v1 — implementation freeze

Date: 2026-09-14

This file records two pre-acquisition implementation clarifications made after the initial preregistration but before any corpus shard was run.

1. The English confirmatory text uses up to the first 5,000 characters of plaintext from the linked English Wikipedia page rather than only the lead paragraph. This is because the exposure episode can occur just below the lead while still being the exact story discovered by the native-language search.
2. Search-vocabulary leakage is blocked in dependent-feature coding. In particular, the discovery term `foundling` does not itself count as a boundary/receiver or identity-family hit. Boundary coding uses explicit retrieval phrases such as `was found`, `were found`, `rescued`, `retrieved`, `recovered`, shore/bank/reeds/weir/net/ashore/landing, and named receiver-place terms. The identity family uses adoption/fosterage/raised-by/naming/orphan/new-family/parentage/rebirth language but does not award a hit merely for the word `foundling`.
3. Eligibility requires an exposure/abandonment/foundling anchor to occur within 900 characters of a child/infant anchor, reducing accidental inclusion of pages where those ideas occur in unrelated parts of the text.
4. Short object terms are treated as terms rather than arbitrary internal substrings during manual interpretation; the automatic lexicon was reviewed before acquisition so `foundling` does not create a `found` hit and `throne` was removed from the unrelated negative-control family because it is too closely tied to hero/king outcomes.

No data had been acquired when these clarifications were frozen. All pass thresholds, language shards, search queries, coding windows, sample-size floors and confirmatory tests remain as preregistered. Any post-run alteration becomes v2.
