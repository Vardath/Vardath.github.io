# Recursive phonetic proto-language reconstruction

This experiment uses the frozen 348-language WikiPron/PHOIBLE 256-gate profiles already published by the phonetic bridge.

## What is being reconstructed

The result is a **latent phonetic/gate-state prototype**: a probability distribution over the 256 directed bridge gates after allowing a small fixed vocabulary of reflections. It is **not** a reconstructed historical word list, grammar, script, or proof that an ancient device deliberately created languages.

## Does the finite operator vocabulary help recover genealogy?

- Identity-only nearest-neighbour family accuracy: **0.447**
- Operator-aware accuracy: **0.447** (Δ +0.000)
- Mean operator gain, same-family pairs: **0.0138**
- Mean operator gain, cross-family pairs: **0.0206**
- Random-permutation control mean same-family gain: **0.0031 ± 0.0016**

## Latent root fingerprint

- Entropy: **6.497 bits**
- Effective gate count: **90.3**
- Mean similarity to root without operators: **0.767**
- Mean similarity after operator alignment: **0.774** (gain +0.007)

Top inferred root gates:

- A1→B2: 0.05533
- B2→A1: 0.04817
- A2→B2: 0.03572
- D2→A1: 0.03071
- B2→A2: 0.02950
- A3→B2: 0.02678
- C2→A1: 0.02642
- B2→A3: 0.02246
- D3→A1: 0.02129
- A1→C2: 0.02019
- D1→A1: 0.01984
- D2→A2: 0.01929
- B1→A1: 0.01845
- D3→A2: 0.01788
- A1→D2: 0.01745
- D3→A3: 0.01733
- D2→A3: 0.01583
- D1→A2: 0.01521
- B1→A2: 0.01396
- B2→D2: 0.01381

Closest language profiles to the latent root (after allowed alignment):

- Occitan (post 1500) [Indo-European]: 0.954 via identity
- Albanian [Unclassified]: 0.953 via identity
- Indonesian [Austronesian]: 0.953 via identity
- Malay (macrolanguage) [Unclassified]: 0.945 via identity
- Lombard [Unclassified]: 0.944 via identity
- Turkish [Turkic]: 0.941 via identity
- Interlingua (International Auxiliary Language Association) [Unclassified]: 0.941 via identity
- Romanian [Indo-European]: 0.939 via identity
- Sranan Tongo [Unclassified]: 0.935 via identity
- Tajik [Indo-European]: 0.934 via place
- Asturian [Indo-European]: 0.934 via identity
- Latin [Unclassified]: 0.934 via identity
- Galician [Indo-European]: 0.934 via identity
- Italian [Indo-European]: 0.933 via identity
- Dhivehi [Indo-European]: 0.932 via identity

## Diachronic checks

- Ancient Greek (to 1453) → Modern Greek (1453-): identity 0.957, best 0.957, Δ +0.000, operator **identity**
- Old English (ca. 450-1100) → Middle English (1100-1500): identity 0.890, best 0.890, Δ +0.000, operator **identity**
- Middle English (1100-1500) → English: identity 0.927, best 0.927, Δ +0.000, operator **identity**
- Old Spanish → Spanish: identity 0.929, best 0.929, Δ +0.000, operator **identity**
- Old High German (ca. 750-1050) → German: identity 0.793, best 0.793, Δ +0.000, operator **identity**
- Middle Dutch (ca. 1050-1350) → Dutch: identity 0.941, best 0.941, Δ +0.000, operator **identity**
- Old Russian → Russian: identity 0.782, best 0.782, Δ +0.000, operator **identity**
- Old French (842-ca. 1400) → French: identity 0.665, best 0.665, Δ +0.000, operator **identity**
- Old Irish (to 900) → Middle Irish (900-1200): identity 0.911, best 0.911, Δ +0.000, operator **identity**
- Middle Irish (900-1200) → Irish: identity 0.884, best 0.884, Δ +0.000, operator **identity**

## Interpretation

A useful result requires the structured operators to outperform arbitrary state permutations and ideally improve recovery of known family relationships. If they do not, the finite-operator idea is not supported by this test. The recursive map in the JSON is descriptive and should not be mistaken for an accepted linguistic family tree.

## Refinement: can the root survive family imbalance?

The family-balanced reconstruction gives each of **36 named PHOIBLE families one vote**, rather than allowing large families to dominate the root.

- Family-balanced entropy: **6.541 bits** (93.1 effective gates)
- Top-20 overlap with the all-language root: **18/20**

Family-balanced top gates:

- A1→B2: 0.04088
- B2→A1: 0.03772
- A2→B2: 0.03706
- B2→A2: 0.03448
- D2→C2: 0.03370
- A3→B2: 0.02878
- D2→A1: 0.02285
- D3→A2: 0.02242
- B2→A3: 0.02134
- D3→A3: 0.02063
- C2→A1: 0.01975
- D3→A1: 0.01936
- B1→A1: 0.01928
- D1→A2: 0.01910
- D2→A2: 0.01875

## Refinement: older/early-labelled subset

The benchmark contains **27** records explicitly labelled Ancient/Old/Middle/Classical or selected early-attested languages. This is not a chronological phylogeny; it is a bias check using the labels available in WikiPron.

- Early-subset entropy: **6.373 bits**
- Top-20 overlap with the all-language root: **18/20

Early-subset top gates:

- A1→B2: 0.07167
- B2→A1: 0.05749
- A2→B2: 0.03735
- D2→A1: 0.03461
- A3→B2: 0.03118
- A1→C2: 0.02952
- C2→A1: 0.02719
- B2→A2: 0.02473
- B1→A1: 0.02156
- A1→D2: 0.02104
- B2→D2: 0.02031
- B2→A3: 0.01977
- D3→A1: 0.01720
- D2→A2: 0.01582
- D1→A1: 0.01554

## Bootstrap-stable root gates

Each bootstrap chooses one language from every named family, reconstructs a root, and records which gates remain in the top 20. High survival means the inferred root feature is not being carried by one oversized family.

- D3→A3: top-20 in 100.0% of runs; mean mass 0.02017
- D3→A2: top-20 in 100.0% of runs; mean mass 0.02291
- D3→A1: top-20 in 100.0% of runs; mean mass 0.02245
- D1→A2: top-20 in 100.0% of runs; mean mass 0.01910
- D1→A1: top-20 in 100.0% of runs; mean mass 0.01795
- D2→A1: top-20 in 100.0% of runs; mean mass 0.02179
- D2→A2: top-20 in 100.0% of runs; mean mass 0.01834
- D2→C2: top-20 in 100.0% of runs; mean mass 0.03410
- C2→A1: top-20 in 100.0% of runs; mean mass 0.02070
- A3→B2: top-20 in 100.0% of runs; mean mass 0.02788
- A1→B2: top-20 in 100.0% of runs; mean mass 0.04409
- A2→B2: top-20 in 100.0% of runs; mean mass 0.03687
- B2→A1: top-20 in 100.0% of runs; mean mass 0.03827
- B2→A3: top-20 in 100.0% of runs; mean mass 0.02092
- B2→A2: top-20 in 100.0% of runs; mean mass 0.03441

## Recurrent family-level gates

- A1→B2: top-32 in 33/36 families (91.7%)
- B2→A1: top-32 in 33/36 families (91.7%)
- D2→A1: top-32 in 32/36 families (88.9%)
- A2→B2: top-32 in 32/36 families (88.9%)
- B2→A2: top-32 in 32/36 families (88.9%)
- D3→A3: top-32 in 31/36 families (86.1%)
- A3→B2: top-32 in 30/36 families (83.3%)
- D3→A2: top-32 in 29/36 families (80.6%)
- B2→A3: top-32 in 29/36 families (80.6%)
- D1→A1: top-32 in 28/36 families (77.8%)
- D2→A3: top-32 in 28/36 families (77.8%)
- D3→A1: top-32 in 28/36 families (77.8%)
- D2→A2: top-32 in 27/36 families (75.0%)
- B1→A1: top-32 in 27/36 families (75.0%)
- C2→A1: top-32 in 26/36 families (72.2%)