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


## Retrieval ranking and collection progression
The index now ranks query terms by inverse fragment frequency, preserves the first 24 distinct query terms in user order, and reranks actual excerpts using a bounded adjacent-term bonus. Each document contributes at most eight candidate fragments, at most two nonduplicate excerpts, with a distinct-source first pass. Source reads are bounded to 16 successful extractions (two PDFs); hashes and current enrollment are rechecked before returning each chosen excerpt. Exclusions are applied in the SQL candidate stage. Unseen manuals receive priority on subsequent discovery passes; forgotten documents do not consume discovery slots. This is lexical retrieval; synthetic independent-answer regressions test the old starvation cases, not real model intelligence or semantic retrieval parity.


## Independent Sentinel document review
New knowledge excerpts supplied through JANUS document-search, ordinary short draft planning, and technical recovery are independently reviewed by Sentinel on the existing ONNX council. Exact source evidence, project, task, original specification and amendment history bind a durable verdict. Only an exact USE response and current revalidated evidence allow optional context delivery. Rejection, uncertainty, missing advisor or insufficient prompt space withhold this optional evidence; ordinary work can continue. The pre-existing short-reference and manifest pathways remain unchanged. This is a relevance/scope screen, not factual validation, runtime testing, or a permission grant. The same model performs both roles. Long indexed planning and real-world model evaluation remain future work.

## Portable knowledge enrollment manifests

In Project knowledge, select up to 12 current enrolled documents and choose Export selected enrollment. The new JSON contains project-relative paths and exact SHA-256 hashes, not document bodies, indexed postings, state databases or credentials. Move the manifest and the original documents separately into a destination workspace preserving relative paths. Import enrollment manifest previews the exact document names and requires confirmation. It refuses changed/excluded/missing files, duplicate or unsafe paths and quota violations; all lexical postings are regenerated locally in one transaction. Existing source files are never overwritten. Reimport explicitly enrolls the matched sources. This is portable enrollment reconstruction, not a full database or content backup.

## Reviewed knowledge graph (Pass 082)

Files & Images → Build knowledge graph. Select a typed JSON specification and a new JSON output. The `document` must be a project-relative TXT/Markdown/RST/AsciiDoc source. Provide `nodes` (id, label, kind, evidence) and `edges` (from, to, predicate, evidence). Every evidence object contains one-based `line`, zero-based `start`, and an exact `quote` (maximum 500 characters). Node labels must appear in their quotes, and both endpoint labels must appear in an edge quote. The report includes directed adjacency and the exact document SHA-256. Predicates are reviewer assertions, not verified facts. Original source and index remain unchanged; no new execution authority.

## Automatic relationship candidates (Pass 083)

Files & Images → Discover relationship candidates. The typed JSON specification contains `document`, `nodes` (as in the reviewed graph) and `max_candidates` (1–128). Choose 2–32 exact entity labels. Candidate pairs are discovered automatically from whole-label matches within 500 characters on the same source line; dense lines with more than 128 mentions are skipped and reported. Each pair retains supporting-line count and up to three exact quote locators. Co-occurrence is an observation, never a verified semantic predicate or an automatic graph mutation.

## Explicit larger text enrollment (Pass 084)

Explicit enrollment of TXT, Markdown, RST and AsciiDoc now permits up to 2 MiB, 16,384 fragments and 200,000 postings per document. The existing aggregate project quota remains in force, along with line/content filtering and exact source hash checks. Automatic discovery, DOCX and PDF limits are unchanged. The existing index and portable enrollment manifest support these larger text sources; no new document body storage is introduced. Cancellation during fragmentation rolls back the index transaction. Larger and streaming ingestion is not yet implemented.
