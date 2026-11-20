# Scratch Chat — Step 8: local GitHub/Drive dataset training

The standalone Vardath Scratch Chat language model remains separate from DeepThorT.

The Step 8 Windows package adds:
- `32-v08-Download-GitHub-Text.cmd`: download an explicitly identified public-domain Shakespeare sample from GitHub and prepare held-out text splits.
- `33-v08-Train-GitHub-CPU.cmd`: train a fresh original transformer on the GitHub text, with resumable checkpoints.
- `34-v08-Prepare-Drive-Folder.cmd`: prepare user-authorised .txt/.md files from a local Google Drive for desktop synced folder.
- `35-v08-Train-Drive-CPU.cmd`: train a separate fresh transformer on that corpus.
- `capability/github_drive_training.py`: validated downloader, provenance metadata, deterministic split preparation.
- `tests/test_github_drive_training.py`: ingestion and permission tests.

Google Drive training folder: https://drive.google.com/drive/folders/1BGKACe5Dz47U3s5FBrTDS1m6HBsUIrS6

**Verified:** 60 tests pass with pytest, and a real two-step CPU training/evaluation smoke test passes on a generated fixture. The external GitHub text download itself cannot be executed from the restricted build environment, so the actual GitHub dataset training run must be initiated on the Windows PC. Google Drive is storage/sync, not compute. Neither sample model is a capable conversational assistant.

The complete Step 8 source and launchers are distributed as a downloadable ZIP in the ChatGPT conversation. Do not infer that these new source files are already committed to this repository from this note alone.
