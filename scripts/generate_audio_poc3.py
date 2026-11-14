"""Generate POC #3 warm conversational Hindi narration and atmospheric SFX bed."""

from __future__ import annotations

import asyncio
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio.sfx_gen import SAMPLE_RATE, _add_node_ping, _add_sub_impact, _add_tick, _add_whoosh, _write_stereo_wav
from audio.tts_and_captions import synthesize_beats

STORY_BEATS = [
    {
        "id": "underground_hook",
        "narration": "इस वक़्त, सड़क की ज़मीन से पाँच फ़ीट नीचे दबी एक फाइबर केबल में रोशनी की किरण दौड़ रही है, दो लाख किलोमीटर प्रति सेकंड की रफ़्तार से।",
    },
    {
        "id": "tapri_intro",
        "narration": "यह रोशनी तुम्हारे अभी-अभी किए गए बीस रुपये के चाय वाले पेमेंट का डेटा है। सफ़र शुरू होता है बारिश की शाम, नुक्कड़ की चाय टपरी से।",
    },
    {
        "id": "qr_repair",
        "narration": "जैसे ही कैमरा क्यूआर कोड पर जाता है, कोड के तीन कोने दिशा पहचानते हैं। ऊपर चाय गिर भी जाए, तब भी तीस प्रतिशत बैकअप डेटा इसे पढ़ लेता है।",
    },
    {
        "id": "encrypt_tower",
        "narration": "पे दबाते ही फ़ोन डेटा को लॉक करता है, और रेडियो तरंगों से इसे पास के मोबाइल टावर तक भेज देता है।",
    },
    {
        "id": "npci_grid",
        "narration": "टावर से डेटा ज़मीन के फाइबर हाईवे पर उतरता है, और पहुँचता है एनपीसीआई स्विच में, जहाँ दोनों बैंक तीन तरफ़ा मुहर लगाते हैं।",
    },
    {
        "id": "soundbox",
        "narration": "मंज़ूरी मिलते ही सिग्नल टपरी के साउंडबॉक्स तक लौटता है, और स्पीकर गूँज उठता है, बीस रुपये प्राप्त हुए!",
    },
    {
        "id": "finale_layers",
        "narration": "रेडियो वेव, फाइबर केबल, लॉक, एनपीसीआई और साउंडबॉक्स। सब कुछ सिर्फ़ आठ सौ मिलीसेकंड में।",
    },
]


def build_warm_sfx_bed(total_ms: int, beat_map: dict, out_wav: Path) -> Path:
    n = int(total_ms * SAMPLE_RATE / 1000) + SAMPLE_RATE
    buf_l = [0.0] * n
    buf_r = [0.0] * n

    # Warm lush ambient cinema drone (C2=65.41Hz, G2=98.0Hz, D3=146.83Hz) — smooth & calm
    fade_in = int(1.0 * SAMPLE_RATE)
    fade_out = int(1.2 * SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        breath = 0.78 + 0.22 * math.sin(2.0 * math.pi * 0.18 * t)
        pad = (
            0.55 * math.sin(2.0 * math.pi * 65.41 * t)
            + 0.28 * math.sin(2.0 * math.pi * 98.00 * t)
            + 0.17 * math.sin(2.0 * math.pi * 146.83 * t)
        )
        env = 1.0
        if i < fade_in:
            env *= i / fade_in
        if i > n - fade_out:
            env *= max(0.0, (n - i) / fade_out)
        val = pad * breath * env * 0.048
        buf_l[i] += val
        buf_r[i] += val

    # Soft scene transition whooshes & deep booms (restrained, polished)
    for idx, bid in enumerate(["underground_hook", "tapri_intro", "qr_repair", "encrypt_tower", "npci_grid", "soundbox", "finale_layers"]):
        st = beat_map[bid]["start_ms"]
        _add_sub_impact(buf_l, buf_r, st, gain=0.22 if idx in (0, 4, 5) else 0.14)
        if idx > 0:
            _add_whoosh(buf_l, buf_r, max(0, st - 150), gain=0.10)

    # QR focus subtle ticks
    qr = beat_map["qr_repair"]
    for k in range(3):
        _add_tick(buf_l, buf_r, qr["start_ms"] + 600 + k * 420, pitch=1450.0 + k * 180.0, gain=0.07)

    # Lock click
    enc = beat_map["encrypt_tower"]
    _add_node_ping(buf_l, buf_r, enc["start_ms"] + int(enc["duration_ms"] * 0.38), freq=660.0, gain=0.14)

    # 3-way NPCI verification chimes
    npci = beat_map["npci_grid"]
    for k, f in enumerate([523.25, 659.25, 783.99]):
        _add_node_ping(buf_l, buf_r, npci["start_ms"] + int(npci["duration_ms"] * (0.45 + k * 0.16)), freq=f, gain=0.15)

    # Iconic Soundbox dual-chime ding! (C6 + E6)
    sb = beat_map["soundbox"]
    ding_t = sb["start_ms"] + int(sb["duration_ms"] * 0.56)
    _add_node_ping(buf_l, buf_r, ding_t, freq=1046.50, gain=0.20)
    _add_node_ping(buf_l, buf_r, ding_t + 160, freq=1318.51, gain=0.22)

    _write_stereo_wav(out_wav, buf_l, buf_r)
    return out_wav


async def main() -> None:
    work_dir = ROOT / "build" / "poc3_audio"
    manifest = await synthesize_beats(
        STORY_BEATS,
        work_dir=work_dir,
        voice="hi-IN-MadhurNeural",
        rate="+8%",
        pitch="-3Hz",
        gap_ms=260,
    )
    beat_map = {b["beat_id"]: b for b in manifest["beats"]}
    sfx_wav = work_dir / "sfx_bed.wav"
    build_warm_sfx_bed(manifest["total_ms"], beat_map, sfx_wav)
    manifest["sfx_wav"] = str(sfx_wav)
    (work_dir / "audio_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"POC3_TOTAL_MS={manifest['total_ms']} ({manifest['total_ms']/1000:.2f}s)")
    for b in manifest["beats"]:
        print(f"  {b['beat_id']:17s}: {b['start_ms']:5d} -> {b['end_ms']:5d} ({b['duration_ms']:4d}ms)")


if __name__ == "__main__":
    asyncio.run(main())
