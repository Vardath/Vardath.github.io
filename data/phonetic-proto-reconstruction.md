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