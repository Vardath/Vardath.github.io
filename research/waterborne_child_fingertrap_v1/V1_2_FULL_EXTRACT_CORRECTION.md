# Waterborne-child travelling-fingertrap v1.2 — full-extract transport correction

The scientific protocol remains the frozen v1 protocol. This correction changes acquisition/transport only.

The v1.1 Wikidata repair worked: 2,649 multilingual discoveries resolved to 2,070 English-title occurrences across the 20 language passes. However only 111 records received English extracts. The failure was in the TextExtracts call, not the Wikidata mapping.

MediaWiki TextExtracts permits multiple extracts in one request only when `exintro` is enabled. The frozen test requires the beginning of the full article, up to `MAX_CHARS = 5000`, so switching to intro-only extracts would change the evidence window. v1.2 therefore requests exactly one full plaintext article per API call (`exlimit=1`), preserving the original scoring window.

The extraction cache is shared across the serial language passes so repeated English titles are fetched once. Cached text is truncated to the frozen `MAX_CHARS` window because the scorer never reads beyond that point.

No search query, language set, scientific feature lexicon, coding distance, eligibility rule, target/control definition, statistical test, multiple-testing rule, pass threshold, negative control, or `MAX_CHARS` value is changed.
