# Local project knowledge (v61 development)

The existing Capability Library short references remain intact. DocumentKnowledge extends them with incremental lexical retrieval for UTF-8 TXT/MD/RST/ADOC and DOCX main text, up to 512 KiB per source, 16 enrolled documents per project, 4096 fragments and 50000 term postings per document. Auto discovery considers up to eight eligible large text or DOCX files in the existing bounded project scan. Larger documents within the 512 KiB ceiling can be enrolled explicitly. PDF, scanned images, OCR, physical DOCX pagination, embeddings and semantic reranking are not included.

From the DeepThorT installation, with the selected workspace path (examples):

    py -3 -m deepthort_local.capability_library --db state/capabilities.sqlite3 knowledge-index "D:\x4mods" docs/manual.docx
    py -3 -m deepthort_local.capability_library --db state/capabilities.sqlite3 knowledge-search "D:\x4mods" "ship macro registry"
    py -3 -m deepthort_local.capability_library --db state/capabilities.sqlite3 knowledge-list "D:\x4mods"
    py -3 -m deepthort_local.capability_library --db state/capabilities.sqlite3 knowledge-remove "D:\x4mods" docs/manual.docx

Removal deletes index entries, not the file, and prevents automatic enrollment until explicit enrollment. Project inspection exclusion purges this new index too. Legacy short-reference records retain their existing policy. Explicit reindex is required for changed explicitly enrolled sources outside automatic discovery.

Search results report SHA-256, relative path, one-based original text line or extracted DOCX paragraph and inclusive character offsets. They are quoted data, not project instructions. DOCX relationships and external resources are not processed. Hashed term postings are derived data, not encryption; protect the state database like other project records. The current lexical filter cannot guarantee detection of every secret or prompt injection. The existing independent specification review, job grants and fixed execution boundaries remain mandatory.

The feature is a first local RAG-style retrieval path, not AnythingLLM feature parity or a measured Qwen performance improvement. Use representative long manuals and independent exact-answer tests before comparing quality.
