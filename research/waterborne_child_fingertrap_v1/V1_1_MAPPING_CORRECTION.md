# Waterborne-child travelling-fingertrap v1.1 — mapping correction

The v1 scientific protocol remains frozen. This correction changes only acquisition/transport.

The v1 serial run found 2,651 multilingual search hits but only 27 English-linked records because the local-Wikipedia `langlinks` bridge collapsed almost every non-English result to about one English article per language pass.

v1.1 therefore resolves multilingual search results in two steps:

1. obtain each local page's Wikidata Q-ID from `pageprops`;
2. resolve those Q-IDs through Wikidata `enwiki` sitelinks, then fetch the corresponding English plaintext article.

No scientific feature lexicon, coding distance, eligibility rule, target/control definition, statistical test, multiple-testing rule, pass threshold, or negative control is changed. The purpose is solely to carry the already-discovered multilingual records into the frozen scoring stage.
