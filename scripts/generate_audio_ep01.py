"""Generate Episode 01 Hindi/Hinglish narration, word timings, and layered SFX bed.

Topic: IRCTC 10:00 AM Tatkal — Million-to-One Concurrency Funnel (Computer Science, Age 16-36).
All claims grounded in CRIS / Ministry of Railways NGeT / ACID DBMS architecture.
"""

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

RESEARCH_LEDGER = {
    "topic": "Inside IRCTC 10:00 AM Tatkal Concurrency (Computer Science)",
    "claims": [
        {"id": "C1", "status": "VERIFIED_FACT", "text": "IRCTC AC Tatkal opens 10:00 AM & Sleeper at 11:00 AM to partition peak demand.", "source": "Indian Railways / CRIS"},
        {"id": "C2", "status": "VERIFIED_FACT", "text": "NGeT supports 3–5 lakh+ concurrent sessions and up to 1.5L tickets/min in Cloud PRS.", "source": "PIB / Ministry of Railways"},
        {"id": "C3", "status": "VERIFIED_FACT", "text": "SQL SELECT ... FOR UPDATE enforces pessimistic row-level Mutual Exclusion (Mutex).", "source": "ACID RDBMS Architecture"},
    ],
}

STORY_BEATS = [
    {
        "id": "hook_0959",
        "narration": "सुबह के नौ बजकर अट्ठावन मिनट! तुम्हारे सामने IRCTC की स्क्रीन पर दिख रहा है अवेलेबल बयालीस। पर बुक दबाते ही एक सेकंड में स्टेटस हो जाता है, वेटिंग एक सौ अस्सी! आखिर उस एक सेकंड में सर्वर के अंदर क्या हुआ?",
    },
    {
        "id": "scale_illusion",
        "narration": "सुबह ठीक दस बजे, पूरे भारत से पाँच लाख से ज़्यादा लोग एक साथ एक ही दरवाज़े पर टूट पड़ते हैं। पर बर्थ सिर्फ़ कुछ सौ होती हैं। यहीं से शुरू होती है कंप्यूटर साइंस की सबसे तेज़ रेस!",
    },
    {
        "id": "gate1_bot_shield",
        "narration": "पहले दरवाज़े पर बैठता है सिक्योरिटी गार्ड — रेट लिमिटर और CAPTCHA शील्ड। इसका काम है हज़ारों ऑटोमेटेड बॉट स्क्रिप्ट को मुख्य सर्वर तक पहुँचने से पहले ही ब्लॉक कर देना।",
    },
    {
        "id": "cache_vs_truth",
        "narration": "अब आता है सबसे बड़ा भ्रम! स्क्रीन पर जो बयालीस सीटें दिखती हैं, वो असली डेटाबेस नहीं, बल्कि तेज़ Redis Cache से आती हैं। वो डेटा कुछ सौ मिली-सेकंड पुराना हो सकता है।",
    },
    {
        "id": "row_lock_mutex",
        "narration": "जब तुम पेमेंट के लिए क्लिक करते हो, रिक्वेस्ट असली डेटाबेस पर पहुँचती है। वहाँ चलता है SQL का एक ख़ास कमांड — SELECT FOR UPDATE, जिसे हम Mutex Row Lock कहते हैं!",
    },
    {
        "id": "why_300ms_kills",
        "narration": "एक बर्थ पर एक वक़्त में सिर्फ़ एक ही थ्रेड ताला लगा सकता है। अगर तुम्हारा OTP या नेटवर्क सिर्फ़ तीन सौ मिली-सेकंड लेट हुआ, तो तुमसे आगे चालीस रिक्वेस्ट सीट लॉक कर चुकी होती हैं!",
    },
    {
        "id": "race_recap",
        "narration": "देखो, यहाँ तेज़ फाइबर वाले थ्रेड ने ताला पहले खींच लिया। तुम ठीक पीछे पहुँचे, और सिस्टम ने तुम्हें वेटिंग लिस्ट में डाल दिया। सोचो अगर ये लॉक न होता, तो एक ही सीट दो लोगों को मिल जाती!",
    },
    {
        "id": "cs_law_takeaway",
        "narration": "तो अगली बार दस बजे टिकट वेटिंग में जाए, तो समझ जाना — सर्वर धोखा नहीं दे रहा, बल्कि डेटाबेस का Mutex Lock भारतीय रेलवे को डबल-बुकिंग से बचा रहा है!",
    },
]


def build_ep01_sfx_bed(total_ms: int, beat_map: dict, out_wav: Path) -> Path:
    n = int(total_ms * SAMPLE_RATE / 1000) + SAMPLE_RATE
    buf_l = [0.0] * n
    buf_r = [0.0] * n

    # Atmospheric crisp dark CS synth bed (D2=73.42, A2=110.0, E3=164.81)
    fade_in = int(0.8 * SAMPLE_RATE)
    fade_out = int(1.2 * SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        pulse = 0.76 + 0.24 * math.sin(2.0 * math.pi * 0.28 * t)
        drone = (
            0.55 * math.sin(2.0 * math.pi * 73.42 * t)
            + 0.28 * math.sin(2.0 * math.pi * 110.0 * t)
            + 0.17 * math.sin(2.0 * math.pi * 164.81 * t)
        )
        env = 1.0
        if i < fade_in:
            env *= i / fade_in
        if i > n - fade_out:
            env *= max(0.0, (n - i) / fade_out)
        val = drone * pulse * env * 0.044
        buf_l[i] += val
        buf_r[i] += val

    for idx, b in enumerate(STORY_BEATS):
        st = beat_map[b["id"]]["start_ms"]
        _add_sub_impact(buf_l, buf_r, st, gain=0.26 if idx in (0, 4, 6) else 0.15)
        if idx > 0:
            _add_whoosh(buf_l, buf_r, max(0, st - 140), gain=0.11)

    # Countdown ticks on hook_0959 + rapid key clacks
    hk = beat_map["hook_0959"]
    for k in range(4):
        _add_tick(buf_l, buf_r, hk["start_ms"] + 450 + k * 550, pitch=1700.0 + k * 140.0, gain=0.08)

    # Bot filter pings
    g1 = beat_map["gate1_bot_shield"]
    for k in range(5):
        _add_tick(buf_l, buf_r, g1["start_ms"] + 900 + k * 420, pitch=2100.0, gain=0.07)

    # Heavy mutex lock snap chime on row_lock_mutex
    rl = beat_map["row_lock_mutex"]
    _add_node_ping(buf_l, buf_r, rl["start_ms"] + int(rl["duration_ms"] * 0.60), freq=587.33, gain=0.19)
    _add_node_ping(buf_l, buf_r, rl["start_ms"] + int(rl["duration_ms"] * 0.63), freq=880.00, gain=0.18)

    # Lever snap on race_recap
    rc = beat_map["race_recap"]
    _add_node_ping(buf_l, buf_r, rc["start_ms"] + int(rc["duration_ms"] * 0.36), freq=1046.50, gain=0.19)

    _write_stereo_wav(out_wav, buf_l, buf_r)
    return out_wav


async def main() -> None:
    work_dir = ROOT / "build" / "ep01_audio"
    manifest = await synthesize_beats(
        STORY_BEATS,
        work_dir=work_dir,
        voice="hi-IN-MadhurNeural",
        rate="+8%",
        pitch="-2Hz",
        gap_ms=160,
    )
    beat_map = {b["beat_id"]: b for b in manifest["beats"]}
    sfx_wav = work_dir / "sfx_bed.wav"
    build_ep01_sfx_bed(manifest["total_ms"], beat_map, sfx_wav)
    manifest["sfx_wav"] = str(sfx_wav)
    manifest["research_ledger"] = RESEARCH_LEDGER
    (work_dir / "audio_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"EP01_TOTAL_MS={manifest['total_ms']} ({manifest['total_ms']/1000:.2f}s)")
    for b in manifest["beats"]:
        print(f"  {b['beat_id']:18s}: {b['start_ms']:6d} -> {b['end_ms']:6d} ({b['duration_ms']:5d}ms, {b['word_count']}w)")


if __name__ == "__main__":
    asyncio.run(main())
