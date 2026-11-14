"""Assemble rendered 3D frames, narration, procedural SFX, and kinetic ASS captions into final MP4."""

from __future__ import annotations

import subprocess
from pathlib import Path


def assemble_short(
    frames_pattern: str,
    fps: int,
    narration_wav: Path,
    sfx_wav: Path,
    ass_path: Path,
    out_mp4: Path,
) -> Path:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    # Escape path for ffmpeg ass filter (handles spaces & colons safely)
    ass_escaped = str(ass_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    filter_complex = (
        f"[0:v]ass='{ass_escaped}',format=yuv420p[vout];"
        f"[1:a]aresample=48000,highpass=f=75,acompressor=threshold=-16dB:ratio=3:attack=5:release=60[nar];"
        f"[2:a]aresample=48000[sfx];"
        f"[nar][sfx]amix=inputs=2:duration=first:dropout_transition=0:weights=1.0 0.85,"
        f"loudnorm=I=-14:TP=-1.5:LRA=9[aout]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        frames_pattern,
        "-i",
        str(narration_wav),
        "-i",
        str(sfx_wav),
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "17",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        "-shortest",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    return out_mp4
