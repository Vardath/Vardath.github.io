# Extended lexical operator-class test

The four added classes are operational proxies over the existing 4x4 bridge paths. Metathesis is a local transposition model; acrophonic compression approximates retaining initial states from hypothesized chunks because the current proto-word dataset has no phrase boundaries; clipping/blending removes medial material or keeps word edges; resegmentation is approximated by boundary rotations. A positive result would show predictive structure under these operators, not prove a particular prehistoric derivation, Proto-World, or deliberate language engineering.

## Held-out result

Full 12-class held-out score: **0.648**
Baseline 8-class held-out score: **0.538**
New four-class held-out score: **0.653**
Identity same-meaning baseline: **0.578**
Oracle same-meaning ceiling: **0.721**
Unrestricted-anagram diagnostic ceiling: **0.640**
Shuffled held-out score: **0.626 ± 0.012**
Δ vs null **+0.022**, permutation p **0.041250**

## Same-meaning versus wrong-meaning by class

- identity: same 0.578, wrong 0.579, Δ -0.001
- reverse: same 0.570, wrong 0.559, Δ +0.011
- place: same 0.581, wrong 0.565, Δ +0.016
- reverse+place: same 0.550, wrong 0.546, Δ +0.004
- manner: same 0.543, wrong 0.561, Δ -0.018
- reverse+manner: same 0.572, wrong 0.571, Δ +0.001
- place+manner: same 0.542, wrong 0.547, Δ -0.004
- reverse+place+manner: same 0.557, wrong 0.556, Δ +0.001
- metathesis: same 0.625, wrong 0.625, Δ +0.000
- acrophonic: same 0.651, wrong 0.650, Δ +0.002
- clipblend: same 0.610, wrong 0.609, Δ +0.001
- resegmentation: same 0.605, wrong 0.600, Δ +0.005

## Classes selected by leave-one-meaning-out validation

- acrophonic: 37
- metathesis: 21
- resegmentation: 12
- clipblend: 7
- identity: 1
- place: 1
- reverse+place+manner: 1
- manner: 0
- place+manner: 0
- reverse: 0
- reverse+manner: 0
- reverse+place: 0