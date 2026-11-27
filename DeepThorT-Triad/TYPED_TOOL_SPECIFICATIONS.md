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
