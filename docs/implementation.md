# Implementation / setup plan (Phase 1)

How the first basic phase is built. Reconciled from three expert reviews — SAE/BSF training recipe, engineering
setup, and a soundness red-team. Engineering only; the scientific plan lives privately. `[U]` = unverified
(confirm before it gates anything). Status: **conditional GO** — build the weight-free pipeline now behind the
*plumbing contract* below; the first real-model run is two-staged (ESM-2 then ESM3).

## 0. Decisions (owned)

- **Do we train SAEs/BSFs? Not for the first step — defer.** The first result (the per-layer localization atlas +
  identity-up-to-isometry) needs only **linear/MLP probes + a fixed circular/torus block + supervised alignment**,
  on a ~1M-residue-token cache. All three reviews agree. SAEs/BSFs are trained **later and narrowly, as
  matched-bits controls** — the scalar-SAE "fragments the angle into arcs" baseline, the unsupervised torus
  recovery (G0b), and the Steenwyk scalar-steering must-beat. They do **not** produce the headline coordinate or
  the truth/confidence directions (those are probes).
- **Minimum first experiment is two-staged** (ESM3 access not yet secured):
  - **Stage 0 — full pipeline smoke on ungated ESM-2** (one layer): de-risks every plumbing hazard (indexing,
    join, fp32, determinism, metric) with zero gated-weight dependency. ESM-2 is already a planned panel model.
  - **Stage 1 — one-layer identity on ESM3-open** (L≈24, sequence-only, structure track OFF, both confidence
    signals cached) vs random-init + nuisance + local-window nulls, on the frozen test split.
- **Freeze splits first; cache both confidence signals; all unsupervised fits train-only; metric math in fp32;
  determinism is a checked gate.** (See the plumbing contract.)

## 1. The plumbing contract (the 8 must-fix items — write these before the first real cache)

These are correctness guarantees, not features. The pipeline is not "solid" until each has an assertion/test.

1. **Canonical residue join key** (the #1 silent correctness killer). Define at cache time how an activation row
   maps to a ground-truth residue under insertions, missing density, chain breaks, and BOS/EOS/CLS tokens. Store
   `(chain_id, auth_resi, insertion_code, model_token_index)`; assert join coverage; unit-test insertions/gaps.
   **Labels are joined at analysis time, never baked into the cache.**
2. **Pinned forward protocol + shared hook point.** Identity cache = a single clean *full-visible* forward;
   steering = iterative. Record which, and read a coordinate in the *same representation it was identified in*.
   The residual-stream hook point is named once and shared by cache AND intervention.
3. **Cache both confidence signals from day one** — ESM3 seq-only pLDDT **and** structure-token predictive
   entropy, with provenance. (ESM3 seq-only pLDDT is confidence over the model's *own* predicted structure, likely
   near-identical to entropy `[U]`; the headline truth-vs-confidence claim depends on having a real `c`.)
4. **Splits are a frozen, hashed, committed artifact** produced before any fit or split-dependent decision
   (including the nuisance/leakage probe). Every fit records the split `content_sha256`.
5. **fp16 storage, fp32 math.** Store activations fp16; do all projection / `atan2` / alignment / metric math in
   fp32 (the 0.15 go-margin can hide in fp16 noise). Add an fp16-vs-fp32 stability check.
6. **All unsupervised fits (SAE/BSF/PCA) are TRAIN-only.** The MPU-0 `pca_2d` fits on all points — must **not** be
   copied into the real pipeline. Fit on train, score on test.
7. **Confidently-wrong power is counted at split-freeze**, not in week 5. MPU-0 showed the slice collapses
   (~27 cases at ρ=0.7, 0 at ρ≥0.9) vs the ~45–55 needed; stratify this cell when freezing and decide Track-A vs
   Track-B reliance then.
8. **Determinism is a checked gate** (fixed seeds, fixed order, re-cache reproduces), and **complete run
   metadata** (code SHA, config, split hash, seeds, package versions) is written with every artifact.

## 2. Module APIs (filling the scaffold; reuse the implemented `metrics/` core)

- **`data/`** — `SplitSpec` + `freeze_split()` (MMseqs2 ≤30% ∩ deposition-date; CATH-domain for Tsuboyama;
  PLINDER/PINDER/Bernett for complexes); `ground_truth` (DSSP φ/ψ/ω, FreeSASA rel-SASA, helix_phase, SS);
  `esm3_runner` / `esm2_runner` (seq-only hooks, pLDDT + entropy, the forward protocol of contract #2);
  `CacheWriter` / `CacheReader` (streaming); `SyntheticCache` (plants the Phase-0/MPU-0 signals in the real format).
- **`probes/`** — `RidgeProbe`, `CircularProbe`, `MLPProbe`, `ConfidenceProbe`, and `localization_atlas()` = the
  per-layer "which layers encode X" map (the Phase-1 headline deliverable).
- **`dictionaries/`** — `TopKSAE` (scalar baseline), `EuclideanBlock`, fixed `CircularBlock`/`TorusBlock`
  (controls; no learnable curvature), `matched_bits()` / MDL, ISA/TC torus factorization (G0b). Built/trained in a
  *later* PR.
- **`controls/`** — `NuisanceBaseline` (position/RoPE ⊕ train-membership/cluster ⊕ self-confidence), `random_init`,
  `LeakageProbe`, 3-leg `ValidityFilter`, `cluster_bootstrap`, Holm/BH. Every GO threshold = "beat nuisance+random
  by ≥0.15."
- **`metrics/`** (done; extend) — add `toroidal_corr`, `principal_angles`+nulls, `wrap_closure`, `delong_ci`,
  `betti`. **`interventions/`** — `geodesic_rotate` + `persistence_ratio` (gated, GPU, last).

## 3. Activation cache format + storage

One **fp16 memmap per layer** (`N_residues × d_model`) + a `meta.parquet` keyed by `global_row_index`
(`chain_id, auth_resi, insertion_code, cluster_id, split_tag, phi, psi, omega, helix_phase, rel_sasa, ss,
pLDDT, entropy, forward_protocol`) + a `MANIFEST.json` with per-file sha256. Shard >2 GB; the reader memory-maps
per layer and streams. Storage math (`d_model=1536` fp16 ≈ 3.0 KB/res/layer `[U]`): minimal 300-chain
localization cache ≈ **1.5 GB**; fuller 5k-chain × 200-res = 1M res → **3.07 GB/layer** → ~**24.6 GB** for 8 layers
(+ an equal random-init control).

## 4. SAE/BSF training recipe (for the later control PR — not step 1)

Direct precedent = **Steenwyk's ESM3 SAE** (L33, TopK k=64, width 8× = 12,288, Adam 3e-4, resample/500, 10 epochs).
- **Scalar TopK SAE** (baseline): 8× / width ~12,288, k=32–64, Adam 3e-4, warmup 1000, unit-norm decoder,
  BatchTopK + AuxK (or resample every 500) for feature death.
- **Euclidean BSF**: block size b=2,3 with `G·b` matched to the scalar's *bits*; top-ℓ=8–16; Tournament-TopK.
- **Circular S¹ / torus T²**: **fixed read-time geometry, mostly fitted not trained** (no learnable curvature).
- **Token budget caveat (important):** full-width (~12k) SAEs need **≥5–30M residue tokens** (~25k–150k chains)
  or they feature-die (1M tokens at 12k width ≈ 80 tok/feature, 1–2 orders too few). For the control step, either
  expand the cache to ~25k+ chains **or** shrink expansion to 2–4×. The first step (probes + fixed block) is fine
  on ~1M tokens.
- **Normalization must be identical across scalar and block** for a fair matched-bits control; **prefer subtracting
  a pre-bias over LayerNorm** (LayerNorm flattens the radial structure the circular probe reads). Drop CLS/BOS/EOS.
- **Matched-BITS/MDL, never matched feature count:** fix total description length (active-index bits + quantized-
  value bits + residual bits), tune (width, l0) to equal bits, compare on the rate–distortion frontier. ≥5 seeds,
  median + across-seed SD, mean−2SD margins, Tournament-TopK. Curved-vs-flat differ *only* in read-out geometry,
  judged by identifiability, not FVU.
- **Reusable code:** SAELens (MIT), `dictionary_learning` (saprmarks, MIT), BatchTopK (bartbussmann), InterProt,
  InterPLM — fork one for the scalar/BatchTopK baseline; implement Euclidean/circular/torus blocks + Tournament-TopK
  ourselves. All licenses `[U]` — confirm each LICENSE file.

## 5. Config / CLI / reproducibility

argparse + YAML (no hydra), one config per phase/quantity. Verbs: `eg-freeze-splits → eg-cache → eg-probe-atlas →
eg-truthconf → eg-dict → eg-persistence/eg-wraparound`, plus `eg-smoke`. A `_runner` sets seeds [0–4],
hash-verifies splits, and writes `run_meta.json` + `REPORT.md` under `results/<phase>/<quantity>/<split>/<run_id>/`.
Pre-registered thresholds frozen before any real-model run.

## 6. Weight-free end-to-end smoke test (`eg-smoke`) — the CI gate

`SyntheticCache` writes a **format-identical** cache (planted torus + helix-circle + SASA + an orthogonal
confidence channel with tunable ρ, known clusters) through the real `CacheWriter`, then runs
freeze-splits → atlas → dict → truth-vs-confidence → controls, asserting the Phase-0/MPU-0 numbers (recovery
corr ~0.999, covering penalty, trust-ROC beats confidence at mid-ρ and degrades at ρ→1). This is the standing
**integration gate** and exercises the whole pipeline — including the dictionary interfaces — before any weights.

## 7. Build order (8 PRs) + compute

PR1 runner/CI · PR2 splits+freeze · PR3 cache+reader+synthetic · PR4 controls · PR5 probes/atlas ·
PR6 dicts+truthconf+`eg-smoke`+viz (**closes the weight-free pipeline**) · PR7 `esm2_runner` Stage-0 then
`esm3_runner` Stage-1 (first GPU/weights) · PR8+ interventions (persistence G2, then wrap-around; gated).
Dependencies: PR1→{PR2,PR4}; PR3→PR1; PR5→PR3+PR4; PR6→PR5; PR7→PR6; PR8→PR7 + probe gates.
**PR1–PR6 and the whole smoke test are CPU-only, no weights** (CI green without the torch extra). Only caching
and interventions need GPU (caching 1×24 GB streamed; persistence ~30–80 GPU-h gated first; sweeps ~100–250 GPU-h;
all `[U]`). Four CPU/probe gates gate the entire steering budget.

## 8. Minimum solid first experiment + go/no-go

Stage 0 (ESM-2, one layer) then Stage 1 (ESM3-open, one layer). **"Setup is sound, proceed" = ALL of:** held-out
circular-R² beats nuisance + random-init + local-window by ≥0.15 at one layer; join coverage + insertion/gap tests
pass; metric stable fp16-vs-fp32 and re-cache reproduces; a usable per-residue confidence exists and both are
cached; the frozen test split has ≥~45–55 confidently-wrong candidates. A clean NO-GO with plumbing checks passing
is itself the honest minimum-publishable-result signal.

## 9. Verify before it gates anything (`[U]`)
ESM3 `d_model`≈1536 / `n_layers`≈48 / RoPE / seq-only per-residue pLDDT / structure-token→(φ,ψ) decode fidelity;
ESM3-open gated access + license; dataset counts/licenses (CATH S40, Tsuboyama Zenodo version, PDBBind/PLINDER/
PINDER, SKEMPI, Bernett); Boltz `d_pair` for Track-B sizing; the reusable-codebase LICENSE files. All ESM3 internals
are isolated to `data/esm3_runner.py`, so the rest is testable now.
