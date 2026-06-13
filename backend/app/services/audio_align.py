from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
import torch
import torchcrepe
from loguru import logger

from app.services.audio_engine import (
    CONFIDENCE_THRESHOLD,
    FMAX,
    FMIN,
    HOP_LENGTH,
    NOTE_NAMES,
    SAMPLE_RATE,
    _midi_to_note,
)

CHROMA_BINS = 12


def _audio_chroma(audio: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    audio_t = torch.from_numpy(audio).unsqueeze(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pitch, periodicity = torchcrepe.predict(
        audio_t, sample_rate=sr, hop_length=HOP_LENGTH, fmin=FMIN, fmax=FMAX,
        model="full", decoder=torchcrepe.decode.weighted_argmax,
        return_periodicity=True, device=device, batch_size=512,
    )
    periodicity = torchcrepe.filter.median(periodicity, 3)
    pitch = torchcrepe.filter.mean(pitch, 3)
    freqs = pitch.squeeze(0).cpu().numpy()
    conf = periodicity.squeeze(0).cpu().numpy()
    midi = librosa.hz_to_midi(np.where(freqs > 0, freqs, np.nan))

    chroma = np.zeros((len(midi), CHROMA_BINS), dtype=np.float32)
    voiced = (conf >= CONFIDENCE_THRESHOLD) & np.isfinite(midi)
    for i in np.where(voiced)[0]:
        pc = int(round(midi[i])) % 12
        chroma[i, pc] = conf[i]
    return chroma, midi, conf


def _score_chroma_from_notes(notes: list[dict], total_frames: int, sr: int,
                             tempo_bpm: float) -> np.ndarray:
    hop_sec = HOP_LENGTH / sr
    sec_per_quarter = 60.0 / max(tempo_bpm, 1.0)
    chroma = np.zeros((total_frames, CHROMA_BINS), dtype=np.float32)
    t = 0.0
    for n in notes:
        dur_sec = float(n["duration"]) * sec_per_quarter
        start_frame = int(round(t / hop_sec))
        end_frame = int(round((t + dur_sec) / hop_sec))
        if start_frame >= total_frames:
            break
        end_frame = min(end_frame, total_frames)
        pc = int(n["midi"]) % 12
        chroma[start_frame:end_frame, pc] = 1.0
        t += dur_sec
    return chroma


def _cosine_cost_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    na = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    nb = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
    return 1.0 - na @ nb.T


def _banded_dtw(cost: np.ndarray, band_frac: float = 0.25) -> list[tuple[int, int]]:
    N, M = cost.shape
    band = max(8, int(M * band_frac))
    INF = np.inf
    D = np.full((N + 1, M + 1), INF, dtype=np.float64)
    D[0, 0] = 0.0
    bt = np.zeros((N + 1, M + 1), dtype=np.int8)
    for i in range(1, N + 1):
        j_center = int(round(i * M / N))
        j_lo = max(1, j_center - band)
        j_hi = min(M, j_center + band)
        for j in range(j_lo, j_hi + 1):
            c = cost[i - 1, j - 1]
            diag = D[i - 1, j - 1]
            up = D[i - 1, j]
            left = D[i, j - 1]
            best = diag; choice = 0
            if up < best: best, choice = up, 1
            if left < best: best, choice = left, 2
            D[i, j] = c + best
            bt[i, j] = choice
    path: list[tuple[int, int]] = []
    i, j = N, M
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        c = bt[i, j]
        if c == 0:   i, j = i - 1, j - 1
        elif c == 1: i = i - 1
        else:        j = j - 1
    path.reverse()
    return path


@dataclass
class AlignedNote:
    index: int
    expected_midi: int
    expected_name: str
    start_sec: float
    end_sec: float
    played_midi: int
    played_name: str
    pitch_diff_cents: float
    voiced_fraction: float
    status: str = "correct"  # "correct" | "wrong_pitch" | "missed"


def _classify(pitch_diff_cents: float, voiced_fraction: float) -> str:
    if voiced_fraction < 0.3:
        return "missed"
    if abs(pitch_diff_cents) > 50:
        return "wrong_pitch"
    return "correct"


def align_audio_to_score(
    audio_path: Path, expected_notes: list[dict], tempo_bpm: float,
) -> dict:
    audio, sr = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
    duration_sec = float(len(audio) / sr)
    if not expected_notes:
        raise ValueError("expected_notes is empty - nothing to align against")

    logger.info(f"DTW alignment: {duration_sec:.1f}s audio vs {len(expected_notes)} expected notes @ {tempo_bpm} BPM")

    audio_ch, midi_track, conf_track = _audio_chroma(audio, sr)
    score_ch = _score_chroma_from_notes(expected_notes, len(audio_ch), sr, tempo_bpm)

    cost = _cosine_cost_matrix(score_ch, audio_ch)
    path = _banded_dtw(cost)

    from collections import defaultdict
    score_to_audio: dict[int, list[int]] = defaultdict(list)
    for si, ai in path:
        score_to_audio[si].append(ai)

    hop_sec = HOP_LENGTH / sr
    sec_per_quarter = 60.0 / max(tempo_bpm, 1.0)

    aligned: list[AlignedNote] = []
    t = 0.0
    for idx, n in enumerate(expected_notes):
        dur_sec = float(n["duration"]) * sec_per_quarter
        s_start = int(round(t / hop_sec))
        s_end = int(round((t + dur_sec) / hop_sec))
        t += dur_sec
        if s_end <= s_start:
            continue

        audio_idxs: list[int] = []
        for sf in range(s_start, min(s_end, len(score_ch))):
            audio_idxs.extend(score_to_audio.get(sf, []))
        if not audio_idxs:
            continue
        a_start, a_end = min(audio_idxs), max(audio_idxs) + 1

        seg_midi = midi_track[a_start:a_end]
        seg_conf = conf_track[a_start:a_end]
        v = (seg_conf >= CONFIDENCE_THRESHOLD) & np.isfinite(seg_midi)
        voiced_frac = float(v.mean()) if len(v) else 0.0
        if v.any():
            played_midi_float = float(np.median(seg_midi[v]))
        else:
            played_midi_float = float(n["midi"])

        played_midi = int(round(_octave_snap(played_midi_float, n["midi"])))
        info = _midi_to_note(played_midi)
        cents = (played_midi_float - n["midi"]) * 100.0

        aligned.append(AlignedNote(
            index=idx,
            expected_midi=int(n["midi"]),
            expected_name=str(n.get("name_with_octave") or _midi_to_note(int(n["midi"]))["name_with_octave"]),
            start_sec=round(a_start * hop_sec, 3),
            end_sec=round(a_end * hop_sec, 3),
            played_midi=played_midi,
            played_name=info["name_with_octave"],
            pitch_diff_cents=round(cents, 1),
            voiced_fraction=round(voiced_frac, 3),
            status=_classify(cents, voiced_frac),
        ))

    correct = sum(1 for a in aligned if a.status == "correct")
    wrong = sum(1 for a in aligned if a.status == "wrong_pitch")
    missed = sum(1 for a in aligned if a.status == "missed")

    return {
        "audio_duration_sec": duration_sec,
        "tempo_bpm": tempo_bpm,
        "expected_count": len(expected_notes),
        "aligned_count": len(aligned),
        "summary": {"correct": correct, "wrong_pitch": wrong, "missed": missed},
        "notes": [a.__dict__ for a in aligned],
    }


def _octave_snap(played_midi: float, expected_midi: int) -> float:
    diff = played_midi - expected_midi
    if diff > 6:
        while played_midi - expected_midi > 6 and played_midi >= expected_midi + 12:
            played_midi -= 12
    elif diff < -6:
        while expected_midi - played_midi > 6 and played_midi <= expected_midi - 12:
            played_midi += 12
    return played_midi
