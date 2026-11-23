# scripts

## `download_weights.sh`
Fetches open-source model weights onto a GPU machine before any experiment (downloading needs no GPU, but
needs outbound access to Hugging Face, GitHub, and the IPD file server).

**Safety:** defaults to **`DRY_RUN=1`** — it prints the exact commands it would run and downloads nothing.
Inspect, then re-run with `DRY_RUN=0`.

Usage:
```bash
bash scripts/download_weights.sh                                           # dry-run, default set
DRY_RUN=0 WEIGHTS_DIR=/data/weights MODELS="esm3 boltz proteinmpnn" bash scripts/download_weights.sh
```

Model keys and status (sources verified via model cards/docs; re-confirm on the box):

| key | model | status |
|---|---|---|
| `esm3` | ESM3-open (`EvolutionaryScale/esm3-sm-open-v1`) | **GATED**, non-commercial — accept license + `huggingface-cli login` |
| `boltz` | Boltz-2 (`boltz-community/boltz-2`) | open, MIT |
| `chai` | Chai-1 (`chaidiscovery/chai-1`) | open, Apache-2.0 |
| `proteinmpnn` | ProteinMPNN (`dauparas/ProteinMPNN`) | open, MIT — validity/refold filter |
| `rfdiffusion` | RFdiffusion (`RosettaCommons/RFdiffusion`) | open, BSD-3 |
| `rfdiffusion_aa` | RFdiffusionAA (`baker-laboratory/rf_diffusion_all_atom`) | open — weight URL `[VERIFY]` on box |
| `rfd3` | RFdiffusion3 / RF3 (Rosetta Commons `foundry`) | open, BSD-3 — CLI/pip `[VERIFY]` (not in default set) |
| `proteina` | Proteina (`nvidia/RFD4-Proteina`) | open, BSD-3 — HF id `[VERIFY]` (not in default set) |
| `proteina_complexa` | NVIDIA Proteina-Complexa | `[TODO]` exact id unconfirmed; use Boltz-2/Chai-1 meanwhile (not in default set) |

Default set = `esm3 boltz chai proteinmpnn rfdiffusion rfdiffusion_aa`. The newer/less-certain models
(`rfd3`, `proteina`, `proteina_complexa`) are opt-in via `MODELS="..."` and print a verify/TODO note rather
than guessing an exact source.

Notes:
- Never hard-code an HF token; the script uses your `huggingface-cli login` session or `HF_TOKEN`.
- `WEIGHTS_DIR` defaults to `./data/weights`, which is git-ignored.
- Which models you actually need depends on the track: `esm3` for the structural-geometry (angles/dynamics/
  stability) spine; a co-folding model (`boltz`/`chai`) for the PPI/interface/specificity/binding probes;
  `proteinmpnn` for the validity filter. The diffusion models (`rfdiffusion*`, `rfd3`, `proteina*`) are for
  the later, deferred causal/steering work.
