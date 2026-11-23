#!/usr/bin/env bash
# =============================================================================
# download_weights.sh  —  fetch open-source model weights for this project.
#
# Run on the GPU machine BEFORE any experiment. Downloading needs NO GPU, but it
# does need outbound access to Hugging Face, GitHub, and the IPD file server.
#
# SAFETY: defaults to DRY_RUN=1 (prints the commands it *would* run). Review, then
# re-run with DRY_RUN=0 to actually download.
#
# Confidence tags (sources verified via model cards / docs; re-confirm on the box):
#   [CONFIRMED-open]  standard, permissive-or-open weights
#   [GATED]           open weights behind a license-accept + HF login
#   [VERIFY]          newer / less-common source; confirm the exact id before DRY_RUN=0
#   [TODO]            source not pinned down; script prints guidance, downloads nothing
#
# Usage:
#   bash scripts/download_weights.sh                                   # dry-run, default set
#   DRY_RUN=0 WEIGHTS_DIR=/data/weights MODELS="esm3 boltz" bash scripts/download_weights.sh
#
# Gated (ESM3): accept the license on the HF page, then `huggingface-cli login`
# (or export HF_TOKEN). NEVER hard-code a token here.
# =============================================================================
set -uo pipefail

WEIGHTS_DIR="${WEIGHTS_DIR:-./data/weights}"
DRY_RUN="${DRY_RUN:-1}"
# default set = the high-confidence models; optional ones (rfd3 proteina proteina_complexa)
# are opt-in via MODELS="..." because their source is newer / less certain.
MODELS="${MODELS:-esm3 boltz chai proteinmpnn rfdiffusion rfdiffusion_aa}"

log()  { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
warn() { printf '\033[33mWARN:\033[0m %s\n' "$*" >&2; }
run()  { printf '  + %s\n' "$*"; if [ "$DRY_RUN" = "0" ]; then "$@"; fi; }
have() { command -v "$1" >/dev/null 2>&1; }

HF=""   # resolved to `hf` or `huggingface-cli` in preflight

preflight() {
  log "preflight"
  have python3 || { warn "python3 not found"; exit 1; }
  have git     || warn "git not found (needed for ProteinMPNN / RFdiffusion)"
  have wget    || warn "wget not found (needed for some IPD weight files)"
  have git-lfs || warn "git-lfs not found; run 'git lfs install' (some weights are LFS)"
  if have hf; then HF="hf";
  elif have huggingface-cli; then HF="huggingface-cli";
  else
    warn "no HF CLI; installing huggingface_hub[cli]"
    run python3 -m pip install -U "huggingface_hub[cli]"
    HF="huggingface-cli"
  fi
  mkdir -p "$WEIGHTS_DIR"
  printf 'WEIGHTS_DIR=%s  DRY_RUN=%s  HF=%s\n' "$WEIGHTS_DIR" "$DRY_RUN" "${HF:-none}"
  printf 'MODELS="%s"\n' "$MODELS"
  df -h "$WEIGHTS_DIR" 2>/dev/null | sed 's/^/  /' || true
}

hf_dl() {  # hf_dl <repo_id> <subdir> [extra args...]
  local repo="$1" sub="$2"; shift 2
  run "$HF" download "$repo" --local-dir "$WEIGHTS_DIR/$sub" "$@"
}

# --- ESM3-open — protein LM [GATED, non-commercial Community License, ~3 GB] ---
get_esm3() {
  log "ESM3-open  EvolutionaryScale/esm3-sm-open-v1  [GATED, non-commercial]"
  echo "  Accept the license at https://huggingface.co/EvolutionaryScale/esm3-sm-open-v1, then '$HF login'."
  hf_dl EvolutionaryScale/esm3-sm-open-v1 esm3-sm-open-v1
  echo "  (Alternative: 'pip install esm' and load esm3_sm_open_v1 via the esm package.)"
}

# --- Boltz-2 — co-folding / complexes [CONFIRMED-open, MIT, ~1-2 GB] ----------
get_boltz() {
  log "Boltz-2  boltz-community/boltz-2  [CONFIRMED-open, MIT]"
  echo "  pip install boltz; weights auto-download on first run (or pull explicitly below)."
  run python3 -m pip install -U boltz
  hf_dl boltz-community/boltz-2 boltz-2
}

# --- Chai-1 — co-folding / complexes [CONFIRMED-open, Apache-2.0, ~1-2 GB] ----
get_chai() {
  log "Chai-1  chaidiscovery/chai-1  [CONFIRMED-open, Apache-2.0]"
  echo "  pip install chai_lab; weights auto-download (CHAI_DOWNLOADS_DIR), or pull explicitly below."
  run python3 -m pip install -U chai_lab
  hf_dl chaidiscovery/chai-1 chai-1
}

# --- ProteinMPNN — validity / refold filter [CONFIRMED-open, MIT, ~tens MB] ---
get_proteinmpnn() {
  log "ProteinMPNN  dauparas/ProteinMPNN  [CONFIRMED-open, MIT]  (weights bundled in the repo)"
  if [ ! -d "$WEIGHTS_DIR/ProteinMPNN" ]; then
    run git clone --depth 1 https://github.com/dauparas/ProteinMPNN "$WEIGHTS_DIR/ProteinMPNN"
  else echo "  already present: $WEIGHTS_DIR/ProteinMPNN"; fi
}

# --- RFdiffusion (original) — structure diffusion [CONFIRMED-open, BSD-3] -----
get_rfdiffusion() {
  log "RFdiffusion  RosettaCommons/RFdiffusion  [CONFIRMED-open, BSD-3, ~3-4 GB]"
  if [ ! -d "$WEIGHTS_DIR/RFdiffusion" ]; then
    run git clone --depth 1 https://github.com/RosettaCommons/RFdiffusion "$WEIGHTS_DIR/RFdiffusion"
  fi
  echo "  weights are fetched by the repo's own script (downloads from the IPD file server):"
  run bash -c "cd '$WEIGHTS_DIR/RFdiffusion' && bash scripts/download_models.sh ./models"
}

# --- RFdiffusionAA — all-atom [CONFIRMED-open, ~1-1.5 GB] ----------------------
get_rfdiffusion_aa() {
  log "RFdiffusionAA  baker-laboratory/rf_diffusion_all_atom  [CONFIRMED-open]"
  if [ ! -d "$WEIGHTS_DIR/rf_diffusion_all_atom" ]; then
    run git clone --depth 1 https://github.com/baker-laboratory/rf_diffusion_all_atom "$WEIGHTS_DIR/rf_diffusion_all_atom"
  fi
  echo "  [VERIFY] fetch the paper weights per the repo README (IPD file server), e.g.:"
  echo "  #   wget -P '$WEIGHTS_DIR/rf_diffusion_all_atom' http://files.ipd.uw.edu/.../RFDiffusionAA_paper_weights.pt"
}

# --- RFdiffusion3 / RF3 — via Rosetta Commons foundry [CONFIRMED-open, BSD-3] -
get_rfd3() {
  log "RFdiffusion3 / RF3  (Rosetta Commons 'foundry')  [VERIFY the CLI + pip on the box]"
  echo "  [VERIFY] reported path: pip install rc-foundry; then 'foundry install base-models' (~6-10 GB)."
  echo "  #   python3 -m pip install -U rc-foundry && foundry install base-models --dest '$WEIGHTS_DIR/rf3'"
}

# --- Proteina (NVIDIA) — backbone flow-matching [CONFIRMED-open, BSD-3] --------
get_proteina() {
  log "Proteina  nvidia/RFD4-Proteina  [VERIFY exact HF id; reported not-gated, ~1.7 GB]"
  echo "  [VERIFY] confirm the repo id on huggingface.co before DRY_RUN=0:"
  echo "  #   $HF download nvidia/RFD4-Proteina --local-dir '$WEIGHTS_DIR/proteina'"
}

# --- Proteina-Complexa (NVIDIA) — co-folding/complex [TODO: id not pinned] ----
get_proteina_complexa() {
  log "Proteina-Complexa (NVIDIA)  [TODO — exact official download id UNVERIFIED]"
  echo "  Code: github.com/NVIDIA-Digital-Bio/Proteina-Complexa ; weights under NVIDIA Open Model License."
  echo "  Confirm the NGC / HF id before use. Confirmed-open co-folding substitutes: Boltz-2, Chai-1 (above)."
}

main() {
  preflight
  for m in $MODELS; do
    if declare -F "get_$m" >/dev/null; then
      "get_$m" || warn "$m: a download step failed (continuing)"
    else
      warn "unknown model key: $m (valid: esm3 boltz chai proteinmpnn rfdiffusion rfdiffusion_aa rfd3 proteina proteina_complexa)"
    fi
  done
  log "disk usage"
  du -sh "$WEIGHTS_DIR"/* 2>/dev/null | sed 's/^/  /' || echo "  (nothing downloaded; DRY_RUN=$DRY_RUN)"
  log "done"
  [ "$DRY_RUN" = "1" ] && echo "This was a DRY RUN. Re-run with DRY_RUN=0 to download."
  return 0
}

main "$@"
