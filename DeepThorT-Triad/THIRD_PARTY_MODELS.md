# Third-party models and runtimes — not bundled

This ZIP does NOT include any neural-network model weights or independently installed Node/Python packages. All model downloads are opt-in and performed via explicit GUI installation approval.

- **Implementation:** IBM Granite 4.1 3B, community INT4 OpenVINO conversion (Apache-2.0): https://huggingface.co/HarmenWessels/granite-4.1-3b-int4-cw-code-ov
- **JANUS language model:** SmolLM3-3B, community INT4 OpenVINO conversion (Apache-2.0): https://huggingface.co/HarmenWessels/SmolLM3-3B-int4-symg128-ov
- **Sentinel:** Qwen3-4B INT4 (Apache-2.0): https://huggingface.co/OpenVINO/Qwen3-4B-int4-ov
- **Text runtime:** native OpenVINO GenAI 2026.4.1.0, CPU only, installed separately; exact model revisions are pinned in triad_profiles.py.
- **Image reading:** local Florence-2-base-ft ONNX model via Transformers.js. Consult upstream model card/license: https://huggingface.co/onnx-community/Florence-2-base-ft
- **Image generation:** Stable Diffusion 1.5 Diffusers format. License: CreativeML Open RAIL-M; consult https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5
- **Optional image engines only:** Transformers.js / ONNX Runtime and optional PyTorch + Diffusers, with their own third-party licenses.

Model training provenance, capabilities, safety conditions, compatibility, hardware constraints and download availability are controlled by upstream repositories and can change. No AI inference request is sent to a cloud API by this app.
