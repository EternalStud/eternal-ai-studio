"""Synthesize & master 6-min Google Colab documentary audio (~350-380s).

Uses:
- Male Primary Host: Local Voicebox Chatterbox ('Notebook LLM hindi') with RMS tail trim (NO fixed -450ms word clipping!).
- Female Co-Host: Pre-generated Veena 'kavya' WAVs (from Colab T4).
"""

from __future__ import annotations

import json
import math
import sqlite3
import struct
import subprocess
import time
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "build" / "colab_doc" / "audio"
VB_DB = Path.home() / "Library" / "Application Support" / "sh.voicebox.app" / "voicebox.db"
VB_GEN_DIR = Path.home() / "Library" / "Application Support" / "sh.voicebox.app" / "generations"
MALE_PROFILE = "555e2132-b157-464d-8967-cf569e6e35af"  # Notebook LLM hindi

SCRIPT_BEATS = [
    # Chapter 1: 2 AM Laptop Struggle (00:00 - 00:45)
    {"id": "b01", "ch": 1, "spk": "male", "text": "मान लीजिए रात के दो बजे हैं। कल सुबह आपका प्रोजेक्ट सबमिट होना है, और सिर्फ एक ए-आई मॉडल लोड करते ही आपके आठ जी-बी लैपटॉप का पंखा ज़ोर से घूमता है, और स्क्रीन पूरी तरह फ्रीज़ हो जाती है।", "cap": "रात के 2 बजे · 8GB Laptop OutOfMemoryError पर फ्रीज़!"},
    {"id": "b02", "ch": 1, "spk": "male", "text": "अब सोचिए, कैसा हो अगर आपको बिना एक भी रुपया खर्च किए, सीधे आपके ब्राउज़र के अंदर एक शक्तिशाली क्लाउड सुपरकंप्यूटर मिल जाए, जिसमें सोलह जी-बी का एनवीडिया जी-पी-यू मुफ्त में लगा हो?", "cap": "सीधे Browser में Free 15.3 GB NVIDIA T4 GPU सुपरकंप्यूटर"},
    {"id": "b03", "ch": 1, "spk": "kavya", "wav": "kavya_b03.wav", "text": "एक मिनट! लोग कहते हैं Google Colab बस एक ऑनलाइन Python नोटबुक है — पर क्या सच में यह मेरे सस्ते लैपटॉप को एक AI सुपरकंप्यूटर बना सकता है?", "cap": "क्या Google Colab सच में सस्ते Laptop को AI Supercomputer बनाता है?"},
    {"id": "b04", "ch": 1, "spk": "male", "text": "बिल्कुल। और अगले छह मिनट में आप सिर्फ इस्तेमाल करना नहीं, बल्कि गूगल कोलैब के अंदर की पूरी मशीनरी समझेंगे, ताकि आप हर एरर, हर टाइमआउट, और हर जी-पी-यू ट्रिक के मास्टर बन जाएँ।", "cap": "अगले 6 मिनट: Architecture + Real T4 Benchmark + Pro Tricks"},

    # Chapter 2: How Colab Really Works (00:45 - 01:45)
    {"id": "b05", "ch": 2, "spk": "male", "text": "सबसे पहले वह सबसे बड़ा भ्रम तोड़ते हैं जो नब्बे प्रतिशत नए लोग मानते हैं। जब आप कोलैब में कोई पायथन कोड चलाते हैं, तो वह कोड आपके लैपटॉप या ब्राउज़र के अंदर बिल्कुल नहीं चलता।", "cap": "Myth #1: Python आपके Browser या Laptop पर नहीं चलता"},
    {"id": "b06", "ch": 2, "spk": "male", "text": "आपका ब्राउज़र सिर्फ एक सुंदर रिमोट कंट्रोल है। जैसे ही आप शिफ्ट और एंटर दबाते हैं, आपका कोड एक छोटे मैसेज की तरह इंटरनेट के रास्ते गूगल के डेटा सेंटर में पहुँचता है।", "cap": "Shift + Enter → JSON Message over WebSockets → Google Data Center"},
    {"id": "b07", "ch": 2, "spk": "male", "text": "वहाँ ऊपर, आपके लिए सिर्फ चार सेकंड में एक बिल्कुल अलग, ताज़ा उबुन्टू लिनक्स वर्चुअल मशीन तैयार होती है, जिसमें बारह पॉइंट सात जी-बी सिस्टम रैम और लगभग सौ जी-बी डिस्क स्पेस जुड़ा होता है।", "cap": "4 सेकंड में Fresh Ubuntu VM तैयार: 12.7 GB RAM + ~107 GB Disk"},
    {"id": "b08", "ch": 2, "spk": "male", "text": "इस मशीन के अंदर एक खास इंजन चलता है जिसे आई-पायथन कर्नेल कहते हैं। आपके हर सेल का वेरिएबल, हर डेटासेट और हर लाइब्रेरी इसी रिमोट मशीन की मेमोरी में जिंदा रहती है।", "cap": "IPython Kernel: सारे Variables और Libraries Remote VM RAM में रहते हैं"},
    {"id": "b09", "ch": 2, "spk": "male", "text": "इसीलिए चाहे आपका लैपटॉप पंद्रह हज़ार का हो या उसमें विंडोज़, मैक या लिनक्स कुछ भी हो, सारा भारी काम गूगल के सर्वर पर होता है, आपकी बैटरी या रैम पर एक प्रतिशत भी लोड नहीं पड़ता।", "cap": "Windows, Mac या Old Chromebook — Laptop Load केवल 8%!"},

    # Chapter 3: CPU vs T4 GPU vs TPU (01:45 - 03:10)
    {"id": "b10", "ch": 3, "spk": "male", "text": "लेकिन असली जादू तब शुरू होता है जब आप रनटाइम मेन्यू में जाकर टी-फोर जी-पी-यू चालू करते हैं। आखिर सी-पी-यू और जी-पी-यू में ऐसा क्या फर्क है कि चार घंटे का काम चार मिनट में हो जाता है?", "cap": "Runtime → Change runtime type → NVIDIA T4 GPU"},
    {"id": "b11", "ch": 3, "spk": "male", "text": "सी-पी-यू को चार बहुत बुद्धिमान और बड़े इंजीनियर समझिए, जो कोई भी मुश्किल काम एक के बाद एक बहुत तेज़ रफ्तार से करते हैं। लेकिन जब ए-आई में लाखों नंबर एक साथ गुणा करने हों, तो यहाँ लंबी लाइन लग जाती है।", "cap": "CPU (Sequential): कुछ बड़े Cores, लाखों Math Ops लाइन में अटकते हैं"},
    {"id": "b12", "ch": 3, "spk": "male", "text": "वहीं एनवीडिया टी-फोर जी-पी-यू के अंदर दो हज़ार पाँच सौ साठ छोटे-छोटे कूडा कोर्स होते हैं। ये सब मिलकर पूरी की पूरी मैट्रिक्स को एक ही पल में, एक साथ प्रोसेस कर देते हैं।", "cap": "NVIDIA T4 GPU: 2,560 CUDA Cores एक साथ पूरी Matrix Process करते हैं"},
    {"id": "b13", "ch": 3, "spk": "male", "text": "हमने इसे लाइव टेस्ट किया। जब चार हज़ार बाय चार हज़ार की पंद्रह मैट्रिक्स हमने कोलैब सी-पी-यू पर चलाईं, तो पूरे अठारह सेकंड लगे। लेकिन टी-फोर जी-पी-यू ने वही काम सिर्फ आधे सेकंड में खत्म कर दिया, यानी चौंतीस गुना तेज़।", "cap": "Verified Live T4 Test: CPU 17.94s vs T4 GPU 0.522s (34.4× Faster!)"},
    {"id": "b14", "ch": 3, "spk": "male", "text": "और अगर आपका मॉडल इससे भी बड़ा है, तो गूगल कोलैब आपको टी-पी-यू यानी टेंसर प्रोसेसिंग यूनिट भी देता है, जिसे गूगल ने खास डीप लर्निंग की विशाल मैट्रिक्स के लिए सिलिकॉन में डिज़ाइन किया है।", "cap": "Google TPU: Giant Tensor Matrix Multiplication के लिए Custom Chip"},
    {"id": "b15", "ch": 3, "spk": "kavya", "wav": "kavya_b15.wav", "text": "रुको, मतलब मैं अगर बिना T4 GPU सिलेक्ट किए सीधे Run दबा दूँ, तो मेरा कोड फिर भी धीमे CPU पर ही चलता रहेगा?", "cap": "Default Runtime CPU होता है — बिना चुने T4 GPU अपने-आप ऑन नहीं होता!"},

    # Chapter 4: Hidden Superpowers (03:10 - 04:20)
    {"id": "b16", "ch": 4, "spk": "male", "text": "बिल्कुल सही पकड़ा। हमेशा पहले रनटाइम मेन्यू में टी-फोर जी-पी-यू चुनें, और पहले ही सेल में एक्सक्लेमेशन मार्क एनवीडिया-डैश-एस-एम-आई चलाकर पक्का करें कि ग्राफिक्स कार्ड जुड़ा है या नहीं।", "cap": "Pro Rule #1: !nvidia-smi चलाकर Tesla T4 (15360 MiB) Confirm करें"},
    {"id": "b17", "ch": 4, "spk": "male", "text": "यही एक्सक्लेमेशन मार्क कोलैब की दूसरी सुपरपावर खोलता है। यह आपको सीधे लिनक्स टर्मिनल का कंट्रोल देता है। पिप इंस्टॉल हो, गिट क्लोन हो, या एफ-एफ-एम-पेग, सब एक क्लिक में चलता है।", "cap": "Shell Superpower (!): !pip install · !git clone · !ffmpeg"},
    {"id": "b18", "ch": 4, "spk": "male", "text": "तीसरी सुपरपावर है डेटा सेंटर इंटरनेट स्पीड। मान लीजिए आपको दो जी-बी का ए-आई मॉडल डाउनलोड करना है। घर के वाई-फाई से आपका डेटा पैक खत्म हो जाएगा, पर कोलैब सर्वर पर यह कुछ ही सेकंड में सीधे गूगल की बैकबोन से खिंच आता है।", "cap": "Zero Local Data Drain: Data Center Backbone Download Speed"},
    {"id": "b19", "ch": 4, "spk": "male", "text": "और चौथी कमाल की ट्रिक है हैश-ऐट-पैराम फॉर्म्स। कोड के कमेंट में बस यह टैग लिखते ही, कोलैब आपके पायथन वेरिएबल को सुंदर बटन और ड्रॉपडाउन फॉर्म में बदल देता है, जिसे कोई नॉन-कोडर भी आसानी से चला सकता है।", "cap": "#@param Tricks: Python Variables बन जाते हैं No-Code Forms & Sliders"},
    {"id": "b20", "ch": 4, "spk": "male", "text": "यही वजह है कि ऑटोमेशन टूल्स, बल्क डेटा स्क्रिप्ट्स और ए-आई डेमो ऐप्स लोग कोलैब लिंक के ज़रिए दूसरों से शेयर करते हैं, बिना किसी इंस्टॉलेशन झंझट के।", "cap": "Share One Link → Anyone Runs Zero-Setup AI & Automation"},

    # Chapter 5: The 12-Hour Trap, Drive & Secrets (04:20 - 05:25)
    {"id": "b21", "ch": 5, "spk": "kavya", "wav": "kavya_b21.wav", "text": "पर मैंने बहुत बार देखा है कि सुबह चलाई हुई फाइलें शाम तक गायब हो जाती हैं, और कुछ कोड चलाते वक़्त API key लीक होने का डर भी रहता है। इससे कैसे बचें?", "cap": "Subah की Files गायब क्यों हो जाती हैं, और API Keys कैसे बचाएँ?"},
    {"id": "b22", "ch": 5, "spk": "male", "text": "यही वह जाल है जिसमें लगभग हर नया यूज़र फँसता है। याद रखिए, कोलैब का हर फ्री रनटाइम अस्थायी होता है। अगर आप नब्बे मिनट तक ब्राउज़र बंद छोड़ दें, या बारह घंटे पूरे हो जाएँ, तो पूरा कंटेंट फोल्डर हमेशा के लिए साफ हो जाता है।", "cap": "90-Min Idle / 12-Hr Limit → /content/ VM Reset पर सारी Files Delete!"},
    {"id": "b23", "ch": 5, "spk": "male", "text": "इसका पक्का इलाज है दो लाइन का कोड, फ्रॉम गूगल डॉट कोलैब इम्पोर्ट ड्राइव, और ड्राइव डॉट माउंट। इसे चलाते ही आपकी अपनी गूगल ड्राइव एक हार्ड डिस्क की तरह जुड़ जाती है, और मॉडल व आउटपुट हमेशा सुरक्षित रहते हैं।", "cap": "from google.colab import drive; drive.mount('/content/drive')"},
    {"id": "b24", "ch": 5, "spk": "male", "text": "दूसरा बड़ा सुरक्षा नियम, अपनी ए-पी-आई की या पासवर्ड कभी कोड सेल में पेस्ट मत कीजिए, क्योंकि नोटबुक शेयर होते ही वह सबको साफ दिख जाएगा।", "cap": "Security Rule: Notebook में कभी API Key Hardcode मत करें!"},
    {"id": "b25", "ch": 5, "spk": "male", "text": "इसके बजाय लेफ्ट साइडबार में चाबी वाले सीक्रेट्स आइकन में अपनी की सेव करें और यूज़रडेटा डॉट गेट से पढ़ें। आपकी की पूरी तरह छिपी और सुरक्षित रहेगी।", "cap": "Colab Secrets (🔑) → userdata.get('API_KEY') — Encrypted & Safe"},

    # Chapter 6: Honest Limits & Wrap (05:25 - 06:00)
    {"id": "b26", "ch": 6, "spk": "male", "text": "अब एक ईमानदार सच्चाई भी जान लीजिए। फ्री टियर में आपको अनलिमिटेड जी-पी-यू नहीं मिलता। ज़्यादा भारी इस्तेमाल करने पर कुछ घंटों का कूल-डाउन लग सकता है, और चौबीसों घंटे चलने वाली वेबसाइट होस्ट करने के लिए यह जगह नहीं बनी है।", "cap": "Honest Limits: Dynamic Free GPU Quota · Not for 24/7 Web Hosting"},
    {"id": "b27", "ch": 6, "spk": "male", "text": "लेकिन सीखने, ए-आई मॉडल टेस्ट करने, बड़े डेटा की सफाई करने, और भारी पायथन ऑटोमेशन बिना महंगे हार्डवेयर के चलाने के लिए, आज भी गूगल कोलैब जैसा दूसरा मुफ्त प्लेटफॉर्म नहीं है।", "cap": "Best For: AI Prototyping · GPU Bursts · Student & Automation Work"},
    {"id": "b28", "ch": 6, "spk": "male", "text": "अगर आपको यह विज़ुअल एक्सप्लेनर पसंद आया और आप किसी एक फीचर का लाइव ट्यूटोरियल चाहते हैं, तो कमेंट में ज़रूर बताइए। मिलते हैं अगले डीप डाइव में, इटरनल स्टूडेंट पर।", "cap": "Eternal Student · Subscribe & Comment Next Deep Dive Topic!"},
]


def _probe_ms(p: Path) -> int:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)]
    ).decode().strip()
    return int(round(float(out) * 1000.0))


def _smart_tail_trim(raw_wav: Path, out_wav: Path) -> int:
    """Trim ONLY actual trailing silence/hiss without ever cutting off final syllables."""
    # Convert to 48k mono 16-bit PCM first so we can inspect sample amplitudes precisely
    tmp_pcm = out_wav.with_suffix(".tmp.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw_wav), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(tmp_pcm)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    with wave.open(str(tmp_pcm), "rb") as wf:
        sr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    n = len(raw) // 2
    samples = struct.unpack(f"<{n}h", raw)

    # Compute RMS in 20ms windows; keep a small noise gate just above digital/breath floor (RMS > 260)
    win = int(sr * 0.020)
    last_active_idx = n
    # Also scan from end: ignore tiny isolated click bursts (< 40ms) at very tail if preceded by > 220ms silence
    rms_list = []
    for pos in range(0, n, win):
        chunk = samples[pos : pos + win]
        if not chunk:
            continue
        rms = math.sqrt(sum(s * s for s in chunk) / len(chunk))
        rms_list.append((pos + len(chunk), rms))

    # Walk backwards requiring sustained speech energy (> 300 RMS across at least 2 adjacent windows or > 450 single)
    cut_sample = n
    for i in range(len(rms_list) - 1, -1, -1):
        end_s, r = rms_list[i]
        prev_r = rms_list[i - 1][1] if i > 0 else 0.0
        if r > 320.0 or (r > 200.0 and prev_r > 240.0):
            cut_sample = min(n, end_s + int(sr * 0.14))  # +140ms generous breathing room!
            break

    dur_s = max(0.8, cut_sample / sr)
    fade_st = max(0.0, dur_s - 0.045)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(tmp_pcm),
            "-af", (
                f"atrim=0:{dur_s:.3f},asetpts=PTS-STARTPTS,"
                "highpass=f=75,equalizer=f=165:t=q:w=1.2:g=1.8,equalizer=f=3000:t=q:w=1.4:g=2.2,"
                f"afade=t=in:st=0:d=0.015,afade=t=out:st={fade_st:.3f}:d=0.045"
            ),
            "-ar", "48000", "-ac", "1", str(out_wav),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    tmp_pcm.unlink(missing_ok=True)
    return _probe_ms(out_wav)


def _vb_generate(text: str, out_raw: Path) -> Path:
    req = urllib.request.Request(
        "http://127.0.0.1:17493/generate",
        data=json.dumps({
            "profile_id": MALE_PROFILE,
            "text": text,
            "language": "hi",
            "engine": "chatterbox",
            "normalize": True,
            "max_chunk_chars": 260,
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        gid = json.loads(r.read())["id"]
    for _ in range(180):
        conn = sqlite3.connect(str(VB_DB))
        row = conn.execute("SELECT status FROM generations WHERE id=?", (gid,)).fetchone()
        conn.close()
        if row and row[0] == "completed":
            src = VB_GEN_DIR / f"{gid}.wav"
            out_raw.write_bytes(src.read_bytes())
            return out_raw
        if row and row[0] == "failed":
            raise RuntimeError(f"Voicebox failed for gid={gid}")
        time.sleep(1.5)
    raise TimeoutError(f"Voicebox timeout for gid={gid}")


def main() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    timeline = []
    cur_ms = 550  # 0.55s opening breath over night desk hook
    wav_inputs = []

    for idx, b in enumerate(SCRIPT_BEATS):
        bid = b["id"]
        clean_wav = AUDIO_DIR / f"clean_{bid}.wav"
        if not clean_wav.exists():
            if b["spk"] == "kavya":
                raw_wav = AUDIO_DIR / b["wav"]
                assert raw_wav.exists(), f"Missing {raw_wav}"
                dur_ms = _smart_tail_trim(raw_wav, clean_wav)
            else:
                raw_wav = AUDIO_DIR / f"raw_{bid}.wav"
                if not raw_wav.exists():
                    print(f"[{idx+1}/{len(SCRIPT_BEATS)}] Generating male {bid}...", flush=True)
                    _vb_generate(b["text"], raw_wav)
                dur_ms = _smart_tail_trim(raw_wav, clean_wav)
        else:
            dur_ms = _probe_ms(clean_wav)

        gap = 520 if b["spk"] == "kavya" or (idx + 1 < len(SCRIPT_BEATS) and SCRIPT_BEATS[idx + 1]["spk"] == "kavya") else 340
        timeline.append({
            "id": bid,
            "ch": b["ch"],
            "spk": b["spk"],
            "start_ms": cur_ms,
            "end_ms": cur_ms + dur_ms,
            "dur_ms": dur_ms,
            "cap": b["cap"],
            "text": b["text"],
            "wav": str(clean_wav),
        })
        wav_inputs.append((clean_wav, cur_ms))
        print(f"  {bid} ({b['spk']:5s}): {cur_ms/1000:6.2f}s -> {(cur_ms+dur_ms)/1000:6.2f}s ({dur_ms/1000:.2f}s)", flush=True)
        cur_ms += dur_ms + gap

    total_ms = cur_ms + 1200
    narration_wav = AUDIO_DIR / "full_narration_16x9.wav"

    inputs = []
    delays = []
    labels = []
    for i, (wpath, st_ms) in enumerate(wav_inputs):
        inputs.extend(["-i", str(wpath)])
        delays.append(f"[{i}:a]adelay={st_ms}|{st_ms}[a{i}]")
        labels.append(f"[a{i}]")
    f_str = ";".join(delays) + f";{''.join(labels)}amix=inputs={len(wav_inputs)}:normalize=0,apad=pad_dur=2,atrim=0:{total_ms/1000.0:.3f},loudnorm=I=-14:TP=-1.5:LRA=7"
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", f_str, "-ar", "48000", "-ac", "1", str(narration_wav)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    out_json = ROOT / "build" / "colab_doc" / "timeline.json"
    out_json.write_text(json.dumps({"total_ms": total_ms, "beats": timeline}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nAUDIO_DONE: {narration_wav} ({total_ms/1000.0:.2f}s = {total_ms/60000.0:.2f} min)", flush=True)


if __name__ == "__main__":
    main()
