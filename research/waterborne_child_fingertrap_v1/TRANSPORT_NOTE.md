# Waterborne-child v1 — transport / execution note

Date: 2026-09-14

The first GitHub Actions acquisition attempt and its failed-job retry both reached the frozen protocol successfully, but English shard 0 was rejected by the English Wikipedia API with HTTP 429 while fetching English extracts. The first attempt had 19 successful shard jobs and one transport failure; the merge was skipped. The retry reproduced the same 429 on English shard 0. No merged result existed and no scientific outcome had been inspected.

Before a successful acquisition, execution is therefore being hardened without changing the scientific protocol:

- HTTP 429 now respects `Retry-After` when present and otherwise uses a long exponential backoff;
- English extract batches are deliberately paced rather than fired in a burst;
- the same 20 languages, same three discovery queries per language, same result limits and same English confirmatory text remain in force;
- short ASCII object terms of four characters or fewer are matched as terms rather than arbitrary internal substrings, implementing the already-frozen rule that `ark` must not match `dark`/`mark`, `bag` must not match a longer unrelated word, etc.;
- JSON result serialization is made non-finite-safe so an infinite risk ratio caused by zero control hits can be recorded without crashing the merge. This does not change the statistic or pass rule.

These are execution/correctness repairs made before any complete merged dataset or test result. They are not a post-result retuning. Any change to the corpus queries, feature lexicons, coding distances, sample floors, or pass thresholds after a successful merge would require a new v2 preregistration.
