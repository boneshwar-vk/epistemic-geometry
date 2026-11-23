#!/usr/bin/env python3
"""Unit tests for epistemic_geometry.metrics (pure numpy; runnable with pytest or directly)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from epistemic_geometry import metrics  # noqa: E402


def test_circular_recovery_up_to_isometry():
    rng = np.random.default_rng(0)
    theta = rng.uniform(0, 2 * np.pi, 5000)
    # a rotated+reflected noisy copy should still align to ~1
    theta_hat = (-theta + 1.1) + 0.02 * rng.standard_normal(5000)
    assert metrics.circular_corr_up_to_isometry(theta, theta_hat) > 0.98


def test_circular_corr_invariant_to_isometry():
    rng = np.random.default_rng(1)
    theta = rng.uniform(0, 2 * np.pi, 3000)
    base = metrics.circular_corr_up_to_isometry(theta, theta)
    rot = metrics.circular_corr_up_to_isometry(theta, theta + 0.7)       # pure rotation
    ref = metrics.circular_corr_up_to_isometry(theta, -theta + 0.3)      # reflection + rotation
    assert base > 0.999 and rot > 0.999 and ref > 0.999


def test_recover_circular_angle():
    theta = np.array([0.0, np.pi / 2, np.pi, -np.pi / 2])
    code = np.stack([np.cos(theta), np.sin(theta)], 1)
    assert np.allclose(metrics.recover_circular_angle(code), theta, atol=1e-6)


def test_auroc_separable_and_random():
    rng = np.random.default_rng(2)
    labels = np.r_[np.ones(500), np.zeros(500)].astype(int)
    sep = np.r_[rng.normal(3, 1, 500), rng.normal(0, 1, 500)]
    assert metrics.auroc(sep, labels) > 0.95
    rnd = rng.standard_normal(1000)
    assert abs(metrics.auroc(rnd, labels) - 0.5) < 0.1
    # empty class -> 0.5 by convention
    assert metrics.auroc(rnd, np.ones(1000, dtype=int)) == 0.5


def test_trust_residual_flags_unexplained_confidence():
    # confidence = f(theta) + anomaly; residual should be large exactly on the anomalous points
    rng = np.random.default_rng(3)
    theta = rng.uniform(0, 2 * np.pi, 4000)
    c = 0.5 + 0.4 * np.cos(theta) + 0.01 * rng.standard_normal(4000)
    anom = rng.random(4000) < 0.05
    c = c + anom * 0.5  # inject unexplained confidence on 5% of points
    beta = metrics.fit_trust_model(theta, c)
    r = metrics.trust_residual(theta, c, beta)
    assert metrics.auroc(r, anom.astype(int)) > 0.9


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("ok:", fn.__name__)
    print(f"\nall {len(fns)} tests passed")


if __name__ == "__main__":
    _run_all()
