# Third-party models and runtimes — not bundled

This ZIP does NOT include any neural-network model weights or independently installed Node/Python packages. All model downloads are opt-in and performed via explicit GUI installation approval.

- **Chat/code:** `onnx-community/Qwen2.5-Coder-1.5B-Instruct` (local ONNX quantization). Consult its model card for the upstream license and usage conditions: https://huggingface.co/onnx-community/Qwen2.5-Coder-1.5B-Instruct
- **Image reading:** local Florence-2-base-ft ONNX model via Transformers.js. Consult upstream model card/license: https://huggingface.co/onnx-community/Florence-2-base-ft
- **Image generation:** Stable Diffusion 1.5 Diffusers format. License: CreativeML Open RAIL-M; consult https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5
- **Engines:** Transformers.js / ONNX Runtime and optional PyTorch + Diffusers, with their own third-party licenses.

Model training provenance, capabilities, safety conditions, compatibility, hardware constraints and download availability are controlled by upstream repositories and can change. No AI inference request is sent to a cloud API by this app.
