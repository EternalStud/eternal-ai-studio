"""Generate synchronized audio, SFX, and kinetic captions for POC #1 (UPI vs Legacy Banks)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from audio.sfx_gen import generate_sfx_bed
from audio.tts_and_captions import synthesize_beats

BEATS = [
    {
        "id": "hook",
        "narration": "Why does a traditional bank wire take two days... while a UPI payment settles in less than one second?",
    },
    {
        "id": "legacy_batch",
        "narration": "Old banking systems don't move money continuously. Your transfer gets trapped inside batch queues, locked behind clearing windows and middleman ledgers.",
    },
    {
        "id": "instant_rail",
        "narration": "UPI flips the architecture. An encrypted token leaves your phone, hits your app node, routes through the central switch, and credits the receiver bank live, in four atomic hops.",
    },
    {
        "id": "payoff",
        "narration": "Zero batch delays. Zero middleman stalls. That is how real-time packet routing replaced two days of waiting.",
    },
]


async def main() -> None:
    work_dir = ROOT / "tmp" / "poc1_upi"
    manifest = await synthesize_beats(
        BEATS,
        work_dir=work_dir,
        voice="en-US-AndrewMultilingualNeural",
        rate="+7%",
        gap_ms=260,
    )

    beat_starts = [b["start_ms"] for b in manifest["beats"]]
    # Place 4 rising node-ping SFX during the instant_rail beat (hop 1 -> hop 4)
    rail = manifest["beats"][2]
    rail_span = rail["duration_ms"]
    ping_events = [
        (rail["start_ms"] + int(rail_span * 0.22), 587.33),  # D5
        (rail["start_ms"] + int(rail_span * 0.44), 659.25),  # E5
        (rail["start_ms"] + int(rail_span * 0.66), 783.99),  # G5
        (rail["start_ms"] + int(rail_span * 0.86), 1046.50), # C6 (settled!)
    ]
    sfx_wav = work_dir / "sfx_bed.wav"
    generate_sfx_bed(
        total_ms=manifest["total_ms"],
        beat_starts_ms=beat_starts,
        ping_events_ms=ping_events,
        out_wav=sfx_wav,
    )
    manifest["sfx_wav"] = str(sfx_wav)
    manifest["ping_events_ms"] = [p[0] for p in ping_events]
    (work_dir / "audio_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
