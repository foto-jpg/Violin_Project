from __future__ import annotations
import numpy as np


def _diff_cents(pred_hz: np.ndarray, true_hz: np.ndarray) -> np.ndarray:
    eps = 1e-9
    return 1200.0 * np.log2((pred_hz + eps) / (true_hz + eps))


def pitch_mae_cents(pred_hz: np.ndarray, true_hz: np.ndarray,
                    voiced: np.ndarray) -> float:
    if voiced.sum() == 0:
        return float("nan")
    d = np.abs(_diff_cents(pred_hz[voiced], true_hz[voiced]))
    return float(np.mean(d))


def raw_pitch_accuracy(pred_hz: np.ndarray, true_hz: np.ndarray,
                       voiced: np.ndarray, tol_cents: float = 50.0) -> float:
    if voiced.sum() == 0:
        return float("nan")
    d = np.abs(_diff_cents(pred_hz[voiced], true_hz[voiced]))
    return float((d <= tol_cents).mean())


def raw_chroma_accuracy(pred_hz: np.ndarray, true_hz: np.ndarray,
                        voiced: np.ndarray, tol_cents: float = 50.0) -> float:
    if voiced.sum() == 0:
        return float("nan")
    d = _diff_cents(pred_hz[voiced], true_hz[voiced])
    d_chroma = ((d + 600.0) % 1200.0) - 600.0
    return float((np.abs(d_chroma) <= tol_cents).mean())
