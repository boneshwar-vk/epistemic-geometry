"""metrics: circular/toroidal correlation, identifiability-up-to-isometry, trust residual, AUROC.

Pure-numpy, dependency-light. These are the measurement primitives reused by every phase:
- identity up to isometry: did we recover *the* physical angle (not just a reconstructing subspace)?
- trust residual: the part of the model's confidence NOT explained by the recovered truth coordinate.

All functions operate on numpy arrays and take radians for angles.
"""
from __future__ import annotations

import numpy as np

__all__ = [
    "recover_circular_angle",
    "fit_circular_isometry",
    "apply_circular_isometry",
    "circular_corr_up_to_isometry",
    "circular_correlation",
    "circular_design",
    "fit_linear",
    "fit_trust_model",
    "predict_confidence",
    "trust_residual",
    "auroc",
]


# --------------------------------------------------------------------------- #
# Circular coordinate recovery and identifiability up to isometry
# --------------------------------------------------------------------------- #
def recover_circular_angle(code2d: np.ndarray) -> np.ndarray:
    """Angle (radians, in (-pi, pi]) of a 2-D block code, i.e. atan2(y, x)."""
    code2d = np.asarray(code2d, dtype=float)
    return np.arctan2(code2d[..., 1], code2d[..., 0])


def fit_circular_isometry(theta_true: np.ndarray, theta_hat: np.ndarray) -> tuple[float, float]:
    """Best element of O(2) aligning a recovered angle to the true angle.

    Returns (s, phi0) with s in {+1, -1} and offset phi0 maximizing
    E[cos(theta_true - (s*theta_hat + phi0))]. Fit this on TRAIN, score on TEST.
    """
    theta_true = np.asarray(theta_true, dtype=float)
    theta_hat = np.asarray(theta_hat, dtype=float)
    best = (-2.0, 1.0, 0.0)  # (score, s, phi0)
    for s in (1.0, -1.0):
        ang = s * theta_hat
        phi0 = np.arctan2(np.mean(np.sin(theta_true - ang)), np.mean(np.cos(theta_true - ang)))
        score = float(np.mean(np.cos(theta_true - (ang + phi0))))
        if score > best[0]:
            best = (score, s, phi0)
    return best[1], best[2]


def apply_circular_isometry(theta_hat: np.ndarray, s: float, phi0: float) -> np.ndarray:
    """Apply a fitted O(2) element; result wrapped to (-pi, pi]."""
    out = s * np.asarray(theta_hat, dtype=float) + phi0
    return (out + np.pi) % (2 * np.pi) - np.pi


def circular_corr_up_to_isometry(theta_true: np.ndarray, theta_hat: np.ndarray) -> float:
    """Mean cosine agreement after the best O(2) alignment, in [-1, 1].

    ~1 means the recovered angle IS the true angle up to an unimportant rotation/reflection
    (identity up to isometry). This is the C1 identity metric. If a train/test split is wanted,
    fit the isometry with `fit_circular_isometry` on train and score mean cos on test.
    """
    theta_true = np.asarray(theta_true, dtype=float)
    theta_hat = np.asarray(theta_hat, dtype=float)
    s, phi0 = fit_circular_isometry(theta_true, theta_hat)
    return float(np.mean(np.cos(theta_true - apply_circular_isometry(theta_hat, s, phi0))))


def circular_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Jammalamadaka-Sarma circular correlation coefficient in [-1, 1]."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    abar = np.arctan2(np.mean(np.sin(a)), np.mean(np.cos(a)))
    bbar = np.arctan2(np.mean(np.sin(b)), np.mean(np.cos(b)))
    sa, sb = np.sin(a - abar), np.sin(b - bbar)
    denom = np.sqrt(np.sum(sa ** 2) * np.sum(sb ** 2))
    if denom < 1e-12:
        return 0.0
    return float(np.sum(sa * sb) / denom)


# --------------------------------------------------------------------------- #
# Trust residual (confidence not explained by the recovered truth coordinate)
# --------------------------------------------------------------------------- #
def circular_design(theta: np.ndarray) -> np.ndarray:
    """Design matrix [1, cos(theta), sin(theta)] for regressing a scalar on a circular coordinate."""
    theta = np.asarray(theta, dtype=float)
    return np.stack([np.ones_like(theta), np.cos(theta), np.sin(theta)], axis=1)


def fit_linear(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Ordinary least squares coefficients for X @ beta ~= y (lstsq)."""
    beta, *_ = np.linalg.lstsq(np.asarray(X, float), np.asarray(y, float), rcond=None)
    return beta


def fit_trust_model(theta_hat_train: np.ndarray, c_train: np.ndarray) -> np.ndarray:
    """Fit c_hat(theta) = beta . [1, cos theta, sin theta] on TRAIN. Returns beta."""
    return fit_linear(circular_design(theta_hat_train), c_train)


def predict_confidence(theta_hat: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """Predicted confidence from the recovered coordinate, c_hat(theta)."""
    return circular_design(theta_hat) @ np.asarray(beta, float)


def trust_residual(theta_hat: np.ndarray, c: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """r = c - c_hat(theta): the part of confidence NOT explained by the truth coordinate.

    Large positive r = the model is more confident than the recovered truth coordinate warrants
    (the 'confidently wrong' signature). beta is fit on train via `fit_trust_model`.
    """
    return np.asarray(c, float) - predict_confidence(theta_hat, beta)


# --------------------------------------------------------------------------- #
# AUROC (rank-based; no sklearn dependency)
# --------------------------------------------------------------------------- #
def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Area under the ROC curve for `scores` predicting binary `labels` (1=positive).

    Rank-based (Mann-Whitney U) with tie handling. Returns 0.5 when a class is empty.
    """
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels).astype(int)
    pos = labels == 1
    n_pos = int(pos.sum())
    n_neg = int((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return 0.5
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1, dtype=float)
    # average ranks for ties
    s_sorted = scores[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            avg = (ranks[order[i]] + ranks[order[j]]) / 2.0
            ranks[order[i:j + 1]] = avg
        i = j + 1
    sum_pos = ranks[pos].sum()
    return float((sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))
