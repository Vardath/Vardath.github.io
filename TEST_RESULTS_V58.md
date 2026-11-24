# DeepThorT v58 Windows acceptance

## Independent PE attempt

The original test case used DeepThorT's saved request 28 and its own earlier model replies. An isolated copy began with one reviewed section out of three. A real Qwen2.5-Coder-1.5B-Instruct ONNX worker ran offline inside the Windows CPU and commit-memory Job Object. Its focused naming response was `vardath_asteroid_pe_macro`. The next live model exchange proposed `md/wharf_production.xml`. All three sections were then reviewed.

The full-project planner retained four file proposals. Its first hierarchy correction shortened an existing macro proposal and closed zero checks. The run stopped at the bounded correction budget with ten planning checks open and zero extension files written in the full-request workspace. These included mesh integration, crew replacement, replenishment, respawn, equipment mapping, cargo, speed and weapons. The checker tracks planning coverage only.

## Scoped file test and OpenCode comparison

For a separate two-file test, the recorded ONNX reply was replayed against the exact original prompt. The test limited approval to the resulting macro and index. DeepThorT rendered the files using the source adapter used by the desktop Build path. The test applied them in a separate workspace through the approved file writer. Both the actual vanilla macro and its vanilla index registration were read from the extracted game data.

| On-disk evidence | Existing OpenCode extension | DeepThorT full request | DeepThorT two-file test |
| --- | ---: | ---: | ---: |
| XML files | 24 | 0 | 2 |
| XMF files | 10 | 0 | 0 |
| Mission Director XML files | 1 | 0 | 0 |
| Local macro registrations resolved | 10 | 0 | 1 |
| Local component registrations resolved | 2 | 0 | 0 |

The new registration resolves to the local variant, whose component is `ship_xen_m_corvette_02`. After restoring its original macro name in memory, the new ship's parsed XML matched the vanilla PE. The static audit correctly reported the missing content.xml in the two-file test. The OpenCode tree passed the same static audit. Neither extension received an in-game test during this comparison.

| Scoped file | SHA-256 |
| --- | --- |
| assets/units/size_m/macros/vardath_asteroid_pe_macro.xml | b61f6eeafb8dbfffcfc1ec8bdd863f8ab499f241d5afeca83a9fdce3c2967daf |
| index/macros.xml | da9f9e33ef30be9e1cc5c6f0239bbf64eb8ef920f7fc78923f2c71282c987a34 |

## Regression coverage

The Windows regression runner reported 679 tests across 84 isolated modules, with zero failing modules. The Windows environment skipped the symlink fixture for lack of symlink privileges. New cases exercise durable collision recovery, scope matching, changed sources, vanilla naming conflicts, wrong index targets and diff selector handling.
