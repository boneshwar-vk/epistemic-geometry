# MPU-0 — truth-vs-confidence metric de-risk

Run: `python3 mpu0_truth_vs_confidence.py` (pure numpy; imports `epistemic_geometry.metrics`).

Verifies, on planted data with known ground truth and **before any model weights are needed**, that the
project's headline metric is sound: (A) a circular truth coordinate is recovered **up to isometry** from an
activation, and (B) the **trust residual** `r = c − ĉ(θ)` flags *confidently-wrong* cases (high confidence,
atypical truth) better than confidence alone — sweeping the coupling `rho` between confidence and truth.

First result (`mpu0_results.json`):
- angle recovery up to isometry ≈ 0.999 across all `rho`;
- trust residual AUROC ≈ 0.97–0.999 vs confidence AUROC ≈ 0.24–0.40 in the realistic partial-coupling regime
  (`rho` 0.3–0.7);
- degrades at `rho→0` (confidence carries no truth information) and `rho→1` (truth and confidence are fully
  entangled, so no confidently-wrong cases exist) — this `rho→1` corner is the project's known limitation.
- **Gate MPU-0: GO** — the metric is sound; proceed to the model once weights are available.
