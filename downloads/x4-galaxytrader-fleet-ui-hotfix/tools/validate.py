#!/usr/bin/env python3
"""Static contracts for the narrow/wide GalaxyTrader Fleet View patch; no X4 executable."""
from pathlib import Path
from zipfile import ZipFile
import argparse, sys

BASE=Path(__file__).resolve().parents[1]
UI=BASE/"patches/gt_fleet_view.lua"
PACKAGE=BASE/"GT_Fleet_UI_Hotfix_1.0.zip"
s=UI.read_text(encoding="utf-8")
checks={
 "adaptive narrow-width threshold": "local function compactList(ctx)" in s and "(ROW_ACTION_COLS + 1) * icon + 4 * text + 32" in s,
 "compact core five-column fleet list": "local cols = compact and 5 or LIST_COLS" in s,
 "compact mode does not reserve six action widths": "if compact then\n        -- Narrow map panels" in s,
 "compact mode disables too-wide filter toolbar": 'if projection.status == "ready" and not compact then' in s,
 "unselected rows have blank action span": 'added[firstAction]:setColSpan(ROW_ACTION_COLS):createText("")' in s,
 "vanilla-XP skipped action slots padded": 'added[col + 1]:setColSpan(last - col):createText("")' in s,
 "regular ship details and orders remain": "addDetailRows(detail, projection, ctx)" in s and "ctx.onOpenOrders(shipId)" in s,
 "no Egosoft base UI, MD, economy scripts": not (BASE/"md").exists() and not (BASE/"aiscripts").exists()
}
# Conservative geometric boundary checks in the same units as the Lua
# expression. Mock dimensions are illustrative; not an engine substitute.
for width, icon, text, expected in [(438,45,85,True),(1800,45,85,False),(444,50,85,True)]:
    required=7*icon+4*text+32
    checks[f"compact width={width}"]=((width<required)==expected)
parser=argparse.ArgumentParser()
parser.add_argument("--zip",action="store_true")
args=parser.parse_args()
if args.zip:
    with ZipFile(PACKAGE) as z:
        expected={"extensions/galaxy_trader/ui/gt_fleet_view.lua": UI.read_bytes()}
        checks["archive CRC"]=z.testzip() is None
        checks["install target exact"]=set(z.namelist())==set(expected)
        checks["archive source byte-match"]=all(z.read(n)==v for n,v in expected.items())
for k,v in checks.items():print(("PASS " if v else "FAIL ")+k)
if not all(checks.values()):sys.exit(1)
print("Static validated, NOT game-runtime tested")
