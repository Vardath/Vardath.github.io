# Local project knowledge (v61 development)

The existing Capability Library short references remain intact. DocumentKnowledge extends them with incremental lexical retrieval for UTF-8 TXT/MD/RST/ADOC and DOCX main text, up to 512 KiB per source, 64 enrolled documents per project, 4096 fragments and 50000 term postings per document. Auto discovery considers up to 24 eligible large text or DOCX files in a dedicated bounded scan, including manuals above the ordinary workspace preview limit. Larger documents within the 512 KiB ceiling can be enrolled explicitly. Scanned images, OCR, physical DOCX pagination, embeddings and semantic reranking are not included. Explicitly enrolled text-layer PDFs are supported as described below.

From the DeepThorT installation, with the selected workspace path (examples):

    py -3 -m deepthort_local.capability_library --db state/capabilities.sqlite3 knowledge-index "D:\x4mods" docs/manual.docx
    py -3 -m deepthort_local.capability_library --db state/capabilities.sqlite3 knowledge-search "D:\x4mods" "ship macro registry"
    py -3 -m deepthort_local.capability_library --db state/capabilities.sqlite3 knowledge-list "D:\x4mods"
    py -3 -m deepthort_local.capability_library --db state/capabilities.sqlite3 knowledge-remove "D:\x4mods" docs/manual.docx

Removal deletes index entries, not the file, and prevents automatic enrollment until explicit enrollment. Project inspection exclusion purges this new index too. Legacy short-reference records retain their existing policy. Explicit reindex is required for changed explicitly enrolled sources outside automatic discovery.

Search results report SHA-256, relative path, one-based original text line or extracted DOCX paragraph and inclusive character offsets. They are quoted data, not project instructions. DOCX relationships and external resources are not processed. Hashed term postings are derived data, not encryption; protect the state database like other project records. The current lexical filter cannot guarantee detection of every secret or prompt injection. The existing independent specification review, job grants and fixed execution boundaries remain mandatory.

The feature is a first local RAG-style retrieval path, not AnythingLLM feature parity or a measured Qwen performance improvement. Use representative long manuals and independent exact-answer tests before comparing quality.


## Optional PDF manuals
Install the pinned local parser into the same Python environment used by DeepThorT (explicit one-time setup; no model or network access during retrieval):

    py -3 -m pip install --no-deps -r requirements-documents.txt
    py -3 -m deepthort_local.capability_library --db state/capabilities.sqlite3 knowledge-index "D:\x4mods" docs/manual.pdf

The fixed isolated Python subprocess accepts exact in-memory source bytes, not a command or document-selected path. It processes only the text layer, rejects encrypted/unsupported files, has an 18-second deadline per invocation, accepts up to 4 MiB, 128 pages, 512 Ki characters of extracted text and 20,000 rows, and inherits the desktop's Windows resource supervision. POSIX worker tests also use address-space and CPU limits. This is not an OS security sandbox or OCR. No PDF is automatically parsed during ordinary discovery; an explicit enrollment is required. Search rechecks the source hash and re-extracts up to two enrolled PDFs per call, returning a physical 1-based PDF page and extracted text line (not printed page labels or visual coordinates). No parser installation is attempted from a model request. Missing or incompatible parser, changed file, timeouts or invalid protocol produce no document evidence. Larger manuals should be split or later supported via an indexed page-range mechanism.


## Desktop management
Open **Files & Images → Project knowledge…** in a selected workspace. Enroll documents, discover eligible manuals, refresh current/stale status, search exact excerpts, reindex selected sources or forget them without deleting originals. Each operation runs on a background thread, checks gaming/workspace cancellation at bounded operation boundaries, and uses the existing project inspection exclusions. The library supports 64 documents and one million total lexical postings per project. Discovery scans at most 3,000 directory entries, 12 levels and 24 candidate documents per operation; incomplete scans do not discard unseen valid index entries. PDFs remain explicit enrollment only. Existing Install PDF reader uses the same pinned requirement as the knowledge extractor. No OCR yet.
