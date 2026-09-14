# Waterborne-child v1 — single-run execution note

Date: 2026-09-14

After the parallel 20-shard executions encountered Wikipedia throttling and produced an underpowered merged corpus, the user directed that the test be run as a single test instead of 20 shards.

This changes execution only. The scientific protocol remains the preregistered v1 protocol:

- the same 20 language editions;
- the same three discovery queries per language;
- the same result limits;
- the same English confirmatory-text coding;
- the same eligibility rules;
- the same F1 carrier/enclosure, F2 boundary/receiver, F3 changed-household/identity/second-birth families;
- the same negative-control family;
- the same coding windows;
- the same T1–T6 statistics, sample-size floor and pass criteria.

The replacement execution runs the 20 language acquisitions **serially inside one GitHub Actions job**, with the existing resilient 429 handling and pacing, then performs the merge in the same job. This avoids synchronized API bursts and removes cross-job artifact coordination as a source of execution instability.

The previous sharded runs remain preserved in GitHub Actions history as execution/acquisition diagnostics. They are not substituted for the result of this single-run execution.
