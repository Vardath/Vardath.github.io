# Galactic Occupations — localization (0.5.5)

X4 supports 14 Steam interface selections. The stock X4 text table supplies 13 distinct language IDs because Spanish (Spain) and Spanish (Latin America) use the same Spanish text code, L034. The following X4-compatible source files are bundled under `vardath_galactic_occupations/t/`:

| X4 language ID | File | Language |
| --- | --- | --- |
| 007 | `0001-l007.xml` | Russian |
| 033 | `0001-l033.xml` | French |
| 034 | `0001-l034.xml` | Spanish (shared regional text) |
| 039 | `0001-l039.xml` | Italian |
| 042 | `0001-l042.xml` | Czech |
| 044 | `0001-l044.xml` | English |
| 048 | `0001-l048.xml` | Polish |
| 049 | `0001-l049.xml` | German |
| 055 | `0001-l055.xml` | Brazilian Portuguese |
| 081 | `0001-l081.xml` | Japanese |
| 082 | `0001-l082.xml` | Korean |
| 086 | `0001-l086.xml` | Simplified Chinese |
| 088 | `0001-l088.xml` | Traditional Chinese |

The original language-neutral `0001.xml` supplies a complete **English** fallback.
All 13 language-specific files use `<page id="191180">` and have exactly the same 60 `<t id="...">` entries. Language IDs are decimal within the XML element (`id="7"` for L007). Filenames are deliberately lowercase for Linux filesystem support.

## Changing your language

Set X4 to your language in the game's settings; the mod reads the matching table automatically when X4 loads. No manual renaming or new-game start is necessary. Install by extracting the current complete release ZIP into the X4 game directory, maintaining the path `extensions/vardath_galactic_occupations/t/`.

## Scope and translation review

These translations cover the 60 `readtext` strings: settings, every occupation name and description, hacking commands, EMP/crystal survey options and tooltip explanations. Text generated directly inside mission/AI scripts or Lua UI, including some debug and logbook status messages, remains in English. The source language tables are complete, **but this is not a claim of 100% localization of all runtime prose**.

Translations are AI-assisted first drafts; native-speaker review is welcomed, especially for in-game X4 technical vocabulary, idioms, grammatical agreement and layout length.

To correct a translation, edit only text content in the appropriate `t/0001-lXXX.xml` file. Preserve the XML structure, text IDs, escape special characters like `&` as `&amp;`, and do not change currency amounts or job mechanics. Run:

```sh
python downloads/x4-galactic-occupations/tools/tests/localization_contracts.py
python downloads/x4-galactic-occupations/tools/validate.py
```

A passing static test confirms formatting/coverage only. Live checks should include selecting each occupation in the ship Behaviour menu, examining the full tooltip and settings at practical UI scaling, then confirming no `ReadText191180-...` placeholders.
