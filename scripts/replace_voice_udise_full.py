"""Replace voiceover on the 17m11s Final Cut Pro UDISE+ Automation video with studio-clear Hindi TTS.

Preserves exact original video stream (-c:v copy, 1920x960 @ 60fps) with zero visual quality loss,
and replaces audio with time-locked, confident, noise-free hi-IN-MadhurNeural narration (-14 LUFS).
"""

from __future__ import annotations

import asyncio
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import edge_tts
from audio.sfx_gen import SAMPLE_RATE, _write_stereo_wav
from audio.tts_and_captions import _probe_duration_ms

INPUT_MOV = ROOT / "input" / "udise+ automation GP, PEN search , Udise Import.mov"
OUT_MP4 = ROOT / "output" / "udise_automation_full_clean_voice.mp4"
WORK_DIR = ROOT / "build" / "udise_edit" / "full_voice"

# Time-locked studio Hindi narration segments faithfully matching every chapter & screen demo of the 17m11s video
SEGMENTS = [
    (
        1.0,
        "स्वागत है हमारे चैनल इटरनल स्टूडेंट में! आज के इस वीडियो में हम सीखेंगे कि यू-डाइस प्लस पर जनरल प्रोफ़ाइल अपडेट, पेन नंबर सर्च, और स्टूडेंट्स इम्पोर्ट — ये तीनों काम बल्क में और ऑटोमेटिक तरीके से कैसे करें।",
    ),
    (
        26.0,
        "पहले हम यही काम पायथन और सेलेनियम स्क्रिप्ट से करते थे, जहाँ ब्राउज़र आपके सामने खुलता था और एक्सेल से एक-एक फ़ील्ड भरकर सेव करता था। अब वही पूरा प्रोसेस ए-पी-आई के ज़रिए सीधे बैकग्राउंड में, और भी तेज़ चलता है।",
    ),
    (
        68.0,
        "इसे गूगल कोलैब पर बनाने का मुख्य कारण यह था कि लोकल कंप्यूटर पर पायथन और सेलेनियम इंस्टॉल करने में नॉन-टेक्निकल टीचर्स को काफ़ी परेशानी आती थी। विंडोज़ और मैक के अलग-अलग सेटअप में एरर आ जाते थे।",
    ),
    (
        112.0,
        "लेकिन अब इस गूगल कोलैब नोटबुक को कोई भी टीचर या स्कूल एडमिनिस्ट्रेटर बिना किसी सॉफ्टवेयर इंस्टॉलेशन के बड़ी आसानी से चला सकता है। आपको बस अपने ब्राउज़र से सिर्फ़ तीन चीज़ें कॉपी करनी हैं — पहली कुकी, दूसरा स्कूल आई-डी यू-आर-एल, और तीसरी एन्क्रिप्ट की।",
    ),
    (
        162.0,
        "स्क्रीन पर दिख रही यह पी-डी-एफ़ गाइड मैंने टेलीग्राम ग्रुप में शेयर कर दी है। आप वहाँ से स्टेप-बाय-स्टेप रेफरेंस और कोलैब नोटबुक का डायरेक्ट लिंक ले सकते हैं।",
    ),
    (
        196.0,
        "अब लिंक को नए टैब में ओपन करते ही नोटबुक कुछ इस तरह खुलेगी। सबसे पहले ऊपर दाईं तरफ़ दिए गए कनेक्ट बटन पर क्लिक करें। इससे गूगल आपको फ्री में क्लाउड सर्वर, रैम और डिस्क स्पेस दे देता है, जिस पर हमारा पूरा ऑटोमेशन चलेगा।",
    ),
    (
        255.0,
        "कनेक्ट होते ही ऊपर रैम और डिस्क दिखने लगेगा। अब बाईं तरफ़ दिए छोटे एरो आइकन पर क्लिक करके आप किसी भी सेक्शन को एक्सपैंड या कोलैप्स कर सकते हैं — जैसे सेटअप एनवायरनमेंट, ऑथेंटिकेशन, डिटेक्ट स्कूल, जनरल प्रोफ़ाइल अपडेट, और बल्क इम्पोर्ट।",
    ),
    (
        312.0,
        "सबसे पहले सेटअप एनवायरनमेंट वाले सेल को रन करें। गूगल एक स्टैंडर्ड सिक्योरिटी वॉर्निंग दिखाएगा। यहाँ रन एनीवे पर क्लिक करें, क्योंकि यह टूल आपसे कभी भी आपका यू-डाइस आई-डी या पासवर्ड नहीं माँगता — यह केवल आपके टेम्पररी ब्राउज़र सेशन कुकी का उपयोग करता है।",
    ),
    (
        372.0,
        "सेटअप पूरा होने के बाद अगला स्टेप है ऑथेंटिकेशन। इस सेल को रन करने पर यह आपसे यू-डाइस प्लस की कुकी माँगेगा। आइए देखते हैं कि अपने ब्राउज़र से यह कुकी कैसे निकालनी है।",
    ),
    (
        412.0,
        "सबसे पहले अपने ब्राउज़र में यू-डाइस प्लस के स्टूडेंट मॉड्यूल में लॉगिन कर लें। अब पेज पर कहीं भी राइट-क्लिक करके इंस्पेक्ट चुनें, या कीबोर्ड से एफ़-बारह दबाएँ, और ऊपर दिए नेटवर्क टैब पर क्लिक करें।",
    ),
    (
        466.0,
        "अब यू-डाइस में एक्टिव स्टूडेंट्स या स्कूल डैशबोर्ड पर क्लिक करें। नेटवर्क टैब में कई रिक्वेस्ट दिखेंगी — उनमें से किसी भी एक रिक्वेस्ट पर क्लिक करें और रिक्वेस्ट हेडर्स में सबसे नीचे स्क्रॉल करें।",
    ),
    (
        506.0,
        "यहाँ आपको कुकी के सामने जे-सेशन-आई-डी से शुरू होने वाली पूरी स्ट्रिंग दिखेगी। इस पूरी स्ट्रिंग को कॉपी करें और कोलैब के ऑथेंटिकेशन बॉक्स में पेस्ट कर दें। ध्यान रखें, जैसे ही आप यू-डाइस से लॉगआउट करेंगे, यह सेशन अपने आप एक्सपायर हो जाता है।",
    ),
    (
        552.0,
        "अगला स्टेप है डिटेक्ट स्कूल। इस सेल को रन करें और अपने यू-डाइस स्कूल डैशबोर्ड का ऊपर वाला यू-आर-एल कॉपी करके यहाँ पेस्ट कर दें। इससे टूल को आपके स्कूल की यूनिक आई-डी तुरंत मिल जाती है।",
    ),
    (
        595.0,
        "अब देखते हैं बल्क पेन सर्च मॉड्यूल, जिससे आप आधार नंबर और डेट ऑफ़ बर्थ के ज़रिए सैकड़ों बच्चों का पेन नंबर एक साथ निकाल सकते हैं। इसके लिए कुकी के साथ एक एन्क्रिप्ट की चाहिए, क्योंकि पोर्टल पर आधार नंबर एन्क्रिप्ट होकर जाता है।",
    ),
    (
        652.0,
        "एन्क्रिप्ट की निकालने के लिए नोटबुक में दिया गया एक लाइन का कोड कॉपी करें। फिर यू-डाइस टैब में एफ़-बारह दबाकर कंसोल टैब खोलें, कोड पेस्ट करके एंटर दबाएँ। की अपने आप आपके क्लिपबोर्ड में कॉपी हो जाएगी।",
    ),
    (
        702.0,
        "अब इस एन्क्रिप्ट की और कुकी हेडर को पेन सर्च सेल में पेस्ट करें और रन करें। एक अपलोड बटन खुलेगा — वहाँ अपनी एक्सेल फ़ाइल अपलोड करें जिसमें आधार और डेट ऑफ़ बर्थ हो। टूल कॉलम और डेट फ़ॉर्मेट खुद पहचानकर सभी बच्चों के पेन नंबर निकाल देगा।",
    ),
    (
        754.0,
        "अगला मॉड्यूल है यू-डाइस प्लस बल्क स्टूडेंट इम्पोर्ट। इसमें वही ज़रूरी कॉलम लगते हैं जो मैनुअल इम्पोर्ट में चाहिए — पेन नंबर, डेट ऑफ़ बर्थ, क्लास, सेक्शन और डेट ऑफ़ एडमिशन। यह टूल पहले हर बच्चे की एलिजिबिलिटी चेक करता है।",
    ),
    (
        798.0,
        "जो बच्चे एलिजिबल हैं, उन्हें सीधे इम्पोर्ट कर देता है, और जो इम्पोर्ट नहीं हो पाए, उनके लिए एक्सेल रिपोर्ट में साफ़ कारण लिख देता है — जैसे नॉट फ़ाउंड, आपके स्कूल में पहले से एक्टिव, या किसी दूसरे स्कूल में एक्टिव और ड्रॉपबॉक्स में नहीं है।",
    ),
    (
        844.0,
        "अब सबसे ज़्यादा इस्तेमाल होने वाला मॉड्यूल — जनरल प्रोफ़ाइल बल्क अपडेट! पहले फेच करंट एकेडमिक सेशन स्टूडेंट्स रन करें। यह आपके स्कूल के सभी एडमिटेड बच्चों का डेटा फेच करके एक प्री-फ़िल्ड एक्सेल शीट तैयार कर देगा।",
    ),
    (
        896.0,
        "उस एक्सेल में आप जिस कॉलम को बदलना चाहते हैं, उसे आसानी से ड्रैग-एंड-ड्रॉप करके अपडेट करें, फ़ाइल सेव करें, और फिर स्टेप-बाय-स्टेप अपलोड, वैलिडेट और सबमिट वाले सेल रन कर दें। पचानवे प्रतिशत से ज़्यादा बच्चों का डेटा ऑटोमेटिक अपडेट हो जाता है!",
    ),
    (
        942.0,
        "पिछली बार हमने इसी टूल से सात सौ चौबीस बच्चों का जनरल प्रोफ़ाइल मात्र तीस मिनट में पूरा अपडेट कर दिया था! इसमें किसी प्रोग्रामिंग की ज़रूरत नहीं — बस सिंपल कॉपी-पेस्ट और थोड़ी सी एक्सेल जानकारी काफ़ी है।",
    ),
    (
        980.0,
        "आगे चलकर एनरोलमेंट प्रोफ़ाइल और फैसिलिटी प्रोफ़ाइल के अपडेट भी इसी लिंक में अपने आप जुड़ जाएँगे, इसलिए इस लिंक को सेव रखें। कोई भी दिक्कत आए तो हमारे टेलीग्राम चैनल पर स्क्रीनशॉट शेयर करें। वीडियो देखने के लिए बहुत-बहुत धन्यवाद!",
    ),
]


async def synth_segment(text: str, out_mp3: Path) -> int:
    comm = edge_tts.Communicate(
        text,
        voice="hi-IN-MadhurNeural",
        rate="+10%",
        pitch="-1Hz",
        boundary="WordBoundary",
    )
    last_end_ms = 0
    with open(out_mp3, "wb") as fp:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                fp.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                end_ms = int((ch["offset"] + ch["duration"]) // 10_000)
                if end_ms > last_end_ms:
                    last_end_ms = end_ms
    dur_ms = _probe_duration_ms(out_mp3)
    return min(dur_ms, last_end_ms + 180) if last_end_ms > 0 else dur_ms


def build_subtle_pad(total_sec: float, out_wav: Path) -> None:
    """Whisper-quiet warm harmonic studio bed (-33 dB) so pauses feel polished, never dead."""
    n = int(math.ceil(total_sec * SAMPLE_RATE))
    # Build 10-second seamless loop and tile via ffmpeg (fast & low RAM for 17-min audio!)
    loop_sec = 10.0
    ln = int(loop_sec * SAMPLE_RATE)
    buf_l = [0.0] * ln
    buf_r = [0.0] * ln
    for i in range(ln):
        t = i / SAMPLE_RATE
        breath = 0.85 + 0.15 * math.sin(2.0 * math.pi * 0.1 * t)
        pad = (
            0.55 * math.sin(2.0 * math.pi * 110.0 * t)
            + 0.28 * math.sin(2.0 * math.pi * 164.81 * t)
            + 0.17 * math.sin(2.0 * math.pi * 220.0 * t)
        )
        v = pad * breath * 0.015
        buf_l[i] = v
        buf_r[i] = v
    loop_wav = out_wav.parent / "pad_loop_10s.wav"
    _write_stereo_wav(loop_wav, buf_l, buf_r)
    subprocess.run(
        [
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(loop_wav),
            "-t", f"{total_sec:.3f}",
            "-af", f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(0, total_sec-2.0):.2f}:d=2.0",
            str(out_wav),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


async def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    total_sec = _probe_duration_ms(INPUT_MOV) / 1000.0
    print(f"INPUT_DURATION={total_sec:.2f}s ({len(SEGMENTS)} segments)", flush=True)

    placed: list[tuple[Path, int, int]] = []
    prev_end_ms = 0
    for idx, (target_sec, text) in enumerate(SEGMENTS):
        mp3 = WORK_DIR / f"seg_{idx:02d}.mp3"
        eff_ms = await synth_segment(text, mp3)
        start_ms = max(int(target_sec * 1000), prev_end_ms + 380)
        # Keep inside total video duration
        if start_ms + eff_ms > int(total_sec * 1000) - 300:
            start_ms = max(prev_end_ms + 200, int(total_sec * 1000) - eff_ms - 300)
        placed.append((mp3, start_ms, eff_ms))
        prev_end_ms = start_ms + eff_ms
        print(f"  seg_{idx:02d}: {start_ms/1000:6.1f}s -> {prev_end_ms/1000:6.1f}s ({eff_ms/1000:4.1f}s)", flush=True)
        await asyncio.sleep(0.08)

    pad_wav = WORK_DIR / "ambient_pad.wav"
    build_subtle_pad(total_sec, pad_wav)

    # Mix all 22 voice segments + subtle pad into mastered 48kHz stereo WAV
    master_wav = WORK_DIR / "master_voice_14lufs.wav"
    cmd = ["ffmpeg", "-y", "-i", str(pad_wav)]
    f_parts = ["[0:a]aresample=48000[pad]"]
    labels = ["[pad]"]
    for idx, (mp3, delay_ms, eff_ms) in enumerate(placed):
        inp_i = idx + 1
        cmd.extend(["-i", str(mp3)])
        lbl = f"v{idx}"
        eff_s = eff_ms / 1000.0
        fade_st = max(0.0, eff_s - 0.04)
        f_parts.append(
            f"[{inp_i}:a]atrim=0:{eff_s:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=out:st={fade_st:.3f}:d=0.04,"
            f"highpass=f=75,acompressor=threshold=-16dB:ratio=3:attack=5:release=60,"
            f"adelay={delay_ms}|{delay_ms},aresample=48000[{lbl}]"
        )
        labels.append(f"[{lbl}]")

    f_parts.append(
        f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:dropout_transition=0:normalize=0,"
        f"loudnorm=I=-14:TP=-1.5:LRA=9[aout]"
    )
    cmd.extend(["-filter_complex", ";".join(f_parts), "-map", "[aout]", "-t", f"{total_sec:.3f}", str(master_wav)])
    print("Mixing mastered studio audio...", flush=True)
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Stream-copy exact original Final Cut Pro video + attach new clean AAC 192k voiceover!
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    print(f"Muxing {OUT_MP4.name} (-c:v copy)...", flush=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(INPUT_MOV),
            "-i", str(master_wav),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            str(OUT_MP4),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"FULL_VIDEO_DONE: {OUT_MP4} ({OUT_MP4.stat().st_size / (1024*1024):.1f} MB)", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
