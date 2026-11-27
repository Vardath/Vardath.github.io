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
