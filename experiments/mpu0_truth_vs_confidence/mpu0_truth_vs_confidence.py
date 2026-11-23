#!/usr/bin/env python3
"""
MPU-0 — de-risk the TRUTH-vs-CONFIDENCE metric before any model.

Why (from the plan): the paper's headline is that a model stores a physical quantity (truth) in a
direction distinct from its own confidence, and that a *trust residual* read off the recovered truth
coordinate flags the model's confidently-wrong outputs. Before spending anything on real model
activations (which need gated weights), we verify on PLANTED data with known ground truth that:

  (A) the truth coordinate (a circular angle) is recoverable up to isometry from an activation, and
  (B) the trust residual r = c - c_hat(theta) flags "confidently wrong" cases (high confidence,
      atypical truth) better than confidence alone — and we map exactly where this works as the
      coupling rho between confidence and truth is swept from 0 (independent) to 1 (fully entangled,
      the paper's known limitation).

Pure numpy; imports the project's metrics module. Deterministic. Writes results JSON next to this file.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from epistemic_geometry import metrics  # noqa: E402

RNG = np.random.default_rng(0)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def pca_2d(x):
    mu = x.mean(0, keepdims=True)
    idx = RNG.choice(x.shape[0], size=min(4000, x.shape[0]), replace=False)
    _, _, Vt = np.linalg.svd(x[idx] - mu, full_matrices=False)
    return mu, Vt[:2].T


def run(rho, n=20000, d=64, noise=0.05):
    # --- plant a truth angle and its "typicality" (how canonical the local geometry is) ---
    theta = RNG.uniform(0.0, 2.0 * np.pi, n)
    typicality = 0.5 * (1.0 + np.cos(theta))            # high near theta=0, low (atypical) near theta=pi
    z_struct = (typicality - typicality.mean()) / (typicality.std() + 1e-9)

    # --- model's confidence c: couples to typicality with strength rho, else noise ---
    eps = RNG.standard_normal(n)
    c = sigmoid(2.5 * (rho * z_struct + np.sqrt(1 - rho ** 2) * eps))

    # --- plant the truth angle into an activation, then recover it (identity up to isometry) ---
    A, _ = np.linalg.qr(RNG.standard_normal((d, 2)))
    x = np.stack([np.cos(theta), np.sin(theta)], 1) @ A.T + noise * RNG.standard_normal((n, d))
    mu, V = pca_2d(x)
    theta_hat = metrics.recover_circular_angle((x - mu) @ V)
    recov = metrics.circular_corr_up_to_isometry(theta, theta_hat)

    # --- train/test split; trust model fit on train only ---
    tr = RNG.random(n) < 0.5
    beta = metrics.fit_trust_model(theta_hat[tr], c[tr])
    te = ~tr
    r = metrics.trust_residual(theta_hat[te], c[te], beta)
    c_te, typ_te = c[te], typicality[te]

    # --- "confidently wrong" test: within the HIGH-confidence slice, flag the ATYPICAL cases ---
    hi = c_te >= np.quantile(c_te, 0.75)
    atypical = (typ_te <= np.quantile(typ_te, 0.25)).astype(int)
    labels = atypical[hi]
    n_cw = int(labels.sum())
    auroc_r = metrics.auroc(r[hi], labels)          # trust residual
    auroc_c = metrics.auroc(c_te[hi], labels)        # confidence alone (should be ~0.5 within a hi-c slice)
    return {
        "rho": round(float(rho), 2),
        "angle_recovery_up_to_isometry": round(recov, 4),
        "n_confidently_wrong_in_slice": n_cw,
        "auroc_trust_residual": round(float(auroc_r), 4),
        "auroc_confidence_alone": round(float(auroc_c), 4),
        "trust_minus_confidence": round(float(auroc_r - auroc_c), 4),
    }


def verdict(rows):
    # the metric should help in the realistic middle regime (partial coupling), and we expect it to
    # degrade at rho->0 (confidence carries no truth info) and rho->1 (no confidently-wrong cases exist).
    mid = [r for r in rows if 0.3 <= r["rho"] <= 0.7 and r["n_confidently_wrong_in_slice"] >= 50]
    helps = [r for r in mid if r["trust_minus_confidence"] >= 0.15 and r["auroc_trust_residual"] >= 0.70]
    recov_ok = all(r["angle_recovery_up_to_isometry"] > 0.95 for r in rows)
    lines = [
        "ANGLE recovery up to isometry > 0.95 across rho: " + ("PASS" if recov_ok else "FAIL"),
        f"TRUST RESIDUAL beats confidence in the partial-coupling regime (rho 0.3-0.7): "
        + ("PASS" if helps else "NOT SHOWN"),
        "Expected degradation documented: rho->0 (confidence uninformative) and rho->1 "
        "(truth and confidence entangled -> few/no confidently-wrong cases) = the paper's §14.1 limitation.",
    ]
    go = recov_ok and len(helps) >= 1
    lines.append("GATE MPU-0: " + ("GO -> the truth-vs-confidence metric is sound; proceed to the model."
                                    if go else "REVIEW -> inspect the metric before using it on a model."))
    return go, lines


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    rows = [run(rho) for rho in (0.0, 0.3, 0.5, 0.7, 0.9, 1.0)]
    go, lines = verdict(rows)
    out = {"sweep": rows, "gate_MPU0_go": go, "verdict": lines}
    with open(os.path.join(here, "mpu0_results.json"), "w") as f:
        json.dump(out, f, indent=2)

    print("=" * 84)
    print("MPU-0 — truth-vs-confidence metric de-risk (synthetic; no model weights)")
    print("=" * 84)
    print(f"{'rho':>5} {'angle_recov':>12} {'n_conf_wrong':>13} {'AUROC_trust':>12} {'AUROC_conf':>11} {'trust-conf':>11}")
    for r in rows:
        print(f"{r['rho']:>5} {r['angle_recovery_up_to_isometry']:>12} {r['n_confidently_wrong_in_slice']:>13} "
              f"{r['auroc_trust_residual']:>12} {r['auroc_confidence_alone']:>11} {r['trust_minus_confidence']:>11}")
    print("-" * 84)
    for ln in lines:
        print("  " + ln)
    print("-" * 84)
    print("results written to:", os.path.join(here, "mpu0_results.json"))


if __name__ == "__main__":
    main()
