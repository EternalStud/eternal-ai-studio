"""Build the 2-min 1080x1920 bespoke animated explainer: How Google Maps Predicts Traffic.

Zero repetitive loops: 12 custom animated Canvas/SVG scenes synced beat-for-beat at 30fps,
paired with approved dual-voice Hinglish (Chatterbox Notebook LLM hindi + Veena kavya).
Supports `--spot-only` to visually inspect all 12 scenes BEFORE rendering full frames.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import subprocess
import sys
import wave
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audio.sfx_gen import generate_sfx_bed

BUILD = ROOT / "build" / "gmaps_2min"
AUDIO_DIR = BUILD / "audio"
FRAMES_DIR = BUILD / "frames"
SPOT_DIR = BUILD / "spot"
HTML_PATH = ROOT / "scenes" / "gmaps_2min_1080x1920.html"
OUT_MP4 = ROOT / "output" / "gmaps_traffic_2min_1080x1920.mp4"
BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

CAPTIONS = {
    "t01": "सड़क बिल्कुल खाली है — फिर भी Google Maps 3 km आगे Red Jam कैसे दिखा रहा है?",
    "t02": "यह Satellite या Traffic Camera नहीं — सड़क पर चलती गाड़ियों के Phones का जाल है",
    "t03": "पर अगर सबकी Speed ट्रैक हो रही है, तो क्या Google को मेरा नाम-नंबर भी दिखता है?",
    "t04": "नहीं! आपका Phone पहचान हटाकर सिर्फ GPS, Heading और Speed भेजता है (Every 5 seconds)",
    "t05": "जब 25 Phones की Speed 50 → 12 km/h गिरती है, सड़क तुरंत Red हो जाती है",
    "t06": "Future Prediction: आज की Live Speed की तुलना पिछले 52 Tuesdays से की जाती है",
    "t07": "Supersegments & Graph AI: एक चौराहे का जाम पीछे की सड़कों पर असर पहले ही भाँपता है",
    "t08": "Berlin 2020: एक कलाकार खाली सड़क पर हाथठेले में 99 ऑन Android Phones लेकर चला",
    "t09": "0 कारें थीं सड़क पर — फिर भी 99 Phones ने Google Maps को गहरा लाल जाम दिखा दिया!",
    "t10": "Modern AI: रुके Parked Outliers को छांटता है और Traffic को 3 रास्तों में बांटता है",
    "t11": "मतलब खाली सड़क पर भी Red Line दिखे, तो AI और सैकड़ों गुमनाम Phones पहले ही जाम पकड़ चुके हैं!",
    "t12": "Live Anonymous Pings + Historical Baseline + Graph AI — यही है Data Magic · Eternal Student",
}
ORDER = ["t01", "t02", "t03", "t04", "t05", "t06", "t07", "t08", "t09", "t10", "t11", "t12"]


def _probe_ms(p: Path) -> int:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)]
    ).decode().strip()
    return int(round(float(out) * 1000.0))


def _smart_trim_eq(raw_wav: Path, out_wav: Path) -> int:
    tmp = out_wav.with_suffix(".tmp.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw_wav), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(tmp)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    with wave.open(str(tmp), "rb") as wf:
        sr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    n = len(raw) // 2
    samples = struct.unpack(f"<{n}h", raw)
    win = int(sr * 0.020)
    rms_list = []
    for pos in range(0, n, win):
        ch = samples[pos : pos + win]
        if ch:
            rms_list.append((pos + len(ch), math.sqrt(sum(s * s for s in ch) / len(ch))))
    cut_s = n
    for i in range(len(rms_list) - 1, -1, -1):
        end_s, r = rms_list[i]
        prev_r = rms_list[i - 1][1] if i > 0 else 0.0
        if r > 320.0 or (r > 200.0 and prev_r > 240.0):
            cut_s = min(n, end_s + int(sr * 0.14))
            break
    dur = max(0.8, cut_s / sr)
    fst = max(0.0, dur - 0.045)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(tmp),
            "-af", (
                f"atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
                "highpass=f=75,equalizer=f=165:t=q:w=1.2:g=1.8,equalizer=f=3000:t=q:w=1.4:g=2.2,"
                f"afade=t=in:st=0:d=0.015,afade=t=out:st={fst:.3f}:d=0.045"
            ),
            "-ar", "48000", "-ac", "1", str(out_wav),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    tmp.unlink(missing_ok=True)
    return _probe_ms(out_wav)


def build_audio_timeline() -> dict:
    cur_ms = 400
    beats = []
    wavs = []
    for idx, bid in enumerate(ORDER):
        raw_p = AUDIO_DIR / f"raw_{bid}.wav"
        clean_p = AUDIO_DIR / f"clean_{bid}.wav"
        assert raw_p.exists(), f"Missing {raw_p}"
        dur = _smart_trim_eq(raw_p, clean_p) if not clean_p.exists() else _probe_ms(clean_p)
        spk = "kavya" if bid in ("t03", "t11") else "male"
        gap = 450 if spk == "kavya" or (idx + 1 < len(ORDER) and ORDER[idx + 1] in ("t03", "t11")) else 280
        beats.append({
            "id": bid, "spk": spk, "start_ms": cur_ms, "end_ms": cur_ms + dur,
            "dur_ms": dur, "cap": CAPTIONS[bid], "wav": str(clean_p),
        })
        wavs.append((clean_p, cur_ms))
        print(f"  {bid} ({spk:5s}): {cur_ms/1000:6.2f}s -> {(cur_ms+dur)/1000:6.2f}s ({dur/1000:.2f}s)", flush=True)
        cur_ms += dur + gap

    total_ms = cur_ms + 900
    nar_wav = AUDIO_DIR / "full_narration_2min.wav"
    inputs, delays, labels = [], [], []
    for i, (wp, st) in enumerate(wavs):
        inputs.extend(["-i", str(wp)])
        delays.append(f"[{i}:a]adelay={st}|{st}[a{i}]")
        labels.append(f"[a{i}]")
    fc = ";".join(delays) + f";{''.join(labels)}amix=inputs={len(wavs)}:normalize=0,apad=pad_dur=2,atrim=0:{total_ms/1000.0:.3f},loudnorm=I=-14:TP=-1.5:LRA=7"
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-ar", "48000", "-ac", "1", str(nar_wav)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    manifest = {"total_ms": total_ms, "beats": beats}
    (BUILD / "timeline.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"AUDIO_2MIN_READY: {total_ms/1000.0:.2f}s ({total_ms/60000.0:.2f} min)", flush=True)
    return manifest


def run_spot_only() -> None:
    SPOT_DIR.mkdir(parents=True, exist_ok=True)
    dummy = {
        "total_ms": 120000,
        "beats": [
            {"id": bid, "spk": "kavya" if bid in ("t03", "t11") else "male", "start_ms": i * 10000, "end_ms": (i + 1) * 10000 - 300, "cap": CAPTIONS[bid]}
            for i, bid in enumerate(ORDER)
        ],
    }
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=BRAVE_PATH, headless=True, args=["--no-sandbox", "--disable-gpu-sandbox"])
        try:
            pg = br.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
            pg.goto(HTML_PATH.resolve().as_uri(), wait_until="load")
            pg.evaluate("(m) => document.fonts.ready.then(() => window.initDoc(m))", dummy)
            for i, bid in enumerate(ORDER):
                pg.evaluate("(t) => window.seekToMs(t)", i * 10000 + 6200)
                pg.screenshot(path=str(SPOT_DIR / f"spot_{bid}.png"))
        finally:
            br.close()
    print(f"SPOT_12_SAVED: {SPOT_DIR}", flush=True)


def run_full_render() -> None:
    manifest = build_audio_timeline()
    total_ms = manifest["total_ms"]
    fps = 30
    total_frames = int(math.ceil((total_ms / 1000.0) * fps))
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Rendering {total_frames} bespoke 1080x1920 frames @ {fps}fps...", flush=True)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=BRAVE_PATH, headless=True, args=["--no-sandbox", "--disable-gpu-sandbox"])
        try:
            pg = br.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
            pg.goto(HTML_PATH.resolve().as_uri(), wait_until="load")
            pg.evaluate("(m) => document.fonts.ready.then(() => window.initDoc(m))", manifest)
            for idx in range(total_frames):
                fnum = idx + 1
                out_p = FRAMES_DIR / f"f_{fnum:04d}.png"
                if not out_p.exists():
                    t_ms = int(round((idx * 1000.0) / fps))
                    pg.evaluate("(t) => window.seekToMs(t)", t_ms)
                    pg.screenshot(path=str(out_p))
                if fnum % 300 == 0:
                    print(f"  FRAMES {fnum}/{total_frames}", flush=True)
        finally:
            br.close()

    print("[2/3] Synthesizing stereo SFX + radar pings...", flush=True)
    starts = [b["start_ms"] for b in manifest["beats"]]
    pings = [(b["start_ms"] + 160, 940.0 if b["spk"] == "kavya" else 760.0) for b in manifest["beats"]]
    sfx_wav = AUDIO_DIR / "sfx_2min.wav"
    generate_sfx_bed(total_ms, starts, pings, sfx_wav)

    print("[3/3] Final mux (-14 LUFS)...", flush=True)
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    nar_wav = AUDIO_DIR / "full_narration_2min.wav"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-framerate", str(fps), "-i", str(FRAMES_DIR / "f_%04d.png"),
            "-i", str(nar_wav),
            "-i", str(sfx_wav),
            "-filter_complex", (
                "[0:v]format=yuv420p[vout];"
                "[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0[nar];"
                "[2:a]aresample=48000,volume=0.35[sfx];"
                "[nar][sfx]amix=inputs=2:duration=first:dropout_transition=0,"
                "loudnorm=I=-14:TP=-1.5:LRA=8[aout]"
            ),
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "16",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(OUT_MP4),
        ],
        check=True,
    )
    mb = OUT_MP4.stat().st_size / (1024 * 1024)
    print(f"GMAPS_2MIN_DONE: {OUT_MP4} ({mb:.1f} MB, {total_ms/1000.0:.2f}s)", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--spot-only", action="store_true")
    args = ap.parse_args()
    if args.spot_only:
        run_spot_only()
    else:
        run_full_render()
