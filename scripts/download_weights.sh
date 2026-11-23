#!/usr/bin/env bash
# =============================================================================
# download_weights.sh  —  fetch open-source model weights for this project.
#
# Run this on the GPU machine BEFORE any experiment. Downloading needs NO GPU.
#
# SAFETY: defaults to DRY_RUN=1 (prints the commands it *would* run). Review,
# then re-run with DRY_RUN=0 to actually download.
#
# STATUS: DRAFT. Commands tagged [VERIFY] still need their exact repo id /
# source confirmed (see scripts/README.md). [CONFIRMED] are standard. This file
# will be finalized once sources are verified.
#
# Usage:
#   DRY_RUN=0 WEIGHTS_DIR=/data/weights MODELS="esm3 boltz proteinmpnn" bash scripts/download_weights.sh
#   bash scripts/download_weights.sh            # dry-run, default model set
#
# Gated models (ESM3) require: (1) a Hugging Face account, (2) accepting the
# model's license on its HF page, (3) `huggingface-cli login` (or HF_TOKEN env).
# NEVER hard-code a token in this file.
# =============================================================================
set -euo pipefail

WEIGHTS_DIR="${WEIGHTS_DIR:-./data/weights}"
DRY_RUN="${DRY_RUN:-1}"
MODELS="${MODELS:-esm3 boltz proteinmpnn rfdiffusion chai}"   # proteina / rfd3: see TODO section

log()  { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
warn() { printf '\033[33mWARN:\033[0m %s\n' "$*" >&2; }
run()  { printf '  + %s\n' "$*"; [ "$DRY_RUN" = "0" ] && "$@"; return 0; }
have() { command -v "$1" >/dev/null 2>&1; }

preflight() {
  log "preflight"
  have python3 || { warn "python3 not found"; exit 1; }
  have git || warn "git not found (needed for ProteinMPNN / RFdiffusion)"
  have git-lfs || warn "git-lfs not found (some weights are LFS; 'git lfs install' first)"
  if ! have huggingface-cli; then
    warn "huggingface-cli not found; installing huggingface_hub[cli]"
    run python3 -m pip install -U "huggingface_hub[cli]"
  fi
  mkdir -p "$WEIGHTS_DIR"
  printf 'WEIGHTS_DIR=%s  DRY_RUN=%s  MODELS="%s"\n' "$WEIGHTS_DIR" "$DRY_RUN" "$MODELS"
  df -h "$WEIGHTS_DIR" | sed 's/^/  /' || true
}

# --- ESM3-open — protein LM [CONFIRMED gated, non-commercial] ------------------
# Spine model for the structural-geometry track. Repo id to VERIFY on the HF page.
get_esm3() {
  log "ESM3-open (EvolutionaryScale/esm3-sm-open-v1) [gated, non-commercial]"
  echo "  Requires: accept license at https://huggingface.co/EvolutionaryScale/esm3-sm-open-v1 then 'huggingface-cli login'."
  run huggingface-cli download EvolutionaryScale/esm3-sm-open-v1 \
      --local-dir "$WEIGHTS_DIR/esm3-sm-open-v1" --exclude "*.msgpack"
  echo "  (Alternative: 'pip install esm' then load esm3_sm_open_v1 via the esm package.)"
}

# --- Boltz — open co-folding / complex model [VERIFY repo id; license MIT] -----
get_boltz() {
  log "Boltz (co-folding / complexes) [open, MIT — VERIFY]"
  echo "  Easiest path: 'pip install boltz'; weights download to cache on first run."
  run python3 -m pip install -U boltz
  echo "  [VERIFY] For an explicit weights pull, confirm the HF repo id (e.g. boltz-community/boltz-1 or -2) before enabling:"
  echo "  #   huggingface-cli download <boltz-repo-id> --local-dir $WEIGHTS_DIR/boltz"
}

# --- Chai-1 — open co-folding model [VERIFY] ----------------------------------
get_chai() {
  log "Chai-1 (co-folding / complexes) [VERIFY]"
  echo "  [VERIFY] 'pip install chai_lab'; weights auto-download on first run. Confirm license + cache path."
  echo "  #   python3 -m pip install -U chai_lab"
}

# --- ProteinMPNN — open; needed for the validity / refold filter [CONFIRMED] --
get_proteinmpnn() {
  log "ProteinMPNN (validity / refold filter) [open]"
  if [ ! -d "$WEIGHTS_DIR/ProteinMPNN" ]; then
    run git clone --depth 1 https://github.com/dauparas/ProteinMPNN "$WEIGHTS_DIR/ProteinMPNN"
  else
    echo "  already present: $WEIGHTS_DIR/ProteinMPNN (weights ship in the repo under */_model_weights)"
  fi
}

# --- RFdiffusion — open; weights via the repo's own download script [VERIFY] --
get_rfdiffusion() {
  log "RFdiffusion (structure diffusion) [open — VERIFY exact script/URL]"
  if [ ! -d "$WEIGHTS_DIR/RFdiffusion" ]; then
    run git clone --depth 1 https://github.com/RosettaCommons/RFdiffusion "$WEIGHTS_DIR/RFdiffusion"
  fi
  echo "  [VERIFY] weights are fetched by the repo's script (downloads from the IPD file server):"
  echo "  #   ( cd $WEIGHTS_DIR/RFdiffusion && bash scripts/download_models.sh ./models )"
}

# --- TODO: models whose open-weight availability is UNVERIFIED -----------------
todo_unverified() {
  log "UNVERIFIED / possibly-not-open (do NOT guess a URL)"
  echo "  - 'RFD3' / RFdiffusion3 / RoseTTAFold3: confirm whether downloadable weights exist at all; if not, omit."
  echo "  - 'Proteina' (NVIDIA protein backbone flow-matching): confirm public weights + source; if not open, omit."
  echo "  - 'complexa': model not identified — confirm what is meant, else use Boltz/Chai as the open co-folding option."
  echo "  These are intentionally NOT downloaded here until their source is confirmed."
}

main() {
  preflight
  for m in $MODELS; do
    case "$m" in
      esm3)         get_esm3 ;;
      boltz)        get_boltz ;;
      chai)         get_chai ;;
      proteinmpnn)  get_proteinmpnn ;;
      rfdiffusion)  get_rfdiffusion ;;
      *)            warn "unknown model key: $m (skipping)" ;;
    esac
  done
  todo_unverified
  log "disk usage"
  du -sh "$WEIGHTS_DIR"/* 2>/dev/null | sed 's/^/  /' || echo "  (nothing downloaded; DRY_RUN=$DRY_RUN)"
  log "done"
  [ "$DRY_RUN" = "1" ] && echo "This was a DRY RUN. Re-run with DRY_RUN=0 to download."
}

main "$@"
