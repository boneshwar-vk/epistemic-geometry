# Roadmap — what will be pushed to this repository

This repository currently holds a **scaffold** plus one working experiment. This file describes what is
planned to land here as the work proceeds, so a reader knows what each (currently empty) folder is for and what
is coming. It is a public roadmap, not a detailed research protocol; dates are not promised.

## Status at a glance

| Component | State |
|---|---|
| Phase 0 — synthetic calibration | ✅ implemented, passing (`experiments/phase0_synthetic/`) |
| `src/epistemic_geometry/` library | 🚧 package stubs only; implementations incoming |
| Phases 1–4 experiments | 🚧 placeholders; incoming |
| Physical ground-truth suite + splits | 🚧 incoming |
| Figures / results | 🚧 incoming |

## The library (`src/epistemic_geometry/`)

Each module below is currently an empty package with a purpose docstring; the listed functionality is what will
be added.

- **`data/`** — cache per-layer activations from a protein language model (and, for the probe-only track, a
  co-folding model); compute physical ground truth by deterministic code: backbone dihedral angles (φ, ψ) and
  relative solvent accessibility from experimental structures (via DSSP/mdtraj), and laboratory binding
  constants for the binding probe. Includes the frozen, hashed train/test splits (sequence-clustered and
  time-based) so results are leakage-controlled.
- **`dictionaries/`** — a scalar top-k sparse autoencoder (baseline), a Euclidean block, and fixed circular
  (S¹) and torus (T²) blocks. The curved blocks are a *control*, not a contribution; everything is compared at a
  matched information budget.
- **`probes/`** — linear and MLP probes for a target physical quantity, and a separate probe for the model's own
  confidence signal.
- **`interventions/`** — wrap-around geodesic steering of a recovered circular coordinate, and the
  persistence/commitment measure (does a mid-computation edit survive the model's generation to the output?).
- **`metrics/`** — circular/toroidal correlation, identifiability-up-to-isometry alignment and scoring,
  topological checks (Betti numbers / persistence), the wrap-around closure metric, and the trust residual
  (confidence not explained by the recovered truth coordinate).
- **`controls/`** — the nuisance-only baseline (position/index, train-set membership, model self-confidence),
  random-initialised-model comparison, matched-bits comparison, a leakage probe, and a structural validity
  filter.
- **`viz/`** — figure generation.

## The experiments (`experiments/`)

- **`phase0_synthetic/`** ✅ — a pure-numpy calibration / "geometry kill-test" on planted data with known
  ground truth. Already run: a curved code ties a flat block of equal dimension at matched budget (so geometry
  is a control), the planted angle is recovered up to isometry, and single-direction codes pay a covering-number
  penalty. Reusable metric code lives here.
- **`phase1_persistence/`** 🚧 — test whether an edit made at a middle layer survives the model's iterative
  generation to the final output. This runs first because it is the most likely to fail and it gates the causal
  experiments.
- **`phase2_identity_truthconf/`** 🚧 — recover the physical coordinate from activations, show it matches the
  truth up to isometry on held-out data, and test whether it is stored in a different direction from the model's
  own confidence.
- **`phase3_causal_wraparound/`** 🚧 — the wrap-around causal dose-response (steer the coordinate a full turn and
  check it returns to baseline), plus a structure-derived phase-slip validator.
- **`phase4_synthesis/`** 🚧 — repeat the analysis across more than one variable and model, run the full
  controls/seed sweep, and assemble the figures.

## What will **not** be in this repository

- The detailed internal research plan and the paper draft are kept private and are not published here.
- Model weights and licensed datasets are obtained separately and are not redistributed; `data/raw/` and
  `data/activations/` are git-ignored.

## Responsible use

The protein (structural-geometry) track is the core. The binding-affinity track is **probe-only** and is framed
as auditing / calibration — it reads internal representations and compares them against laboratory values and
the model's own confidence score, with **no steering toward stronger binding** and no generative-design
pipeline, on benign complexes only.

## Following along

Watch the commit history and the per-folder `README.md` files. `README.md` is the project overview; this file is
the forward-looking plan for the code.
