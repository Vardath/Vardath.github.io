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
