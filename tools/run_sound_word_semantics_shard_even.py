#!/usr/bin/env python3
import argparse
import man_grid_exact_data as D
import test_sound_word_semantics_v1 as T

p=argparse.ArgumentParser();p.add_argument('--id',type=int,required=True);a=p.parse_args()
x=T.loadgz(T.PREP)
order=sorted(x['plan'],key=lambda lid:(D.h64('lexsem-even-order',lid),lid))
for j,lid in enumerate(order):x['plan'][lid]['shard']=j%T.SHARDS
T.dumpgz(T.PREP,x)
T.shard(a.id)
