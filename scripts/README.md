# scripts

## `download_weights.sh`
Fetches open-source model weights onto a GPU machine before any experiment (downloading needs no GPU).

**Status: DRAFT.** Commands tagged `[VERIFY]` still need their exact repo id / source confirmed; `[CONFIRMED]`
ones are standard. The script defaults to **`DRY_RUN=1`** (prints the commands it would run), so it is safe to
inspect before anything downloads.

Usage:
```bash
# see what it would do (default, no downloads):
bash scripts/download_weights.sh

# actually download a chosen subset into a chosen dir:
DRY_RUN=0 WEIGHTS_DIR=/data/weights MODELS="esm3 proteinmpnn" bash scripts/download_weights.sh
```

Notes:
- **ESM3-open is gated/non-commercial**: accept its license on the Hugging Face model page, then
  `huggingface-cli login` (or set `HF_TOKEN`). Never hard-code a token.
- Model keys: `esm3`, `boltz`, `chai`, `proteinmpnn`, `rfdiffusion`. `proteina` / `rfd3` / `complexa` are left
  as explicit TODOs until their open-weight source is confirmed (the script prints what to check rather than
  guessing a URL).
- `WEIGHTS_DIR` defaults to `./data/weights`, which is git-ignored.
