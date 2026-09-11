#!/usr/bin/env python3
from pathlib import Path
import reconstruct_original_phonetics_man_grid_v2 as T

ROOT=Path(__file__).resolve().parents[1]
T.WORK=ROOT/'data/man-grid-original-phonetics-exact-v3-work'
T.PREP=T.WORK/'prepared.json.gz'
T.OUT=ROOT/'data/man-grid-original-phonetics-exact-v3.json'

if __name__=='__main__':
    T.main()
