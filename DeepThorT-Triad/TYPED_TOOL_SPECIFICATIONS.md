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
