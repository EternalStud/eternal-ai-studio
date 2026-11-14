"""Generate POC #2 Hindi documentary narration and dynamic SFX bed."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio.sfx_gen import generate_doc_sfx_bed
from audio.tts_and_captions import synthesize_beats

STORY_BEATS = [
    {
        "id": "hook",
        "narration": "सिर्फ़ एक भूली हुई फ़ाइल, और पैंतालीस मिनट में तीन हज़ार छह सौ करोड़ रुपये स्वाहा!",
    },
    {
        "id": "setup",
        "narration": "एक अगस्त, दो हज़ार बारह। अमेरिका के शेयर बाज़ार का हर छठा ट्रेड यही कंपनी संभालती थी, नाइट कैपिटल!",
    },
    {
        "id": "deploy",
        "narration": "उस सुबह कंपनी ने अपने आठ सर्वर पर नया सॉफ्टवेयर अपडेट किया। सात सर्वर बिल्कुल ठीक चले।",
    },
    {
        "id": "bug",
        "narration": "पर आठवें सर्वर पर अपडेट डालना ही भूल गए! उसमें दो हज़ार तीन का भूला हुआ कोड जाग उठा!",
    },
    {
        "id": "chaos",
        "narration": "नतीजा? एक सेकंड में लाखों गलत ऑर्डर! सिस्टम महँगे दाम पर ख़रीदता रहा, और सस्ते में बेचता रहा!",
    },
    {
        "id": "fallout",
        "narration": "सिर्फ़ पैंतालीस मिनट में चार सौ चालीस मिलियन डॉलर का नुक़सान! सत्तरह साल की कंपनी एक दिन में तबाह हो गई।",
    },
    {
        "id": "lesson",
        "narration": "याद रखो, कोड में छोड़ा गया पुराना कचरा कभी सोता नहीं, वो बस ग़लत वक़्त का इंतज़ार करता है!",
    },
]


async def main() -> None:
    work_dir = ROOT / "build" / "poc2_audio"
    manifest = await synthesize_beats(
        STORY_BEATS,
        work_dir=work_dir,
        voice="hi-IN-MadhurNeural",
        rate="+20%",
        pitch="-2Hz",
        gap_ms=140,
    )

    beat_map = {b["beat_id"]: b for b in manifest["beats"]}
    beat_starts = [b["start_ms"] for b in manifest["beats"]]

    tick_events: list[tuple[int, float]] = []
    # Server deployment pings during 'deploy'
    dep = beat_map["deploy"]
    dep_span = max(1200, dep["duration_ms"] - 400)
    for k in range(7):
        tick_events.append((dep["start_ms"] + 250 + int(k * dep_span / 7), 1200.0 + k * 90.0))

    # Rapid order ticks during 'chaos'
    ch = beat_map["chaos"]
    for t in range(ch["start_ms"] + 150, ch["end_ms"] - 150, 175):
        tick_events.append((t, 2200.0 if (t // 175) % 2 == 0 else 1650.0))

    # Alarm pulses on 'bug' and 'chaos'
    bug = beat_map["bug"]
    alarm_events = [
        bug["start_ms"] + 200,
        bug["start_ms"] + int(bug["duration_ms"] * 0.55),
        ch["start_ms"] + 120,
        ch["start_ms"] + int(ch["duration_ms"] * 0.5),
    ]

    # Tension risers into bug and fallout
    riser_events = [
        (max(0, bug["start_ms"] - 1200), 1200),
        (max(0, ch["start_ms"] - 1000), 1000),
    ]

    sfx_wav = work_dir / "sfx_bed.wav"
    generate_doc_sfx_bed(
        manifest["total_ms"],
        beat_starts,
        tick_events,
        alarm_events,
        riser_events,
        sfx_wav,
    )
    manifest["sfx_wav"] = str(sfx_wav)
    (work_dir / "audio_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"TOTAL_MS={manifest['total_ms']} ({manifest['total_ms']/1000:.2f}s)")
    for b in manifest["beats"]:
        print(f"  {b['beat_id']:8s}: {b['start_ms']:5d} -> {b['end_ms']:5d} ({b['duration_ms']:4d}ms, {b['word_count']} words)")


if __name__ == "__main__":
    asyncio.run(main())
