"""Procedural royalty-free sound design generator (ambient pad, impact, data ticks, whoosh)."""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 48000


def _write_stereo_wav(path: Path, samples_l: list[float], samples_r: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for l_val, r_val in zip(samples_l, samples_r):
            li = max(-32767, min(32767, int(l_val * 32767.0)))
            ri = max(-32767, min(32767, int(r_val * 32767.0)))
            frames.extend(struct.pack("<hh", li, ri))
        wf.writeframes(bytes(frames))


def _add_sub_impact(buf_l: list[float], buf_r: list[float], at_ms: int, gain: float = 0.35) -> None:
    start = int(at_ms * SAMPLE_RATE / 1000)
    dur_samples = int(0.45 * SAMPLE_RATE)
    for i in range(dur_samples):
        idx = start + i
        if idx >= len(buf_l):
            break
        t = i / SAMPLE_RATE
        freq = 110.0 * math.exp(-t * 8.5) + 38.0
        env = math.exp(-t * 9.0) * (1.0 - math.exp(-t * 250.0))
        val = math.sin(2.0 * math.pi * freq * t) * env * gain
        buf_l[idx] += val
        buf_r[idx] += val


def _add_node_ping(
    buf_l: list[float], buf_r: list[float], at_ms: int, freq: float = 880.0, gain: float = 0.16
) -> None:
    start = int(at_ms * SAMPLE_RATE / 1000)
    dur_samples = int(0.28 * SAMPLE_RATE)
    for i in range(dur_samples):
        idx = start + i
        if idx >= len(buf_l):
            break
        t = i / SAMPLE_RATE
        env = math.exp(-t * 14.0) * (1.0 - math.exp(-t * 600.0))
        val = (
            0.7 * math.sin(2.0 * math.pi * freq * t)
            + 0.3 * math.sin(2.0 * math.pi * (freq * 1.5) * t)
        ) * env * gain
        buf_l[idx] += val * 0.95
        buf_r[idx] += val * 1.05


def _add_whoosh(buf_l: list[float], buf_r: list[float], at_ms: int, gain: float = 0.14) -> None:
    start = int(at_ms * SAMPLE_RATE / 1000)
    dur_samples = int(0.35 * SAMPLE_RATE)
    rng = random.Random(at_ms)
    lp = 0.0
    for i in range(dur_samples):
        idx = start + i
        if idx >= len(buf_l):
            break
        t = i / SAMPLE_RATE
        norm = i / dur_samples
        env = math.sin(math.pi * norm) ** 1.6
        cutoff = 0.03 + 0.25 * math.sin(math.pi * norm)
        noise = rng.uniform(-1.0, 1.0)
        lp = lp + cutoff * (noise - lp)
        val = lp * env * gain
        pan = 0.5 + 0.3 * math.cos(math.pi * norm)
        buf_l[idx] += val * pan
        buf_r[idx] += val * (1.0 - pan)


def generate_sfx_bed(
    total_ms: int,
    beat_starts_ms: list[int],
    ping_events_ms: list[tuple[int, float]],
    out_wav: Path,
) -> Path:
    """Synthesize a dark minimalist tech ambient bed + beat impacts + node pings."""
    n = int(total_ms * SAMPLE_RATE / 1000) + SAMPLE_RATE
    buf_l = [0.0] * n
    buf_r = [0.0] * n

    # Subtle warm sub-drone + fifth harmonic (D2 = 73.42Hz, A2 = 110Hz)
    fade_in = int(0.8 * SAMPLE_RATE)
    fade_out = int(1.0 * SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        lfo = 0.75 + 0.25 * math.sin(2.0 * math.pi * 0.22 * t)
        drone = (
            0.55 * math.sin(2.0 * math.pi * 73.42 * t)
            + 0.30 * math.sin(2.0 * math.pi * 110.0 * t)
            + 0.15 * math.sin(2.0 * math.pi * 146.83 * t)
        )
        env = 1.0
        if i < fade_in:
            env *= i / fade_in
        if i > n - fade_out:
            env *= max(0.0, (n - i) / fade_out)
        val = drone * lfo * env * 0.045
        buf_l[i] += val
        buf_r[i] += val

    for idx, b_ms in enumerate(beat_starts_ms):
        _add_sub_impact(buf_l, buf_r, b_ms, gain=0.28 if idx == 0 else 0.22)
        if idx > 0:
            _add_whoosh(buf_l, buf_r, max(0, b_ms - 140), gain=0.12)

    for p_ms, freq in ping_events_ms:
        _add_node_ping(buf_l, buf_r, p_ms, freq=freq, gain=0.17)

    _write_stereo_wav(out_wav, buf_l, buf_r)
    return out_wav


def _add_tick(buf_l: list[float], buf_r: list[float], at_ms: int, pitch: float = 1900.0, gain: float = 0.09) -> None:
    start = int(at_ms * SAMPLE_RATE / 1000)
    dur_samples = int(0.035 * SAMPLE_RATE)
    for i in range(dur_samples):
        idx = start + i
        if idx >= len(buf_l):
            break
        t = i / SAMPLE_RATE
        env = math.exp(-t * 140.0)
        val = math.sin(2.0 * math.pi * pitch * t) * env * gain
        buf_l[idx] += val
        buf_r[idx] += val


def _add_alarm_pulse(buf_l: list[float], buf_r: list[float], at_ms: int, gain: float = 0.14) -> None:
    start = int(at_ms * SAMPLE_RATE / 1000)
    dur_samples = int(0.30 * SAMPLE_RATE)
    for i in range(dur_samples):
        idx = start + i
        if idx >= len(buf_l):
            break
        t = i / SAMPLE_RATE
        env = math.sin(math.pi * (i / dur_samples)) ** 1.2 * math.exp(-t * 4.5)
        freq = 540.0 if t < 0.14 else 415.0
        val = (0.75 * math.sin(2.0 * math.pi * freq * t) + 0.25 * math.sin(2.0 * math.pi * freq * 2.0 * t)) * env * gain
        buf_l[idx] += val * 1.05
        buf_r[idx] += val * 0.95


def _add_riser(buf_l: list[float], buf_r: list[float], start_ms: int, dur_ms: int = 1800, gain: float = 0.12) -> None:
    start = int(start_ms * SAMPLE_RATE / 1000)
    dur_samples = int(dur_ms * SAMPLE_RATE / 1000)
    phase = 0.0
    for i in range(dur_samples):
        idx = start + i
        if idx >= len(buf_l):
            break
        norm = i / max(1, dur_samples)
        freq = 90.0 + 380.0 * (norm ** 2.2)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        env = (norm ** 1.8) * (1.0 if norm < 0.94 else max(0.0, (1.0 - norm) / 0.06))
        val = math.sin(phase) * env * gain
        buf_l[idx] += val
        buf_r[idx] += val


def generate_doc_sfx_bed(
    total_ms: int,
    beat_starts_ms: list[int],
    tick_events_ms: list[tuple[int, float]],
    alarm_events_ms: list[int],
    riser_events: list[tuple[int, int]],
    out_wav: Path,
) -> Path:
    """Synthesize dramatic documentary sound bed: dark minor drone, booms, risers, ticks, alarms."""
    n = int(total_ms * SAMPLE_RATE / 1000) + SAMPLE_RATE
    buf_l = [0.0] * n
    buf_r = [0.0] * n

    # Tense minor suspense pulse (D2=73.42, F2=87.31, A2=110.0)
    fade_in = int(0.5 * SAMPLE_RATE)
    fade_out = int(0.9 * SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        pulse = 0.72 + 0.28 * math.sin(2.0 * math.pi * 1.25 * t)
        drone = (
            0.52 * math.sin(2.0 * math.pi * 73.42 * t)
            + 0.28 * math.sin(2.0 * math.pi * 87.31 * t)
            + 0.20 * math.sin(2.0 * math.pi * 110.0 * t)
        )
        env = 1.0
        if i < fade_in:
            env *= i / fade_in
        if i > n - fade_out:
            env *= max(0.0, (n - i) / fade_out)
        val = drone * pulse * env * 0.055
        buf_l[i] += val
        buf_r[i] += val

    for idx, b_ms in enumerate(beat_starts_ms):
        _add_sub_impact(buf_l, buf_r, b_ms, gain=0.34 if idx in (0, 3, 4) else 0.24)
        if idx > 0:
            _add_whoosh(buf_l, buf_r, max(0, b_ms - 130), gain=0.14)

    for t_ms, pitch in tick_events_ms:
        _add_tick(buf_l, buf_r, t_ms, pitch=pitch, gain=0.10)

    for a_ms in alarm_events_ms:
        _add_alarm_pulse(buf_l, buf_r, a_ms, gain=0.13)

    for r_start, r_dur in riser_events:
        _add_riser(buf_l, buf_r, r_start, dur_ms=r_dur, gain=0.13)

    _write_stereo_wav(out_wav, buf_l, buf_r)
    return out_wav
