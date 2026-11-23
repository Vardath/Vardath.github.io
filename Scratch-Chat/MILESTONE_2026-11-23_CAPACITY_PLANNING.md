# Capacity upgrade planning — 2026-11-23

The original Scratch Chat transformer remains independently randomly initialized. No pretrained weights are substituted.

New `python -m capability.capacity_plan --vocab-size 32000 --width 512 --layers 8 --heads 8 --context-size 2048` reports **analytical parameter counts and parameter-state memory lower bounds**, not training benchmarks or a GPU-fit guarantee. The estimator matches the model's tied input/output embeddings, bias-free attention, SwiGLU and RMSNorm. A regression compares estimates with actual PyTorch parameter counts.

Candidate scaling sequence, contingent on **approved dialogue volume**: existing width 64 / 2 layers / context 256 is a plumbing pilot; width 256 / 8 layers / context 1024 is a capacity experiment; width 512 / 8 layers / context 2048 is a substantially larger experiment requiring measured GPU memory and throughput. Vocabulary size must come from a train-only fitted tokenizer. Do not treat these settings as demonstrated feasible on any particular free GPU.

Potential free GPU environments to investigate separately: Kaggle notebooks and Google Colab free tier, subject to current eligibility, time quotas, GPU availability, network/storage policies, and dataset licensing. No account, accelerator, allocation, runtime or persistent checkpoint storage has been verified. Store resumable checkpoint hashes and manifests outside ephemeral sessions only with explicit authorized storage.

Before any scale-up: admit revision-pinned licensed dialogue, group and decontaminate splits, establish assistant-only training, run small original-weight training, benchmark real peak memory, checkpoint reproducibility, multi-turn and tool-use independent probes, and real DeepThorT JSONL interoperability. GitHub Actions CPU is limited to bounded validation and pilots. Dolly remains quarantined. No dialogue checkpoint or capability gain is claimed by this milestone.

CI baseline inspection: GitHub Actions run 45142368801 completed its GitHub Pages jobs successfully; **that run is not the Scratch Chat source-test job**. The source-test conclusion for the prior repair remains unverified here.
