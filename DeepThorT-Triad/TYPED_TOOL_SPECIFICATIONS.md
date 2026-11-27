# JANUS typed project tools

These local operations accept ordinary UTF-8 JSON specifications stored inside the selected project. The Files & Images tab provides fixed review controls. Choose the specification and a new output filename, inspect the entire normalized specification, then approve the operation. The reviewed specification and any source workbook are hash-bound; an existing output is never overwritten. These are production tools, not permission for a model to run arbitrary commands. Native model-directed execution still needs integration acceptance.

## Edit spreadsheet

Install spreadsheet tools first. Example:

```json
{"workbook":"inventory.xlsx","edits":[{"sheet":"Stock","cell":"B2","value":12},{"sheet":"Stock","cell":"C2","value":null}]}
```

Values are literal finite numbers, booleans, text or null (clear). Existing formula cells require a separate formula operation. Advanced OOXML structures are refused. Formula values are not recalculated.

## Generate SQLite schema

```json
{"tables":[{"name":"items","columns":[{"name":"id","type":"INTEGER","nullable":false},{"name":"title","type":"TEXT","nullable":false}],"primary_key":["id"],"unique":[["title"]],"foreign_keys":[]}]}
```

The new SQL file is tested against an in-memory SQLite database; no existing database is changed. Foreign keys use {"columns":["own_id"],"table":"other","references":["id"]}. Referenced columns must be a declared primary or unique key with matching types.

## Create spreadsheet

```json
{"sheets":[{"name":"Inventory","headers":["Item","Quantity","Cost"],"rows":[["Fuel",12,4.25],["Parts",7,2.1]],"formats":["text","integer","decimal"]}]}
```

Supported formats: general, integer, decimal, percent, text. Outputs are new XLSX files with formatted headers, frozen first row, filters and column widths. Strings are literal. Review results in a spreadsheet application; calculated results and visual fidelity are not verified.

## Generate spreadsheet formulas

```json
{"workbook":"inventory.xlsx","formulas":[{"sheet":"Stock","cell":"D2","replace":false,"expression":{"op":"MUL","args":[{"cell":"B2"},{"cell":"C2"}]}},{"sheet":"Stock","cell":"D10","replace":false,"expression":{"op":"SUM","args":[{"range":"D2:D9"}]}}]}
```

Explicit formula operations only: ADD, SUB, MUL, DIV, EQ, NE, GT, LT, GE, LE, SUM, AVERAGE, MIN, MAX, COUNT, COUNTA, ROUND, ABS and IF. Arguments are nested expressions, cells, aggregate ranges or literals. Same-sheet only. The preview shows exact generated formula text. Existing occupied cells need replace:true. Output formula text is checked but not recalculated; pre-existing dependency chains are not verified.

## Process CSV

```json
{"csv":"inventory.csv","input_delimiter":",","output_delimiter":";","columns":["Item","Quantity"],"start_row":1,"row_count":100,"formula_like_cells":"reject"}
```

Input and output delimiter choices: comma, semicolon, tab and pipe. Select exact column headers and a one-based data row window. UTF-8 literal values are retained, not automatically converted to numbers or dates. Use reject (recommended) or explicitly preserve formula-like strings; preserved strings may be interpreted as formulas when opened in a spreadsheet program.

## Query SQLite

```json
{"database":"inventory.db","query":"SELECT item, SUM(quantity) AS total FROM stock WHERE quantity >= ? GROUP BY item","parameters":[1],"max_rows":100}
```

Use a complete standalone SQLite backup (.db, .sqlite or .sqlite3), not an active WAL database. The exact bytes are opened in disposable memory with read-only query restrictions. SELECT/WITH only, approved built-in functions, ordinary tables, positional parameters and distinct result names. Results are local JSON with explicit truncation; no live database writes.

## Clean CSV data

```json
{"csv":"raw.csv","delimiter":",","trim_columns":["Name"],"missing_tokens":["","NA"],"missing_columns":["Quantity"],"missing_action":"fill","fill_value":"0","deduplicate_by":["ID"],"formula_like_cells":"reject"}
```

Trimming precedes explicit literal missing-value handling; deduplication retains the first remaining row for the selected key. Empty column lists disable their respective operations. No automatic inference or imputation.

## Transform CSV data

```json
{"csv":"data.csv","delimiter":",","formula_like_cells":"reject","operations":[{"type":"filter","column":"Qty","operator":"gt","value":"0","mode":"decimal"},{"type":"derive","name":"Total","left":"Qty","operator":"multiply","right":{"column":"Price"}},{"type":"sort","column":"Total","mode":"decimal","descending":true},{"type":"rename","column":"Qty","name":"Quantity"}]}
```

Operations run in reviewed order. Filters support eq/ne/lt/le/gt/ge; text comparisons use literal string ordering, numeric comparisons require finite decimal strings. Derived arithmetic supports add/subtract/multiply/divide with a column or decimal literal. Division may round at 32 significant digits. Invalid numbers fail closed.

## Edit presentation text

```json
{"presentation":"deck.pptx","edits":[{"slide":1,"before":"Old title","after":"New title"}]}
```

Install presentation tools first. Each edit must match exactly one existing whole text run in a normal slide shape; formatting-split text, charts, tables and notes are not edited. Unchanged package parts are byte-verified. Review text fit visually in a presentation application.

## Create presentations

```json
{"theme":"navy","slides":[{"layout":"title","title":"Project report","body":["Current status"]},{"layout":"bullets","title":"Next steps","body":["Inspect source","Run tests"]},{"layout":"two_columns","title":"Comparison","body":[{"heading":"Before","points":["Manual"]},{"heading":"After","points":["Automated"]}]}]}
```

Themes: navy, graphite, forest. Native editable shapes and text, no rasterized slides. Content is deliberately bounded. Reopened structure is checked, but actual font rendering and text fit still require review.

## Apply presentation template

```json
{"template":"template.pptx","values":{"TITLE":"New title","SUBTITLE":"Reviewed content"}}
```

Prepare whole-run placeholders such as {{TITLE}} inside ordinary slide text shapes. Supply every named placeholder and no unused values. Each named token may appear once per slide and across several slides. Preview includes all resolved replacements. Layouts, masters and untouched package parts are retained; visual fit still needs review.

## Assemble a long-form manuscript

```json
{"title":"Research manuscript","outline":[{"id":"intro","heading":"Introduction","level":1,"min_words":3},{"id":"findings","heading":"Findings","level":1,"min_words":3}],"drafts":{"intro":["A reviewed opening paragraph."],"findings":["Results require independent verification."]}}
```

Provide all named section drafts as literal paragraphs. The ordered outline determines section numbering (levels 1–3), not dictionary ordering. Each section has a reviewed minimum word count. The preview includes section receipts. The new UTF-8 TXT contains every paragraph in order; semantic quality, factual accuracy and native model-authored revision remain separate checks.

## Create a formatted Word document

```json
{"title":"Project report","subtitle":"Reviewed results","theme":"navy","page_size":"A4","blocks":[{"type":"heading","level":1,"text":"Results"},{"type":"paragraph","text":"Verified findings."},{"type":"bullets","items":["First task","Second task"]},{"type":"table","headers":["Name","Value"],"rows":[["Item","12"]]}]}
```

Themes: navy, graphite, forest. Page sizes: A4 and Letter. Heading levels 1–3, literal paragraphs, native bullet lists and rectangular tables. Empty subtitle and empty table cells are allowed. Outputs are editable DOCX with named styles and native table/list structures. Reopened OOXML checks are not visual rendering or factual verification.

## Resolve manuscript citations and bibliography

```json
{"manuscript":"draft.txt","style":"numeric","references":[{"id":"source-a","authors":["Example Author"],"year":2024,"title":"Example title","publication":"Example publisher","locator":"p. 12"}]}
```

Place [[cite:source-a]] in the manuscript. All references must be used; repeated markers reuse the same citation. Numeric labels follow first citation; author_year uses a simple first-author label and rejects ambiguous labels. The complete resolved text is previewed before approval. UTF-8 BOM/newline normalization only; source preserved. Reference metadata is explicitly supplied, not independently retrieved or verified. No formal style-guide compliance or claim-support guarantee.

## Create an interactive data table

```json
{"csv":"inventory.csv","delimiter":",","columns":["Item","Quantity"],"title":"Inventory","page_size":25}
```

Open the new standalone HTML file locally in a modern browser. Search all selected columns, click column headings for stable ascending/descending text sort, and change page size. Literal data is not interpreted as markup or spreadsheet formulas. No network requests; the artifact embeds an exact data snapshot, not a live connection. The review shows total rows and the first 25 rows as a sample. Up to 5,000 rows, 40 columns and 2 MiB embedded data. Browser visual acceptance is separate.

## Create a standalone vector chart

```json
{"csv":"data.csv","delimiter":",","type":"bar","title":"Inventory by month","x":"Month","series":["Quantity","Orders"],"y_label":"Count"}
```

Choose bar (grouped, zero baseline), line (ordered unique categories), or scatter (numeric x). Select one to four numeric series. Missing or nondecimal data is refused rather than guessed; aggregate duplicate categories first. Up to 40 bar rows or 300 line/scatter rows. The SVG includes exact source values as mark metadata and tooltips; category labels may be shortened/sampled for readability. Review the result visually. No source overwrite, external assets or automatic aggregation.

## Create an interactive chart

Use the same typed specification as Create a standalone vector chart. Select a new .html output. Open locally in a modern browser; toggle individual series, select source rows and series or click a visible point for exact values, and reset. Axis ranges remain fixed so hiding a series does not distort comparisons. No live data connection or network requests. Browser visual acceptance remains separate.

## Exact mathematics

```json
{"left":{"op":"add","args":[{"op":"multiply","args":[{"number":"3"},{"variable":"x"}]},{"number":"1"}]},"right":{"number":"8"}}
```

Use expression for constant arithmetic or left/right for a linear equation in x. Values are exact integer, decimal or rational strings. Operations: add, subtract, multiply, divide. Nonlinear terms and variable denominators are refused. The JSON receipt records exact fractions and checked substitution; not a general symbolic solver.

## Personal preferences

Chats → Personal preferences opens the local presentation defaults editor. Select response length/style, metric or imperial units and spelling. Save explicitly or reset fields and save. Defaults apply as bounded advisory context to ordinary chats only, not execution authority or the project specification. Current instructions override saved defaults.

## Statistical analysis

```json
{"csv":"data.csv","delimiter":",","columns":["Quantity","Cost"],"missing_tokens":["","NA"],"variance":"sample"}
```

Explicit numeric columns, exact missing tokens and sample or population variance. JSON results contain exact fractions, 24-significant-digit decimal views and interpolated quartiles. Empty and insufficient samples produce null where undefined. Invalid nonmissing numeric cells block the report. Descriptive only.

## Exploratory data analysis

```json
{"csv":"data.csv","delimiter":",","numeric_columns":["Quantity","Cost"],"categorical_columns":["Region"],"missing_tokens":["","NA"],"top_categories":10,"correlations":true}
```

Explicit column types, up to 10,000 rows, 24 total selected columns and eight numeric columns. Exact full-row duplicates, missingness, counts, top categories, descriptive statistics, IQR flags and pairwise-complete Pearson correlations. No automatic removals or causal conclusions.

## Reproducible analytical report

Use the exploratory analysis specification plus title and expected_source_sha256 (the exact lowercase 64-character CSV SHA-256). Select a new .html output. The local report includes readable tables, methods and an embedded JSON manifest with exact results, input and algorithm hashes, Python version and analysis digest. Repeat with the same source and specification in the same runtime to reproduce the report. No internet or automatic interpretation.

## Detect musical tempo

```json
{"audio":"track.wav","min_bpm":60,"max_bpm":180}
```

16-bit PCM mono/stereo WAV, 8–48 kHz, 3–120 seconds within the shared 16 MiB source limit. The local estimator reports steady transient interval consensus, support fraction and possible half/double ambiguity. Silence or inconsistent transients produce null BPM. This is not a complete beat tracker for complex music.

## Edit music metadata

```json
{"audio":"track.wav","tags":{"title":"New title","artist":"Artist","album":"Album","comment":null}}
```

Edit the eight supported RIFF INFO fields on a local PCM WAV; null removes a field. Printable ASCII only. Preview old/new values and preserve exact audio bytes, format and untouched chunks. Output must be a new WAV. Existing mixed ID3/INFO, MP3/FLAC and Unicode are not supported by this first adapter.

## Estimate musical key

```json
{"audio":"track.wav","channel":"left"}
```

Uses the same bounded 16-bit PCM WAV input as tempo detection. Choose left or right (right requires stereo). The local spectral estimator returns pitch-class evidence, ranked major/minor candidates and a key only when its profile margin is sufficient. Scores are correlations, not probabilities. Silence, single pitches and ambiguous material may yield no key. Complex or modulating music requires listening.

## Reduce quiet audio noise

```json
{"audio":"track.wav","threshold_dbfs":-40,"attenuation_db":-20,"attack_ms":5,"release_ms":100}
```

Bounded 16-bit PCM WAV (same source restrictions as tempo detection). Linked-channel soft gate attenuates low-level intervals with smooth attack/release. It does not remove noise overlapping wanted audio. New WAV preserves frame count, sample rate and channels; metadata is not copied. Inspect the measured quiet RMS and listen to the output.

## Convert PCM WAV audio

```json
{"audio":"track.wav","format":"mp3","bitrate_kbps":192}
```

Choose .mp3 output for MP3 (128/192/256/320 kbps, 32/44.1/48 kHz), or format flac, bitrate_kbps null and .flac output for lossless conversion. Requires the existing installed FFmpeg/FFprobe pair. Uses the bounded PCM WAV input profile. Reopens the encoded stream and decodes it; verifies exact PCM for FLAC and approximate frame duration for MP3. No metadata copying or source mutation.

## Generate a normal map

```json
{"height_map":"height.png","strength":4,"convention":"opengl","edge":"wrap"}
```

Requires Pillow (provided by existing optional presentation or image tools). Input opaque 8-bit grayscale PNG, up to 2048 by 2048 pixels. Strength 0–64, OpenGL or DirectX green channel convention, wrap or clamp edges. Outputs RGB tangent-space normals with decoded pixel checks. Render in the target engine to verify appearance.

## Generate a height map

```json
{"image":"texture.png","channel":"luma","black":0,"white":255,"gamma":1,"invert":false}
```

Uses the existing bounded PNG/Pillow adapter. Choose grayscale or Rec.709 encoded RGB luma, or an explicit red/green/blue channel. Input levels clamp and normalize, gamma remaps, inversion is optional. Produces an 8-bit grayscale PNG suitable for the normal-map tool. This maps intensity to height; it does not infer real depth from a photograph.

## Automatically unwrap a UV atlas

```json
{"mesh":"model.obj","tile_margin":0.05}
```

Plain triangulated OBJ (v and f statements plus comments), up to 20,000 vertices and triangles. Produces new OBJ with one shape-preserving UV island per triangle, distinct atlas tiles and an explicit 1–25% margin of each tile. Positions and triangle indices are retained. Materials, normals, groups and existing UVs are refused in this initial adapter; seam optimisation and engine rendering remain separate.

## Simplify a static mesh

```json
{"mesh":"model.obj","cell_size":0.1,"max_displacement":0.02}
```

Uses plain triangulated OBJ only. Distances are in source model units. Deterministically cluster vertices, remove collapsed or duplicate triangles, and verify surviving winding and output geometry. A cluster exceeding the reviewed maximum displacement blocks the operation. Topology, materials, normals, UV preservation and full surface-error bounds are not provided; render the output before use.

## Convert a static OBJ to GLB

```json
{"mesh":"model.obj","max_position_error":0.0001}
```

Plain triangulated OBJ with optional complete unit-square UVs. Produces self-contained glTF 2.0 binary geometry with indexed positions and UVs (OBJ V origin flipped for glTF), no axis transform. Explicit Euclidean float32 position tolerance in model units, verified decoded accessors and winding. UV seams duplicate vertices where required. Other file formats, materials, normals, groups and animation are not silently discarded; unsupported statements are refused. Native Blender/Godot import and render still require verification.

## Compose multiple PNG images

```json
{"width":640,"height":480,"background":[20,20,20],"layers":[{"image":"base.png","x":0,"y":0,"width":640,"height":480,"opacity":255},{"image":"overlay.png","x":120,"y":80,"width":320,"height":240,"opacity":180}]}
```

Two to six distinct PNG sources, bottom-to-top order; explicit in-canvas position, size and 1–255 opacity. Single-frame 8-bit L/RGB/LA/RGBA PNG only, maximum 2048 pixels per side, no keyed transparency. Lanczos resizing and source alpha multiplied by layer opacity on an opaque RGB canvas. All source hashes are reviewed; generated pixels are decoded and verified, with no overwrite. This does not establish visual quality or ICC color fidelity.

## Enhance an image

```json
{"image":"source.png","brightness":110,"contrast":120,"saturation":100,"sharpness":130}
```

Explicit integer percentages 0–300; 100 is identity. Fixed order brightness, contrast, saturation, sharpness on encoded RGB; source alpha preserved in RGBA PNG, no ICC conversion. Same bounded PNG inputs as composition. Reviewed source identity, exact decoded output and changed pixel count. This is parameter-driven enhancement, not automatic aesthetic judgment, AI upscaling or restoration.

## Generate an editable vector logo

```json
{"title":"Example","width":320,"height":160,"background":null,"elements":[{"kind":"circle","cx":40,"cy":80,"radius":24,"fill":"#005577"},{"kind":"text","x":80,"y":90,"text":"Example","size":24,"family":"sans","weight":"bold","anchor":"start","fill":"#101010"}]}
```

Ordered 1–32 literal shapes or text; bounded rectangle/circle/polygon geometry, hex fills, optional solid background, three font families and explicit wordmark attributes. No arbitrary SVG, URLs, scripts or external assets. Output is editable and structurally verified; rendered appearance, font fit, design originality and trademark clearance are not established.

## Generate an infographic

```json
{"title":"Project snapshot","subtitle":"Supplied local figures","accent":"#1d697a","source_note":"Source: user-provided figures.","facts":[{"label":"Ships built","value":"120","detail":"Completed hulls in the specified period."},{"label":"Deliveries","value":"456","detail":"Recorded deliveries across all sectors."}]}
```

Two to eight supplied fact cards, fixed responsive-to-count two-column vector layout, explicit source note, bounded literal text and editable SVG. The tool verifies the generated structure and text, not the truth of supplied claims or rendered font fit. Review appearance and evidence independently.

## Batch-process PNG images

```json
{"images":[{"image":"a.png","output":"a-enhanced.png"},{"image":"b.png","output":"b-enhanced.png"}],"brightness":110,"contrast":100,"saturation":100,"sharpness":120,"max_edge":1024}
```

Two to six distinct bounded PNG inputs, shared enhancement settings, optional aspect-preserving maximum edge without upscaling, explicit output names. Verified PNG outputs and a source/output hash manifest are published as one non-overwriting ZIP; no partial publication. Alpha is preserved before resizing; resized alpha is resampled. This does not establish visual quality or model-directed acceptance.

## Trim and sequence silent video

```json
{"fps":24,"clips":[{"video":"scene-a.mp4","start_frame":12,"end_frame":36},{"video":"scene-b.mp4","start_frame":0,"end_frame":24}]}
```

One to four distinct short H.264 MP4 clips, one video stream only (audio or other streams refused), matching dimensions up to 640x480 and matching 24/25/30 fps metadata. Start inclusive, end exclusive; at most 300 source frames and 120 output frames. Installed FFmpeg/FFprobe identity and exact input hashes are reviewed. Re-encode selected decoded RGB frames using lossless H.264 RGB, then decode and compare exact output frames; player compatibility and visual quality still require acceptance. No audio, transitions, retiming or broad codec support.

## Remove an image background

```json
{"image":"source.png","mode":"color_key","key":[0,255,0],"tolerance":20,"feather":40}
```

Or supply a same-dimension 8-bit grayscale PNG mask using `{"image":"source.png","mode":"mask","mask":"mask.png"}` (white retains, black removes, intermediate values multiply existing alpha). Color key uses maximum RGB-channel distance; feather linearly transitions outside tolerance. Original RGB retained, existing alpha multiplied, RGBA output decoded and checked. No semantic object detection, despill or visual quality guarantee.

## Replace an image background

```json
{"foreground":"subject.png","mode":"solid","color":[40,70,100]}
```

Or use `{"foreground":"subject.png","mode":"image","background":"scene.png","fit":"exact"}`. Foreground must have actual transparency (use reviewed removal first); replacement image must be opaque. Exact fit requires matching dimensions, stretch explicitly resizes to fit. RGB alpha composite, source hashes, verified decoded pixels and no overwrite. No automatic segmentation or visual quality guarantee.

## Recognize text in an image (OCR)

```json
{"image":"scan.png","layout":"block"}
```

Bounded local PNG, English Tesseract OCR, block or sparse layout, no network. Install Tesseract with English traineddata separately before use; discovery checks PATH and conventional installation paths. Review pins source, executable stat and exact English model hash; JSON result contains recognized text, per-word boxes and engine confidence. White alpha compositing and single-thread engine. Text is untrusted data, not instructions. No accuracy guarantee, handwriting/multilingual/PDF support or visual acceptance claim.

## Scheduled conversation requests

Queue → Scheduled requests… in an open chat. Choose a new exact prompt and delay in minutes, review its UTC due time and explicitly approve. The persistent schedule is bound to that project and chat. When the app is running and the selected workspace and existing dispatcher are eligible, one due request is atomically inserted into the ordinary conversation queue; it grants no file or tool authority. The queue may be delayed by gaming, pause, model readiness or other work; no background OS service or guaranteed deadline. Closing the chat cancels its unreleased requests. Manage or cancel in the same dialog; use normal chat controls after release.

### Recurring scheduled requests

In the same scheduled-request dialog choose Recurring, enter the first delay, repeat interval (15–525600 minutes) and maximum actual occurrences (2–1000). Confirm the exact prompt and cadence. The next due time remains anchored to the previous due time; missed intervals do not create a backlog. Only one occurrence may be unresolved at a time. A failed or cancelled prior request stops future releases. Cancellation stops future occurrences, not already released conversations. The dialog shows remaining admissions, latest request and recent occurrence history. No OS-level background service, recurring automatic tool approval or execution deadline is implied.

## Website change monitoring

Queue → Website monitors. Approve an exact lowercase public HTTPS DNS URL without credentials, query, port or fragment, 15 minutes–7 days between checks and 2–1000 total attempts. The app compares SHA-256 of exact uncompressed HTML/plain response bytes; even dynamic markup may count as a change. The first successful check establishes a baseline; failed checks do not replace it. Only public IPv4 DNS answers are accepted and a pinned address is used with TLS hostname verification; no redirects, proxies, cookies or page execution. Only hashes, sizes and status are retained. Checks are finite, run while the app is available, obey pause/gaming gates and are cancelled on closing the bound chat. No model or tool authority is granted. The Processes log reports changes; history is visible in the dialog. Live remote and native GUI acceptance remain outstanding.

## Monitor user-defined project-file conditions

Queue → Condition watches in a project chat. Choose an exact workspace-relative regular-file path, predicate (`exists`, `missing`, `size_at_least` with byte threshold, or `sha256_equals` with exact lowercase digest), check interval of 1 minute–7 days and 2–1000 attempts. Explicit confirmation is required. Inspection exclusions, linked and protected paths are refused; optional hashing is limited to 16 MiB. Observations record only existence, size, optional hash and predicate truth; no file body is retained or passed to an AI. First successful check establishes baseline; later changes record became_true/became_false, while errors preserve prior truth. Runs in the app with gaming/pause gates and is cancelled on chat close. No arbitrary scripts, additional execution authority or system-level always-on service.

## Event-triggered follow-up workflows

Queue → Event-triggered requests. Select an active monitor in the bound chat and a future website `changed` or condition `became_true`/`became_false` event. Review the exact prompt and choose 1–1000 actual follow-up admissions. Old events are not replayed. Multiple missed matching events coalesce to the latest recorded event, and the previous conversation must respond before another is admitted. A cancelled/failed previous request or cancelled source stops the rule. Event metadata is appended as reference data only. The existing dispatcher, workspace, gaming/pause and approval boundaries remain; no automatic file or tool execution authority is granted. History records the exact originating event and resulting request. Closing the chat cancels outstanding rules. Native desktop/model acceptance remains outstanding.

## Interpret supplied search-engine results

```json
{"query":"quartz engine calibration","results":[{"title":"Manual","url":"https://example.org/manual","snippet":"Quartz calibration reference"}]}
```

Use Interpret search results in Files & Images. Up to 20 supplied rows (zero is valid); exact provider ranks preserved, duplicate URLs omitted, query term coverage and title match tie-breaker computed, and missing query terms plus hostname counts reported. No network call or semantic/factual verification. The output is reference data, not instructions or authority. Actual search and page reading are separate abilities.

## General internet search (optional Brave Search API)

Files & Images → Search internet. Enter the exact public query and 1–20 results, confirm the single outgoing request, then enter your provider key in a masked dialog. The key is transient, never written to disk, model prompts or application logs. Uses the fixed `https://api.search.brave.com/res/v1/web/search` endpoint, public IPv4 pinning and TLS verification; no cookies, redirects, arbitrary URLs or project data are transmitted. An active Brave API account is required and provider charges/terms may apply. Results are shown as untrusted reference data in the dialog, not treated as opened pages or verified facts. Optional clipboard export of supplied-result JSON requires confirmation and provider retention rights; no automatic persistent storage. Local inference remains unchanged. Live provider acceptance and model-selected research integration remain outstanding. API reference: https://api-dashboard.search.brave.com/api-reference/web/search/get

## Retrieve a public webpage

```json
{"url":"https://example.org/manual"}
```

Files & Images → Retrieve webpage. Review the exact outgoing HTTPS request and new JSON output. Accept public lowercase DNS hostnames on default HTTPS port without query, credentials or fragment. Pin a public IPv4 result, verify TLS hostname, refuse redirects, compressed/non-text or oversized responses. Parse static HTML/plain text, excluding script/style/template and other hidden container bodies; list up to 100 discovered display-only links without following them. Report original URL, response and text SHA-256, extracted text and title. Body cap 512 KiB, text cap 100000 characters; no partial/truncated page claimed. No browser rendering, authentication, subresources, page execution or independent factual verification. Live network and native acceptance outstanding.

## Discover online image candidates

```json
{"query":"quartz landscape","count":6}
```

Files & Images → Discover images. Approve the exact Wikimedia Commons query and new JSON report. Finds up to six provider-declared CC0 or CC BY JPEG/PNG candidates within the existing size and dimension limits; report includes title, creator, source and download URLs, license, attribution requirement and provider hashes. No image download or automatic reuse; source-page licensing and other rights must be reviewed independently. Pinned public IPv4 TLS, fixed provider endpoint, bounded JSON and no redirects. Live provider and native acceptance pending.

## Check scientific citation metadata

```json
{"doi":"10.1234/example","title":"Example paper","first_author_family":"Smith","year":2025}
```

Files & Images → Check DOI citation. Approve one DOI lookup against Crossref and a new JSON output; only the bare DOI leaves the computer. Compare supplied title, first listed author's family name and issued year with registered fields. Missing fields are unavailable, not proof of mismatch; a failed request or non-Crossref DOI proves nothing about validity. Metadata agreement does not verify scientific conclusions, full text, retractions or peer review. Source: https://www.crossref.org/documentation/retrieve-metadata/rest-api/ . Live provider and native acceptance pending.

## Discover academic literature

```json
{"query":"quartz engine calibration","count":10,"from_year":2020,"to_year":2025}
```

Files & Images → Discover academic literature. Approve one exact bibliographic query and optional year bounds (null means unbounded) sent to Crossref. Up to ten provider-ranked bibliographic records with exact DOI, title, first author family, issued year, publication, publisher and response hash; duplicates or unusable rows omitted and counted. Provider total is not the number retrieved. Issued-year differences from requested publication filters are flagged rather than silently corrected. No full text, systematic-review completeness, peer-review, retraction or claim verification. Crossref public API; no API key required for public access, but availability/rate limits apply. Live and native acceptance outstanding. Reference: https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/

## Crawl a bounded website directory

```json
{"seed":"https://example.org/docs/","path_prefix":"/docs/","max_pages":5,"max_depth":2}
```

Files & Images → Crawl website. Approve exact seed, same-host directory prefix, up to five page attempts and depth 0–2; robots.txt is fetched separately. Requires successful plain-text robots response; conservative disallow rules override allows. At least two seconds between attempts, respecting supported longer crawl delays up to ten seconds. No query/encoded paths, external origins, redirects, scripts, credentials, or complete-site claim. Retain exact page text and hashes, referring URL, attempts and denied/remaining counts. Bounded cooperative time budget; OS DNS/socket blocking is not a hard wall-clock guarantee. Live/native acceptance outstanding.

## Collect multiple research sources

```json
{"question":"Quartz engine calibration","urls":["https://example.org/manual","https://example.net/reference"]}
```

Files & Images → Collect research sources. Approve 2–5 exact public HTTPS URL reads; the question is used only locally. New JSON contains each attempted source (including unavailable ones), exact static page text/hashes, up to five lexical excerpts per source with one-based line and zero-based character start, and a query-term matrix excluding identical-text duplicates. Different hosts or text do not prove independent sources; lexical overlap is not semantic or scientific claim support. No links followed, scripts, authentication, or claim of complete research. Live/native and model integration acceptance pending.

## Assess source credibility signals

```json
{"research":"research.json","findings":[]}
```

Files & Images → Assess source credibility. Select a previous multi-source research report. Rebuild and verify its derived evidence fields and text hashes; this establishes internal consistency, not signed provenance. Report literal source-transparency cues for authorship, date, references, methodology, funding/conflicts and corrections with exact line and offset; absent cues are not proof of absence. Optionally supply findings with `source_id`, `dimension`, `assessment` (`supports_credibility`, `raises_concern`, `unclear`), one-based `line`, zero-based `start`, exact `quote` and `reason`. Dimensions: `authorship`, `publication_date`, `references`, `methodology`, `conflicts_funding`, `corrections`. Reviewer quotes must match the retrieved evidence, but judgments are not independently verified. Duplicate and unavailable sources are explicitly flagged. Offline; no aggregate credibility score or claim verification. Native/model acceptance pending.

## Compare contradictory source positions

Use Compare contradictory sources with a JSON specification containing `research` (path to the multi-source report) and `claims` (1–12 objects: `id`, `claim`, `context`, `observations`). Each observation contains `source_id`, `position` (`supports`, `opposes`, `qualifies`, `unclear`), one-based `line`, zero-based `start`, exact `quote`, and `reason`. Require 2–5 distinct source observations per claim, verify every quote, and preserve source URL and text hash. Pairwise comparison separates reported disagreement, qualification, unclear positions and duplicate evidence. Claims remain unresolved where opposition is recorded; no vote or automatic truth determination. No independent semantic contradiction detection. Offline reviewed output; native/model acceptance pending.

## Generate a research report

Use Generate research report with `research` (multi-source evidence JSON path), `title`, `sections` (objects with `heading` and `paragraphs`) and `limitations` (nonempty list of text). Each paragraph is an object with `text` containing `[[S1]]` etc. and `evidence` (objects with `source_id`, one-based `line`, zero-based `start`, exact `quote`). Every paragraph requires at least one retrieved source and all citation markers must match supplied evidence. Quotes are verified against the exact input report. Output is standalone escaped HTML with internal citation anchors, evidence quotes, limitations, source register and input hashes. Supplied prose is not automatically verified or independently generated. Offline; no scripts or remote resources. Native/model acceptance pending.

## Train local latent semantic vectors

Use Train local semantic vectors with `documents` (4–32 distinct objects with `id` and `text`, up to 4000 characters each), `query`, `dimensions` (2–16, less than corpus size) and `top_k`. Fit a local TF-IDF corpus matrix and truncated SVD using a bounded symmetric Gram eigensolver, verifying eigenpair residuals and basis orthogonality. Export vocabulary, IDF, fitted basis, normalized document/query vectors and cosine-ranked IDs, with corpus and text hashes. Unknown query terms are flagged; unprojectable queries fail rather than inventing matches. This is corpus-trained latent semantic analysis, not a pretrained contextual model or proven general semantic relevance. No network or new permanent AI model; memory integration/native acceptance pending.

## PDF diagram geometry (Pass 085)

Files & Images → Interpret PDF diagram geometry. JSON: `{"document":"diagram.pdf","pages":[1]}`. Existing pinned PDF production tools required. Up to eight distinct pages of a supported 4 MiB PDF. Results identify labelled rectangular vector nodes and straight-line connector candidates, with no inferred direction, semantic conclusion or raster diagram interpretation.

## PDF layout inspection (Pass 086)

Files & Images → Inspect PDF layout. JSON: `{"document":"manual.pdf","pages":[1,2]}`. Reuse pinned PDF production tools. Reports page boxes, text segments, fonts and sizes, image boxes, rotation and text/image margin estimates, with top-origin point coordinates. Segments are geometric candidates, not a verified reading order; vector drawings are counted but excluded from text/image margin estimates.

## Contract and policy evidence (Pass 087)

Files & Images → Review contract or policy. JSON: `{"document":"terms.pdf","topics":["obligations","termination","privacy"],"custom_checks":[{"id":"access","label":"Access review","phrases":["access log"]}]}`. Other topics: prohibitions, payment, renewal, liability, disputes. TXT/MD/DOCX/PDF sources; PDF extracted page/line locators and missing-text pages retained. Literal matches only; not a legal opinion, compliance assessment or proof of absence.

## PDF raster quality checks (Pass 088)

Files & Images → Check PDF rendered pages. JSON: `{"document":"report.pdf","pages":[1,2],"minimum_margin_points":12,"allow_blank_pages":false}`. Actual 96-DPI local rendering with the existing PDF production tools; reports visible ink bounds, measured margins, blank-page warning and pixel hash. Intentional full-bleed artwork may violate the requested margin. This is not a general visual quality or clipping guarantee.

## Predictive modelling (Pass 089)

Files & Images → Fit predictive model. JSON: `{"csv":"data.csv","delimiter":",","predictor":"x","target":"y","train_rows":4,"missing_tokens":["NA"],"predict_values":["2","10"]}`. Train one-predictor exact ordinary least squares on the specified first data rows; evaluate the untouched suffix. Complete cases only, exact coefficients and held-out metrics against training-mean baseline. Predictions outside the training predictor range are flagged. Not a general-purpose machine-learning or causal inference system.

## Exact scientific computing (Pass 090)

Files & Images → Scientific calculation. Either `{"operation":"solve_linear_system","matrix":[["2","1"],["1","-1"]],"rhs":["7","2"]}` or `{"operation":"integrate_polynomial","coefficients":["1","2","3"],"lower":"0","upper":"2"}`. Exact rational strings, bounded 16-square systems and 32 polynomial coefficients in ascending powers. Unique solutions checked by substitution; integration checked by a second computation and differentiation. No physical simulation or arbitrary code execution.

## Numeric anomaly candidates (Pass 091)

Files & Images → Flag numeric anomalies. JSON: `{"csv":"data.csv","delimiter":",","column":"value","baseline_rows":4,"missing_tokens":["NA"],"iqr_multiplier":"1.5"}`. Derive exact quartile fences from the specified baseline prefix, flag values in the separate monitoring suffix, preserve row identities and missing counts. Constant/zero-IQR baselines can be oversensitive. No data is removed or modified.

## Time-series forecasting (Pass 092)

Files & Images → Forecast time series. JSON: `{"csv":"series.csv","delimiter":",","date_column":"day","value_column":"v","train_rows":4,"horizon":2,"season_length":2}`. Exact increasing ISO dates at constant day intervals, complete numeric values, explicit training prefix. Compare last-value, seasonal-naive and drift on the held-out suffix; select by MAE and refit on all observed values. No independent final accuracy estimate or uncertainty intervals.

## Jupyter notebook export (Pass 093)

Files & Images → Export Jupyter notebook. JSON: `{"cells":[{"id":"intro","kind":"markdown","source":"# Experiment"},{"id":"analysis","kind":"code","source":"print(2 + 2)"}]}`. Creates an unexecuted .ipynb v4.5 document for a Python 3 kernel. Python syntax is checked but code is not executed or declared safe. No local kernel required for export; interactive kernel, execution and output capture are outstanding.

## Live local SQLite (Pass 094)

Files & Images → Query live SQLite. Same JSON fields as the immutable SQLite query (`database`, `query`, `parameters`, `max_rows`), but explicitly reads current committed contents of the reviewed file identity, not a frozen hash. Uses read-only SQLite mode and the existing query authorizer; active WAL requires existing WAL and SHM files, which SQLite may use for its read locks. No database content writes, remote drivers, credentials or persistent connection pool.

## API contract development (Pass 095)

Files & Images → Create API contract. Source JSON has `title`, `version`, `endpoints`: each endpoint includes `path`, lowercase `method`, `id`, `summary`, `request`, `response`, integer `status`. Request/response are arrays of `{name,type,required}` fields (`string`, `integer`, `number`, `boolean`). Creates an OpenAPI 3.1 JSON contract with no running server, authentication, network request or implied implementation.

## Local API testing (Pass 096)

Files & Images → Test local API. JSON: `{"port":8080,"cases":[{"id":"health","path":"/health","status":200,"json_fields":{"ready":true}}]}`. Sends one GET per reviewed case to a running service on 127.0.0.1 only. No redirects, credentials, external network or JANUS control port. Tests status and exact typed JSON scalar fields. Records body hash and timing, not raw response bodies. GET endpoints should be read-only; review the target service before approving.

## Live application health sampling (Pass 097)

Files & Images → Sample application health. JSON: `{"port":8080,"path":"/health","expected_status":200,"json_fields":{"ready":true},"samples":3,"interval_seconds":1,"max_latency_ms":100}`. Two to eight sequential local GET observations with timestamps, status, typed JSON checks and latency threshold. Reports partial observations if the sampling deadline is reached. No persistent monitor, alerts, automatic recovery or service startup.

## Additive SQLite migrations (Pass 098)

Files & Images → Migrate SQLite snapshot. JSON: `{"database":"old.db","from_version":0,"to_version":1,"steps":[{"operation":"add_nullable_column","table":"items","column":"notes","type":"TEXT"},{"operation":"create_index","table":"items","name":"items_notes","columns":["notes"]}]}`. New `.db` only; exact standalone snapshot with no WAL/journal, increment by one, bounded additive operations, schema/integrity/foreign-key and row-count checks. Source retained as rollback copy; no live migration or application compatibility guarantee.

## Local Python language server (Pass 099)

Files & Images → Inspect Python language server. JSON: `{"document":"src/module.py"}`. Real bounded JSON-RPC/LSP stdio lifecycle using the bundled Python AST language server. Syntax diagnostics and direct class/function symbols, nested where directly declared; UTF-16 positions. No execution/imports, external language servers, type checking, completion or project-wide references.

## Documented application interface learning (Pass 100)

Files & Images → Learn documented API interface. JSON: `{"document":"openapi.json"}`. Reads exact local OpenAPI 3.0/3.1 JSON and exports bounded operation, parameter, request/response field and security-presence evidence with JSON pointers. Reference resolution, runtime verification, GUI discovery and autonomous adoption of API recipes remain outstanding. No credentials, calls or network access.

## Python local refactoring (Pass 101)

Files & Images → Refactor Python local name. JSON: `{"document":"source.py","function":"compute","old_name":"total","new_name":"result"}`. One unique top-level undecorated function, locally assigned name only, conservative scope and collision restrictions; UTF-8/LF source without BOM. Exact source offsets and full module AST comparison; new `.py` file, never overwrite or execute original. AST equality under the intended rename is not proof of runtime equivalence.

## Automated debugging evidence (Pass 102)

The existing read-only agent diagnostics tool additionally resolves Python traceback frame paths and line numbers against the current indexed project. Returns exact current source hashes and bounded source lines, not a guessed root cause or failure-time source identity. No external path reads, execution or edits. Agent evidence revalidation rejects stale source.

## GitHub draft pull request (Pass 103)

Files & Images → Create GitHub draft PR. Enter existing remote branches, repository and title/body; approve exact outgoing request and enter a transient GitHub token with pull-request write permission. A successful provider receipt must match repository and refs. No branch push, merge, local source upload or saved token. Remote write may have succeeded despite a lost response; inspect GitHub rather than retry automatically.

## GitHub draft release (Pass 104)

Files & Images → Create GitHub draft release. Enter repository, existing lightweight tag, exact 40-character commit SHA, title and notes. Approve the exact GET tag check and one POST to create a draft. Transient masked token requires contents write permission. No publication, tag creation, asset upload or automatic retries. Tag may change after the check; inspect remote before publishing separately.

## Windows installer project source (Pass 105)

Files & Images → Generate installer project. JSON: `{"app_name":"Example App","app_id":"Example","version":"1.2.0","files":["bin/app.exe","data/info.txt"],"entrypoint":"bin/app.exe"}`. Generates a new Inno Setup `.iss` source, one to six exact payload hashes (existing queue guard limit; each file at most 32,000,000 bytes), per-user destination, Start Menu shortcut, no automatic launch or Pascal code. Compiler and separate install/uninstall acceptance remain required; no actual installer is produced by this operation.

## GitHub pull request review evidence (Pass 106)

Files & Images → Inspect GitHub PR. Enter repository, PR number, exact head/base SHAs, and transient pull-request read token after approval. Retrieves up to 30 changed-file records and bounded provider patches, rechecks metadata, labels omitted patches and path-based review cues. No semantic finding, test proof, atomic remote snapshot, approval, comment or merge. Larger changes require a different reviewed workflow.

## Git three-way conflict proposal (Pass 107)

Files & Images → Propose clean merge. JSON: `{"path":"source.txt"}`. Requires Git root and actual unmerged index entries 1/2/3 for one ordinary same-mode text file. Native git merge-file must produce a clean nonempty result; overlapping conflicts are refused, not guessed. Review exact candidate and stage hashes; publish new `.txt` only. Separate reviewed application/staging needed.

## GitHub OAuth device connection (Pass 108)

Files & Images → Connect GitHub account. Supply your own registered GitHub OAuth public client ID with device flow enabled. Approve read:user scope, manually open the fixed GitHub device page and enter the displayed code after verifying application identity. Account identity is verified via /user. Transient local session expires after 15 minutes, may be disconnected or explicitly reused for read-only PR evidence where provider permissions allow. No repository write scope, saved token, refresh token, provider revocation or bundled OAuth client. Live provider acceptance outstanding.

## Remote MCP discovery (Pass 109)

Files & Images → Discover remote MCP. JSON: `{"url":"https://mcp.example.com/mcp"}`. Explicit public HTTPS initialize, initialized notification and bounded tools/list JSON requests. Uses existing typed schema summaries and hashes. No credentials, SSE, arbitrary tool calls, prompts or resources. Output is historical discovery evidence, not permission to execute.

## Public REST integration (Pass 110)

Files & Images → Reviewed REST request. JSON: `{"url":"https://api.example.com/items","method":"GET","query":{"q":"example"},"body":null}` or POST with explicit JSON object body. Review all outgoing data: field-name checks are not comprehensive secret detection. Fixed public HTTPS destination, no credentials, redirects, retries or uploaded files. Bounded JSON receipt and HTTP status; POST can change remote state. Inspect remote before repeating an uncertain request. No authenticated acceptance yet.

## Windows credential management (Pass 111)

Existing GitHub review/draft dialogs offer separately approved Windows Credential Manager save/replace, retrieve and forget for one exact repository and operation. No enumeration, plaintext fallback, OAuth persistence or automatic use. Local deletion does not revoke provider access; other processes under your Windows account may access the credential. Use narrowly scoped provider tokens.

## JSON tool factory (Pass 112)

Files & Images → Generate JSON tool. JSON: `{"name":"normalise","fields":[{"source":"label","target":"name","operation":"trim"}],"fixtures":[{"input":{"label":" A "},"expected":{"name":"A"}}]}`. Generates new standalone Python source for a bounded JSON scalar mapping (copy, trim, lower, upper). The reference operations check expected fixtures and generated source compiles; actual tool execution and registration are separate. No arbitrary command, network or file operations.

## Public GitHub account inventory (Pass 114)

Files & Images → GitHub public repositories. Connect the existing transient OAuth session, select page 1–10 and approve identity verification plus a bounded public owned-repository page. Returns repository ID, exact name, default branch and flags only. No private repository enumeration, clone, scope change or remote mutation. Page is not a complete account inventory.

## Local signed webhook receiver (Pass 115)

Files & Images → Receive local webhook. Enter exact event type and dedicated test secret, approve one delivery for up to 60 seconds. Send a local JSON POST to the displayed 127.0.0.1 endpoint with X-GitHub-Event, X-GitHub-Delivery UUID and X-Hub-Signature-256 HMAC over raw bytes. Only receipt metadata and body hash retained in the dialog. No public listener, task submission, persistent replay protection or claim of actual GitHub origin.

## Local OpenAI-compatible developer gateway (Pass 116)

Files & Images → Local developer API. Explicitly approve temporary loopback session; use the displayed base URL and separate ephemeral key. Supports GET /v1/models and POST /v1/chat/completions with model `deepthort-triad`, messages, max_tokens and stream=false. Two inference attempts, 120-second admission window; already-admitted inference may continue after cancel. No streaming, role override, tool calls, usage counts, persistent chat, external bind or internal broker key disclosure. Native model/SDK acceptance remains outstanding.

## Local developer status API (Pass 117)

The temporary developer gateway can separately authorize GET /janus/v1/status for the exact selected project/chat. Up to 50 latest jobs and conversation requests per store, IDs/modes/states only, same temporary key. No prompts, files, paths, actions, startup recovery, cross-scope access or atomic cross-store snapshot. Disabled unless explicitly approved; changes of project/chat close admissions.

## Headless client (Pass 118)

After approving a temporary developer session in the desktop, run `python janus_cli.py --port PORT models`, `status` (if separately enabled), or `chat --max-tokens 128` with a bounded UTF-8 prompt on stdin. Supply the temporary client key through masked input or JANUS_DEVELOPER_KEY, never a command-line argument. JSON result on stdout; failures use nonzero status and no automatic retry. Desktop remains the authority and capped model host; this does not start a standalone headless agent.

## External task review inbox (Pass 119)

Optionally enable POST /janus/v1/tasks on the temporary local developer gateway. Body: `{"submission_id":"canonical-lowercase-uuid","prompt":"exact requested task"}`. A 202 receipt means awaiting local owner review, not a queued job. At most two distinct items per session; review the exact prompt in the desktop before creating an ordinary conversation in the selected project/chat. No automatic build, attachment, tools, remote bind or persistent replay ledger. Unreviewed items are discarded on close or scope change.

## Cross-device status notification (Pass 120)

Files & Images → Status notification. Select one existing job or conversation ID in the current project/chat. Provide a dedicated private ntfy.sh topic and access token, explicitly approve the possible generic terminal-state messages. A finite five-minute watch sends at most one HTTPS JSON POST when a terminal state is observed. The message excludes ID, paths, prompts and results; token is not persisted. Configure topic access and receiving-device subscription independently. Provider caching may apply. Provider acceptance is not device-delivery proof. Protocol: https://docs.ntfy.sh/publish/ .

## Microphone recording (Pass 121)

Files & Images → Record microphone. Select a project, approve a 1–30 second recording of the Windows default input device. Capture is local 16 kHz mono PCM16 with visible recording and cancellation. Afterwards separately approve a new project-relative WAV in an existing folder; cancel discards the recording. Protected, linked and existing targets refused. No automatic upload, playback, transcript or model ingestion. Physical microphone acceptance requires a Windows desktop with an available device.

## Offline short speech-to-text (Pass 122)

Files & Images → Speech to text. Review an exact project-relative 1–30 second mono 16 kHz PCM16 WAV, choose an exact installed desktop recognition culture, approve offline dictation. The fixed System.Speech adapter runs under the capped native process. Preview text is unverified and never automatically submitted or saved. Missing or ambiguous installed recognizer is a blocker; no cloud or substitute language. Native recognition accuracy requires real speech acceptance.

## Offline audio transcription (Pass 123)

Files & Images → Transcribe recording. Approve an exact project WAV (1–120 seconds, mono 16 kHz PCM16) and installed recognizer culture. Balanced windows of at most 30 seconds produce global segment timings, recognizer confidence and per-window status. Preview then separately approve JSON publication to a new project path. Speech at window boundaries may be missed. No automatic chat submission, speaker identification, diarisation or upload. Native accuracy remains unverified.

## Optional neural speech (Pass 124)

Files & Images → Neural speech. Select a trusted separately installed Piper 1.3+ piper.exe and matching single-speaker ONNX voice/config outside the project. Review exact hashes, text, length/noise/noise-width controls and new WAV output. Runs only under existing Windows resource cap and a nested 512 MiB child. No download, fallback or voice cloning. Review engine/voice licenses. Job Object limits are not a security sandbox. Native compatibility and listening quality unverified. CLI reference: https://github.com/OHF-Voice/piper1-gpl/blob/main/src/piper/__main__.py .

## Multilingual speech (Pass 125)

Files & Images → Multilingual speech. Discover installed offline voices, then select a project JSON with `segments` (1–8 rows, each `culture`, exact `voice_id`, `text`) and `pause_ms` (0–2000). Review exact source/voice identities and new WAV output. Per-segment capped Windows synthesis, verified WAVs, combined 22050 Hz mono PCM16 output with timing receipts. Text is supplied by the owner; no translation, fallback language, voice cloning or claimed neural synthesis. Native pronunciation requires listening.

## Scripted podcast generation (Pass 126)

Files & Images → Podcast generation. Review JSON containing `title`, `description`, `pause_ms` and 3–8 `turns` with `section` (intro, body, outro in order), `speaker`, `culture`, exact installed `voice_id`, and `text`. Up to four named scripted speakers, stable distinct voice assignments. Output is one new ZIP with `episode.wav`, `episode.json`, and `transcript.txt`; timing is measured from generated PCM. No automatic script writing, music, upload or publishing. Listening quality remains unverified.

## Short audiobook production (Pass 127)

Files & Images → Audiobook generation. Review JSON with `title`, `author`, `culture`, exact installed `voice_id`, `pause_ms` and `chapters` containing `title` and `passages` arrays. Maximum six chapters, twelve passages, 6000 characters and 300 seconds total speech. Output new ZIP containing numbered chapter WAVs, `book.json` with measured timings and hashes, and `manuscript.txt`. No auto-publication or claimed listening quality; this is a short manuscript workflow, not yet a full-length resumable audiobook pipeline.

## Multi-speaker dialogue production (Pass 128)

Files & Images → Multi-speaker dialogue. Review JSON with `title`, `description`, `pause_ms` and 2–8 `turns` containing `speaker`, `culture`, exact installed `voice_id`, and `text`. Two to four distinct scripted speaker labels with stable, distinct installed voices; no podcast section constraints. New ZIP with `dialogue.wav`, `dialogue.json` and `transcript.txt`, including measured cue timings. No identification of recorded speakers or voice cloning; no autonomous script writing or online publication. Native listening acceptance outstanding.

## Anonymous speaker diarisation (Pass 129)

Files & Images → Anonymous speaker diarisation. Select a local 1–120 second mono PCM16 16 kHz WAV, trusted installed `sherpa-onnx-offline-speaker-diarization.exe`, segmentation and embedding ONNX models, expected count 2–8 or -1 for estimate, and new JSON. Exact hashes reviewed. CPU-only bounded optional tool (512 MiB ordinary auxiliary child ceiling) using [upstream documented CLI](https://k2-fsa.github.io/sherpa/onnx/speaker-diarization/index.html). Per-recording anonymous labels and intervals only, including possible overlapping speakers; no individual identification, enrollment, persistent voiceprint storage or separated WAVs. Native accuracy remains unverified. Resource caps do not sandbox untrusted binaries; the owner must install compatible trusted licensed tools and models separately.

## Reviewed audio restoration (Pass 130)

Files & Images → Restore audio. JSON keys: `audio` (project-relative mono/stereo PCM16 WAV, 3–120 seconds), `remove_dc` (boolean), `hum_hz` (0, 50 or 60), and `click_threshold` (0 or 2000–32767 PCM units). At least one operation required. Conservative isolated sample interpolation, mean DC removal and optional Q30 notch; one shared gain only if needed to avoid clipping. Exact reviewed input, new WAV, format/frame roundtrip and repair counts. This may modify wanted audio; does not recover clipped/missing audio or guarantee perceptual improvement. Listening acceptance outstanding.

## Stereo spatial source isolation (Pass 131)

Files & Images → Isolate stereo component. JSON keys: `audio` (project-relative 3–20 second stereo PCM16 WAV, 8–48 kHz), `component` (`center`, `side`, `left`, or `right`). New ZIP with `selected.wav`, `residual.wav` and `manifest.json`. Exact sample reconstruction verified without clipping; spatial extraction only, not semantic separation. Center is not necessarily vocals; side is not necessarily accompaniment. Native listening and general source separation outstanding.

## Musical stem separation (Pass 132)

Files & Images → Separate musical stems. Select a 3–15 second stereo PCM16 44.1 kHz WAV, trusted installed `sherpa-onnx-offline-source-separation.exe`, official [UVR_MDXNET_1_9703.onnx](https://github.com/k2-fsa/sherpa-onnx/releases/tag/source-separation-models) (exact upstream size and SHA-256 pinned), and a new ZIP. CPU-only, one thread, existing 512 MiB ordinary auxiliary limit; fail closed if the engine cannot fit. Outputs `vocals.wav`, `accompaniment.wav` and `manifest.json`, with exact frame alignment and reconstruction error measurement. Native execution and semantic/listening quality unverified. No automatic installation or download, no individual identification or extra instrument stems. Owner must install compatible trusted licensed tool/model separately.

## Instrument isolation (Pass 133)

Files & Images → Isolate instrument. Choose a 3–8 second stereo 44.1 kHz PCM16 WAV, trusted installed `demucs.cpp.main.exe`, `ggml-model-htdemucs-6s-f16.bin`, target `drums`, `bass`, `guitar` or `piano`, and new ZIP. The [upstream single-model CLI](https://github.com/sevagh/demucs.cpp) writes six IEEE float32 stems; all must be finite and frame-aligned. Target and sum of other stems share headroom before PCM16 export. Exact executable/weights SHA-256 reviewed, not an independently pinned distribution. Existing 512 MiB ordinary auxiliary cap may reject this engine; native compatibility and isolation quality unverified. No automated downloads or cap increases.

## Reviewed audio-to-MIDI (Pass 134)

Files & Images → Audio to MIDI. JSON keys: `audio` (project-relative mono PCM16 8/16 kHz WAV, 3–20 seconds), `bpm` (40–220), `min_pitch` and `max_pitch` (ordered MIDI notes 36–84), `gate_dbfs` (-65 to -20). Bounded YIN-style pitch estimation produces timed single-track MIDI with rests, exact byte roundtrip and explicit tempo. No automatic tempo inference, chords, polyphonic recognition, articulation reconstruction or claimed real-recording accuracy. Existing model-composed MIDI route unchanged.

## Reviewed musical arrangement (Pass 135)

Files & Images → Arrange music. JSON keys: `bpm` (40–220), `parts` (1–8 objects with `name`, `program` 0–127 General MIDI, and `notes` lists of `[start_tick,duration_ticks,pitch,velocity]`, 480 ticks/quarter). At most 512 notes, sorted by start/pitch; overlapping distinct pitches allowed, overlapping same pitch within a part rejected. New `.mid` format 1 with conductor and separate channels; exact decode verification. This is explicit arrangement assembly, not autonomous harmony or aesthetic acceptance. Legacy Gemma MIDI generation unchanged.

## Instrumental audio synthesis (Pass 136)

Files & Images → Synthesize instruments. JSON keys: `midi` (canonical JANUS `.mid`/`.midi`), `voices` (one per part, objects with `timbre` = sine/organ/pluck/strings/bass, `gain_db` -36 to 0, `pan` -1 to 1), `peak_dbfs` -18 to -1. Render up to 30 seconds and 2 million total note samples to new stereo 22.05 kHz PCM16 WAV, respecting timing, rests and velocities. Deterministic synthetic timbres, not General MIDI samples or neural instrument realism. Shared peak attenuation, no boost. Exact decoded PCM verification; listening acceptance outstanding.

## Automated audio mixing (Pass 137)

Files & Images → Auto-balance mix. JSON keys: `tracks` (2–6 distinct project-relative `audio` WAV paths, `offset_ms` 0–10000, `trim_db` -24 to 6, `pan` -1 to 1), `target_rms_dbfs` -36 to -12, `max_boost_db` 0–12, `peak_dbfs` -12 to -1. Mono/stereo PCM16 inputs with matching 8–48 kHz rate, 3 seconds minimum each and 30 seconds maximum output. Whole-track RMS gain auto-balance with explicit trim, stereo balance or mono pan, offset and shared peak ceiling. Near-silent tracks rejected. New verified stereo WAV; no perceptual loudness, automatic EQ/compression or listening acceptance claim.

## Automated audio mastering (Pass 138)

Files & Images → Master audio. JSON keys: `audio` (mono/stereo PCM16 WAV, 3–30 seconds, 8–48 kHz), `threshold_dbfs` -36 to -6, `ratio` 1–8, `attack_ms` 1–100, `release_ms` 20–500, `target_rms_dbfs` -30 to -10, `max_boost_db` 0–12, `peak_dbfs` -12 to -1. Linked peak-envelope compression, bounded RMS makeup and shared sample-peak attenuation. The target RMS may be missed to preserve headroom. New verified PCM WAV, original unchanged. No LUFS, true-peak, spectral EQ, listening or professional-mastering claim.

## Reviewed planar retopology (Pass 139)

Files & Images → Improve topology. JSON keys: `mesh` (plain triangular OBJ without UV, normals, materials or rig), `passes` (1–5), `min_quality_gain` (0.0001–0.25). Up to 10,000 faces; consistently wound manifold edge and vertex fans required. Deterministic planar interior edge flips improve the minimum normalized triangle quality of the pair, preserving positions and exact boundary. Report no eligible flip when applicable. Not quad remeshing, curved remeshing, animation retopology or rendering acceptance.

## Blender mesh workflow (Pass 140)

Files & Images → Create editable Blender mesh. Select strict project-relative triangular OBJ (up to 10k vertices/faces), trusted installed `blender.exe` outside project, and new `.blend` path. The exact executable and fixed bundled Python script are reviewed; private geometry JSON is quantized to Blender float32. Factory-startup, disabled autoexecution, one thread, bounded child process; script creates one mesh, saves uncompressed and reopens it to compare exact vertices/faces. No arbitrary scripts or project-supplied blend files. Actual installed Blender compatibility within 512 MiB and visual quality unverified.

## Reviewed automatic mesh repair (Pass 141)

Files & Images → Repair mesh. JSON specification contains only `mesh` (project-relative plain triangular OBJ). Up to 10,000 vertices and faces. Exact-coordinate weld, remove degenerate and duplicate triangles and unused vertices, orient adjacent faces consistently, reject unresolved nonmanifold edges/fans or nonorientable components. Reports remaining boundary edges and verifies geometry. No arbitrary scripts, tolerance welding, hole filling, self-intersection repair, outward orientation or attribute preservation. Native visual acceptance outstanding.

## Reviewed parametric CAD (Pass 142)

Files & Images → Parametric CAD. JSON keys: `polygon` (3–128 distinct strictly convex counterclockwise `[x,y]` millimetre coordinates, absolute value ≤10,000), `height_mm` (0.01–10,000). Produces new ZIP with editable `design.scad`, independently generated `design.obj` and `receipt.json`; closed manifold and analytical volume checked. No arbitrary code, native OpenSCAD or FreeCAD execution, CSG, complex surfaces, manufacturing or STEP acceptance.

## Reviewed 3D scene composition (Pass 143)

Files & Images → Compose 3D scene. JSON keys: `objects` (1–6 entries, each with distinct ASCII `name`, project-relative `mesh` OBJ, three-number `translation` within ±10,000, normalized `rotation_xyzw` quaternion, positive three-number `scale` 0.001–1000), `max_position_error` (1e-12–1 local units). Reuse existing OBJ conversion, retain local UVs when complete, emit one self-contained GLB with separate mesh nodes and independently checked local geometry segments. No materials, lights, collision, animation or rendering verification.

## Reviewed automatic lighting (Pass 144)

Files & Images → Auto-light 3D scene. Use Pass 143 scene specification plus `view_azimuth_deg` (−180–180, relative to +Z around +Y), `key_lux` (1–20,000) and `preset` (`neutral`, `warm`, `cool`). Adds deterministic key/fill/rim directional lights to self-contained GLB using KHR_lights_punctual. Preserves original scene geometry; light orientations and exact metadata checked. Compatible importer must support the extension. No actual render, exposure/shadow or visual-quality acceptance.

## Reviewed automated 3D preview rendering (Pass 145)

Files & Images → Render 3D preview. Pass 144 lighting specification plus `elevation_deg` (−80–80), `width` and `height` (64–512 integer pixels), `colors` (one RGB integer triplet per object), `background` (RGB integer triplet). Produces actual auto-framed orthographic flat-shaded PNG with depth-buffer occlusion. Eight-million candidate-pixel budget, exact source guards and decoded pixels. Approximate lighting, not physical photometry, textures, shadows, PBR or native production render.

## Reviewed game asset optimisation (Pass 146)

Files & Images → Optimise game asset. JSON keys: `mesh` (plain triangular OBJ), `triangle_budget` (1–10,000), `vertex_budget` (3–20,000), `cell_sizes` (1–8 distinct sizes 1e-6–1e6), `max_displacement` (1e-6–1e6), `max_position_error` (1e-12–1), `preserve_boundary` (boolean). Produces new GLB only if budgets, precision, manifold checks and any requested exact boundary preservation pass. Not a surface-distance, engine performance, material, UV, rig, LOD or collider guarantee.

## Reviewed automatic texture mapping (Pass 147)

Files & Images → Map texture. JSON keys: `mesh` (plain triangulated OBJ, up to 10,000 faces), `texture` (opaque 8-bit RGB or grayscale PNG, up to 2048×2048), `max_position_error` (1e-12–1). Produces new self-contained GLB with dominant-axis box-projected UVs and embedded base-color PNG. Exact source guards, geometry and PNG roundtrip checks. UV overlap and seams are possible; no baking, painting or native rendering acceptance.

## Reviewed procedural texture generation (Pass 148)

Files & Images → Generate tileable texture. JSON keys: `size` (64/128/256/512/1024), `seed` (0–4294967295), `base_cells` (2–16), `octaves` (1–4), `persistence_percent` (1–90), `low_rgb` and `high_rgb` (distinct RGB integer triplets). Highest frequency at most 64 cells and half the pixel size. Generates a seeded periodic value-noise RGB PNG. Verified periodic field and decoded pixels; not neural material inference or visual acceptance.

## Reviewed PBR material generation (Pass 149)

Files & Images → Generate PBR maps. JSON keys: `height_map` (opaque 8-bit grayscale PNG, max 1024×1024), `low_rgb`, `high_rgb` (RGB integers), `roughness_low`, `roughness_high`, `metallic` (0–255 linear channel values), `strength` (0–64), `edge` (`wrap`/`clamp`). Produces ZIP of base_color.png (sRGB), normal.png (linear OpenGL +Y), metallic_roughness.png (linear R=255, G=roughness, B=metallic), unchanged height.png and material.json. Explicit authored properties, not physical inference or baked occlusion. No native render acceptance.

## Reviewed character skinning (Pass 150)

Files & Images → Skin character mesh. JSON keys: `mesh` (static triangular OBJ), `max_position_error` (1e-12–1), `joints` (2–32 records with distinct `name`, `parent` null for first root or earlier index, `position` XYZ in mesh coordinates). Assigns normalized inverse squared Euclidean weights to nearest two joint positions. New GLB contains hierarchy, inverse bind and skin attributes; verifies rest transforms and geometry. Does not discover skeletons or establish deformation/anatomical quality. Native import unverified.

## Reviewed skeletal animation (Pass 151)

Files & Images → Animate skeleton. Pass 150 rig keys plus `name` and `tracks`: each distinct joint index has `times` (2–256 increasing seconds starting at 0, max 300) and corresponding normalized `rotations_xyzw`. At most 2048 keys. Writes actual GLB rotation channels, LINEAR interpolation and verified rest skin. No arbitrary script execution, IK or native playback guarantee.

## Reviewed animation retargeting (Pass 152)

Files & Images → Retarget animation. Target `mesh`, `max_position_error`, `joints`, `name`; `source_joints` follows Pass 150 schema, `source_tracks` follows Pass 151, `mapping` has one-to-one source/target joint indices and normalized `basis_xyzw` (maps source-local vectors into target-local axes). Mapped parents must correspond; all animated joints must be mapped. Rotations use b*q*conjugate(b); output uses target rest skeleton. No automatic correspondence, contact, IK, root translation or native playback guarantee.

## Reviewed physics trajectory simulation (Pass 153)

Files & Images → Simulate physics. JSON keys: `gravity` (0.01–100 m/s²), `duration_seconds` (0.1–30), `fps` (10–120 integer), `floor_y` (−1000–1000 m), `bodies` (1–8 named spheres with `radius`, `position` XYZ metres, `velocity` XYZ m/s, `restitution` 0–1). Max 20,000 samples, 2048 impacts per body. Outputs JSON positions, velocities and impact events from analytic ballistic floor contacts; low-energy bounces settle. No inter-body collisions, rotation, friction, arbitrary geometry or native physics-engine guarantee.

## Reviewed image upscaling (Pass 154)

Files & Images → Upscale image. JSON keys: `image` (bounded single-frame PNG), `scale` (2/3/4), `method` (nearest/bicubic/lanczos), `sharpen_percent` (0–100; nearest requires zero). Output up to 2048 pixels per side; preserves resampled alpha, verifies decoded PNG. Classical interpolation only, no learned super-resolution or inferred detail.

## Reviewed image restoration (Pass 155)

Files & Images → Restore image. JSON keys: `image` (opaque PNG, at most 1 megapixel), `mask` (null or same-size binary grayscale PNG marking damage white), `threshold` (16–255), `passes` (1–3, masked repair requires 1). Without mask, thresholded median suppresses impulse noise; with mask, local interpolation only, at most 25% damaged and every masked pixel within 3 px of unmasked data in both axes. No inferred historical detail or neural restoration.

## Reviewed image colourisation (Pass 156)

Files & Images → Colourise image. JSON keys: `image` (opaque grayscale PNG, max one megapixel), `regions` (1–4 objects containing `mask` same-size nonempty binary grayscale PNG, `rgb` chromatic integer triplet, `strength_percent` 1–100). Masks cannot overlap; unmasked pixels stay gray. Output RGB PNG preserves encoded Rec.709 luma within half a byte through gamut-limited chroma. Explicit choices, not semantic or historical inference.

## Reviewed reference palette transfer (Pass 157)

Files & Images → Transfer palette. JSON keys: `image` and `reference` (distinct opaque 8-bit RGB PNG files, each max one megapixel), `strength_percent` (integer 1–100). Maps each source RGB channel's empirical midrank to a reference quantile and blends with original values; output dimensions and pixel locations unchanged. Exact guarded input/output and decoded pixel verification. Independent channel palette transfer only, not neural artistic texture or semantic style synthesis.

## Explicit queued image-to-image generation (Pass 158)

Files & Images → Transform image. Select a project-local opaque RGB PNG, enter a transformation description and strength (30–90%); review exact source and new project-root output, 384×384, 15 steps and seed. Existing local SD1.5 Diffusers model is required. Source SHA-256 is checked before generation and before exclusive output publication. Source resized to square; no automatic model installation or download. Uses the existing capped media process. Model quality and actual native generation unverified.

## Reference-guided generation (Pass 159)

Files & Images → Reference-guided image. Choose source RGB PNG and distinct RGB palette reference, both at most one megapixel; specify palette strength and diffusion strength independently. Palette transfer creates the initial image supplied to the existing local SD1.5 image-to-image backend. Exact two-source hash guards and new PNG publication. Not semantic reference conditioning or guaranteed subject consistency.

## Reviewed local image inpainting (Pass 160)

Files & Images → Inpaint image. Select a square opaque RGB PNG (256/384/512) and same-size binary grayscale mask (white to replace, black to preserve). Choose prompt and strength. Existing optional local SD1.5 weights are loaded with StableDiffusionInpaintPipeline; 4/9-channel UNet supported by the backend contract, no automatic download. Output uses exact source pixels outside the mask; source and mask are hash-bound. Actual native model execution and quality are unverified.

## Reviewed local image outpainting (Pass 161)

Files & Images → Outpaint image. Choose opaque RGB source, strictly larger 256/384/512 square canvas, left/top offsets, prompt and diffusion strength. A deterministic outside-region mask and clamped-edge initialization feed the local inpainting backend. Original source pixels remain exact in their chosen location. Native model execution and seam/visual acceptance unverified.

## Reviewed image object removal (Pass 162)

Files & Images → Remove object. Select an opaque square RGB PNG and same-size binary grayscale mask, describe the unwanted object and expected unobstructed background. At least 25% of the image remains unmasked; the selected region is initialized from neighbouring unmasked pixels, not original masked content. Local diffusion receives negative object guidance. Outside pixels stay exact; visual object absence is not certified.

## Reviewed image object replacement (Pass 163)

Files & Images → Replace object. Select explicit source and mask as for object removal, describe the existing object, a different replacement object, and scene context. The old masked pixels are discarded, the replacement and context supply positive guidance, and the old-object description supplies negative guidance. Source pixels outside the mask remain exact. Identity, geometry, and visual acceptance require review.

## Reviewed pose-guided generation (Pass 164)

Files & Images → Pose-guided image. Select a JSON file containing one `joints` object with 14 named joints; each is an integer `[x,y]` pair in normalized thousandths of the square canvas (0–1000). Example:

```json
{"joints":{"head":[500,120],"neck":[500,230],"left_shoulder":[390,260],"right_shoulder":[610,260],"left_elbow":[310,420],"right_elbow":[690,420],"left_wrist":[260,550],"right_wrist":[740,550],"left_hip":[440,530],"right_hip":[560,530],"left_knee":[400,710],"right_knee":[600,710],"left_ankle":[380,880],"right_ankle":[620,880]}}
```

The exact JSON is bound to the queue request, a deterministic mannequin raster becomes the starting image for existing offline SD1.5 image-to-image, and the output is a new PNG. No learned pose detection or ControlNet is used; pose fidelity requires visual review.

## Reviewed relative-depth guided generation (Pass 165)

Files & Images → Depth-guided image. Select a nonuniform square 8-bit grayscale depth PNG of 256, 384 or 512 pixels, choose near-white or near-black convention, relief strength and descriptive prompt. Relative depth tones and optional finite-difference lighting render a deterministic RGB initial image for existing offline diffusion. The guide is hash-bound and unchanged. This is not metric depth estimation or dedicated depth-conditioned neural generation; exact geometry is unverified.

## Reviewed sketch-to-image (Pass 166)

Files & Images → Sketch to image. Select an opaque RGB or grayscale PNG of at most one megapixel, choose line polarity/contrast, prompt and generation strength. The sketch is converted to grayscale, contrast-normalized and centered in a square white canvas without stretching. Existing offline diffusion receives the raster as its starting image; exact line fidelity and native model output remain unverified.

## Editable raster layers (Pass 167)

Files & Images → Editable layers. Use the same canvas and ordered PNG layer schema as image composition, with additional `name` (unique, 1–80 characters) and `visible` (boolean) per layer. Output is `.ora` (OpenRaster), preserving independent raster layers, positions, names, opacity and visibility, plus an opaque background, merged preview and thumbnail. Canvas up to one megapixel, aggregate placed layers up to four megapixels. New file only; original PNGs untouched. Existing ORA/PSD import and native editor interoperability are not verified.

## Reviewed editable graphic design (Pass 168)

Files & Images → Editable graphic. JSON canvas keys: `title`, `width`, `height`, `background` (hex RGB or null), `groups`. Each of 1–12 groups has a distinct `name`, boolean `visible`, integer `opacity` (0–100), and `elements` using the existing logo rectangle, circle, polygon or text schema (up to 32 per group, 64 total). Output is a new SVG with named independent groups and stable element IDs; hidden elements remain present for editing. No arbitrary SVG import, script, remote resource, or rendering/font-fit claim. Use an external editor to inspect and edit the output.

## Visual workflow dataflow (Pass 169)

Both the JANUS-designed and manually composed tool workflow approval paths show a scrollable read-only stage graph before exact command review. Recipe IDs, titles, input/output paths and actual predecessor links come from the frozen manifest, with independent stages distinguished from artifact dependencies. Cancel to leave the proposal unapproved. Continuing still requires the existing command and source revalidation and user approval. This is not a visual node editor or parallel execution engine.

## Reviewed sampled video interpretation (Pass 170)

Files & Images → Interpret video. JSON: `{"video":"clip.mp4","frames":[0,24,48]}`. Select 1–4 sorted distinct frame indices in a short silent constant-rate H.264 MP4 (max 300 frames, 640×480, 16 MiB). Requires installed FFmpeg pair, Node and existing offline Florence vision model. Produces a new JSON report with source/frame hashes, timestamps and model descriptions; these are sparse sampled observations, not verified semantics or continuous motion/audio interpretation. Existing source remains untouched.

## Reviewed screen snapshot (Pass 171)

Files & Images → Capture screen region. Enter primary monitor x,y,width,height (up to 2048 per dimension and 2 megapixels). Confirm one capture after a three-second countdown, then inspect the in-memory preview. Save a new project PNG only after separate confirmation; optional independent approval queues the exact SHA-256-bound saved image for the existing local vision engine. No automatic capture, continuous monitoring or network upload. Windows display scaling and physical-device acceptance remain unverified.

## Expanded video frame editing (Pass 172)

The existing Trim/sequence video tool also accepts an optional `edit` object on each clip: `{"crop":[0,0,320,240],"rotation":90,"flip":"none"}`. Use null for no crop, clockwise rotation 0/90/180/270, and flip none/horizontal/vertical. Apply crop, rotate, then flip. All edited clips must share output dimensions (max 640×480). Existing frame range, 120-frame limit, silent H.264 and exact source checks remain. Output RGB is independently decoded and compared with the expected edited sequence; no native playback claim.

## Reviewed video transitions (Pass 173)

Optionally supply top-level `transitions`, one entry for each pair of adjacent clips: `{"kind":"cut","frames":0}` or `{"kind":"crossfade","frames":4}` (1–12 overlap frames). No field means hard cuts. Crossfade blends the outgoing tail and incoming head with intermediate opacity; output frame count is input frames minus overlaps. Each clip must retain at least one non-transition frame, so adjacent overlaps cannot collide. Applied after per-clip edits. Audio and more elaborate effects remain unsupported.

## Reviewed video motion tracking (Pass 174)

Files & Images → Track video patch. JSON: `{"video":"clip.mp4","start_frame":0,"end_frame":30,"box":[20,20,12,12],"radius":5,"max_error":12}`. Select a nonuniform 4–32 pixel patch, 2–60 source frames, radius 1–12 and mean absolute RGB error limit 0–50. Search is bounded; stop rather than guess at a tied or excessive-error match. JSON contains frame indices, timestamps, bounding boxes and matching error. Translation only, no identity, scale/rotation or occlusion recovery.
