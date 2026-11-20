# Step 4 — standalone chat training, without JANUS integration

## Scope

The project is an original neural language model, not a bridge to an existing commercial model. JANUS integration and release-validation activities are **out of scope**. This step adds supervised instruction training, interactive inference and evidence of whether that training generalizes.

## Implemented

- `capability/instruct.py`: independent response-target-only training path for messages, using the Step 1 learned byte-BPE vocabulary and the Step 2 original transformer.
- Trainable from random initialization or, when the vocabulary and architecture match, from a previously trained **original** local base checkpoint.
- Proper shifted next-token target masking so it does not waste optimizer updates learning to repeat the user prompt.
- Separate train/validation/test examples, rejecting collisions of split groups.
- Atomic full-state checkpoints, deterministic CPU restoration, measured answer-token cross entropy and perplexity.
- Best-performing checkpoint selected by validation loss, with configurable early stopping to avoid training past the optimum.
- A standalone interactive chat loop; not connected to JANUS.
- Windows command files 21–24.

## Actual experiment

The pilot used only 51 hand-authored original chat examples, split 35 train / 8 validation / 8 test. Model 496,032 parameters, ~646-token BPE vocabulary, context allocation 1,024, CPU-only.

| Measurement | Observed |
| --- | ---: |
| Initial held-out validation loss | 6.525742 |
| Best validation loss after 100 updates | 4.198731 |
| Best validation perplexity | 66.60178 |
| Test loss with best checkpoint | 3.995387 |
| Test perplexity with best checkpoint | 54.34686 |
| Later validation loss after 200 updates | 4.467129 |
| Early-stopping outcome | Stopped at update 200; best checkpoint from 100 |

**Actual generated responses remain poor.** At zero temperature with the best checkpoint:

- Prompt: `hello` → `A a a a a a a a a a a a a and a a a a a a a a a.`
- Prompt: `how do airplanes fly?` → `A a a and a a a a a and and a a.`
- Prompt: `how do you compile a program?` → `A  a and a a a a a and and a a.`

These examples are intentionally included to prevent interpreting decreasing language-model loss as proof of general capability.

## Current limitations and next work

The project's language model remains **not capable** of general conversation. The missing prerequisite is large-scale broad-text pretraining on properly sourced data using substantially more training time and compute. The WikiText ingestion path exists, but the dataset was not downloadable in this environment and has **not** been trained. More significant progress depends on training with actual corpus text, measuring held-out generalization, then instruction-tuning an adequately pretrained base model. A tiny pilot fine-tuned on 35 examples cannot substitute for those steps.

Licensing note: the Salesforce/WikiText dataset page presents inconsistent licence metadata (CC BY-SA 3.0/GFDL in metadata versus CC BY-SA 4.0 in prose). Confirm the applicable terms before redistributing corpus text or trained weights derived from it.
