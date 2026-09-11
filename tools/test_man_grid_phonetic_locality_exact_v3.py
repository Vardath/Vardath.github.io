#!/usr/bin/env python3
from pathlib import Path
import test_man_grid_phonetic_locality_v2 as T

ROOT=Path(__file__).resolve().parents[1]
T.PREP=ROOT/'data/man-grid-original-phonetics-exact-v3-work/prepared.json.gz'
T.WORK=ROOT/'data/man-grid-phonetic-locality-exact-v3-work'
T.OUT=ROOT/'data/man-grid-phonetic-locality-exact-v3.json'

if __name__=='__main__':
    T.main()
