"""Multi-channel YouTube Studio Automation Bridge for Eternal AI Studio.

Supports managing multiple YouTube channels independently (e.g., `eternal_student` for
teacher/portal automation tutorials and `tech_channel` for AI/system explainers).

Per-channel OAuth tokens and registry live inside `.gitignored` `credentials/`:
  - credentials/channels.json
  - credentials/token_<alias>.json

Uploads default to `private` unless `--publish` is explicitly passed, and always verify
that the active OAuth `mine=True` channel ID matches the target alias before uploading.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CREDS_DIR = ROOT / "credentials"
CHANNELS_FILE = CREDS_DIR / "channels.json"
LEGACY_TOKEN = CREDS_DIR / "youtube_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def _find_client_secret() -> Path:
    explicit = CREDS_DIR / "youtube_client_secret.json"
    if explicit.exists():
        return explicit
    matches = sorted(
        p for p in CREDS_DIR.glob("client_secret*.json")
        if not p.name.startswith("._")
    )
    if matches:
        return matches[0]
    raise SystemExit(
        f"Missing OAuth client JSON in {CREDS_DIR} (expected youtube_client_secret.json or client_secret_*.json)."
    )


def _load_registry() -> dict:
    if CHANNELS_FILE.exists():
        return json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
    # Seed initial dual-channel structure cleanly if legacy token exists
    reg: dict = {
        "eternal_student": {
            "channel_id": "UCU7tyDOES8n9XqIDJ86gSrQ",
            "handle": "@Etrnll0v",
            "title": "Eternal Student",
            "niche": "Indian Teacher / School / UDISE+ / Excel Automation Tutorials",
            "token_file": str(CREDS_DIR / "token_eternal_student.json"),
        }
    }
    if LEGACY_TOKEN.exists() and not (CREDS_DIR / "token_eternal_student.json").exists():
        # Legacy token has analytics read on eternal_student while mine=True was default profile
        reg["default_profile"] = {
            "channel_id": "UCqhU754GdfiB-1IVQFmem6g",
            "handle": None,
            "title": "Eternal Love (Default Profile)",
            "niche": "Pending new dedicated channel or Brand Account selection",
            "token_file": str(LEGACY_TOKEN),
        }
        reg["eternal_student"]["token_file"] = str(LEGACY_TOKEN)
    CREDS_DIR.mkdir(parents=True, exist_ok=True)
    CHANNELS_FILE.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    return reg


def _save_registry(reg: dict) -> None:
    CREDS_DIR.mkdir(parents=True, exist_ok=True)
    CHANNELS_FILE.write_text(json.dumps(reg, indent=2), encoding="utf-8")


def _get_oauth_creds(alias: str, force_reauth: bool = False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    reg = _load_registry()
    entry = reg.get(alias, {})
    tok_path = Path(entry.get("token_file") or (CREDS_DIR / f"token_{alias}.json"))

    creds = None
    if tok_path.exists() and not force_reauth:
        creds = Credentials.from_authorized_user_file(str(tok_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and not force_reauth:
            creds.refresh(Request())
        else:
            secret_path = _find_client_secret()
            flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)
            creds = flow.run_local_server(port=0, prompt="select_account consent")
        tok_path.parent.mkdir(parents=True, exist_ok=True)
        tok_path.write_text(creds.to_json(), encoding="utf-8")

        # Record the exact authorized channel into registry
        yt = build("youtube", "v3", credentials=creds)
        mine = yt.channels().list(mine=True, part="id,snippet,statistics").execute().get("items") or []
        if mine:
            ch = mine[0]
            reg[alias] = {
                "channel_id": ch["id"],
                "handle": ch["snippet"].get("customUrl"),
                "title": ch["snippet"]["title"],
                "niche": entry.get("niche", "AI Studio Managed Channel"),
                "token_file": str(tok_path),
            }
            _save_registry(reg)
            print(f"Authorized '{alias}' -> {ch['snippet']['title']} ({ch['id']}, subs={ch['statistics'].get('subscriberCount')})")
    return creds


def cmd_list_channels() -> None:
    from googleapiclient.discovery import build

    reg = _load_registry()
    print("=== REGISTERED YOUTUBE CHANNELS ===")
    for alias, info in reg.items():
        tok = Path(info["token_file"])
        status = "NO TOKEN"
        upload_target = "?"
        if tok.exists():
            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                creds = Credentials.from_authorized_user_file(str(tok), SCOPES)
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                yt = build("youtube", "v3", credentials=creds)
                mine = yt.channels().list(mine=True, part="id,snippet").execute().get("items") or []
                upload_id = mine[0]["id"] if mine else None
                upload_title = mine[0]["snippet"]["title"] if mine else "?"
                upload_target = f"{upload_title} ({upload_id})"
                status = "UPLOAD READY ✓" if upload_id == info["channel_id"] else f"READ-ONLY (upload bound to {upload_title})"
            except Exception as exc:
                status = f"AUTH ERR: {exc}"
        print(f"  - {alias:<16} | target: {info.get('title')} ({info.get('channel_id')}) | {status}")


def cmd_public_audit(channel_url: str, limit: int = 30) -> None:
    raw = subprocess.check_output(
        ["yt-dlp", "--no-update", "--flat-playlist", "--dump-single-json", "--playlist-end", str(limit), channel_url],
        text=True,
    )
    data = json.loads(raw)
    rows = [
        {
            "id": e.get("id"),
            "title": e.get("title"),
            "duration_s": e.get("duration"),
            "view_count": e.get("view_count"),
            "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
        }
        for e in (data.get("entries") or [])
    ]
    out_p = ROOT / "build" / "youtube_public_audit.json"
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps({"channel": data.get("channel") or channel_url, "videos": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Found {len(rows)} public videos -> {out_p}")
    for r in rows[:15]:
        print(f"  [{r['view_count'] or 0:>6} views | {r['duration_s'] or 0:>4}s] {r['title']}")


def cmd_analytics(alias: str, days: int = 90) -> None:
    from googleapiclient.discovery import build

    reg = _load_registry()
    info = reg.get(alias)
    if not info:
        raise SystemExit(f"Unknown channel alias '{alias}'. Run `auth --channel {alias}` first.")
    creds = _get_oauth_creds(alias)
    yt = build("youtube", "v3", credentials=creds)
    yta = build("youtubeAnalytics", "v2", credentials=creds)

    ch_id = info["channel_id"]
    ch = yt.channels().list(id=ch_id, part="snippet,statistics").execute()["items"][0]
    print("CHANNEL:", ch["snippet"]["title"], f"({ch_id})", "| Subs:", ch["statistics"].get("subscriberCount"), "| Views:", ch["statistics"].get("viewCount"))

    end_d = date.today().isoformat()
    start_d = (date.today() - timedelta(days=days)).isoformat()
    rep = yta.reports().query(
        ids=f"channel=={ch_id}",
        startDate=start_d,
        endDate=end_d,
        metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments",
        dimensions="video",
        sort="-views",
        maxResults=25,
    ).execute()

    rows = rep.get("rows") or []
    titles = {}
    if rows:
        v_resp = yt.videos().list(id=",".join(r[0] for r in rows), part="snippet").execute()
        for it in v_resp.get("items", []):
            titles[it["id"]] = it["snippet"]["title"]

    traffic = yta.reports().query(
        ids=f"channel=={ch_id}",
        startDate=start_d,
        endDate=end_d,
        metrics="views,estimatedMinutesWatched",
        dimensions="insightTrafficSourceType",
        sort="-views",
    ).execute()

    out_p = ROOT / "build" / f"youtube_analytics_{alias}.json"
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps({"channel": ch, "analytics": rep, "titles": titles, "traffic_sources": traffic}, indent=2), encoding="utf-8")
    print(f"Saved {days}-day report -> {out_p}")
    for row in rows:
        vid, views, mins, avg_dur, avg_pct, subs, likes, cmts = row
        print(f"  {vid} | {views:>5}v | {mins:>4}m | avg {avg_dur:>4.0f}s ({avg_pct:>5.1f}%) | +{subs} subs | {titles.get(vid, vid)[:48]}")


def cmd_latest(alias: str, limit: int = 10) -> None:
    from googleapiclient.discovery import build

    reg = _load_registry()
    info = reg.get(alias)
    if not info:
        raise SystemExit(f"Unknown channel alias '{alias}'. Run `auth --channel {alias}` first.")
    creds = _get_oauth_creds(alias)
    yt = build("youtube", "v3", credentials=creds)
    ch_id = info["channel_id"]
    ch = yt.channels().list(id=ch_id, part="snippet,contentDetails").execute()["items"][0]
    pl_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = yt.playlistItems().list(playlistId=pl_id, part="contentDetails", maxResults=limit).execute().get("items", [])
    if not items:
        print(f"No uploads yet on {ch['snippet']['title']} ({ch_id}).")
        return
    vids = [i["contentDetails"]["videoId"] for i in items]
    vinfo = yt.videos().list(id=",".join(vids), part="snippet,statistics,contentDetails").execute()["items"]
    print(f"=== LATEST {len(vinfo)} UPLOADS ON {ch['snippet']['title']} ({ch_id}) ===")
    for v in vinfo:
        s = v["statistics"]
        print(f"  {v['id']} | {v['snippet']['publishedAt'][:10]} | {s.get('viewCount',0):>5}v | {s.get('likeCount',0):>2}👍 | {s.get('commentCount',0):>2}💬 | {v['contentDetails']['duration']:<9} | {v['snippet']['title'][:58]}")

    cmts = yt.commentThreads().list(allThreadsRelatedToChannelId=ch_id, part="snippet", maxResults=15).execute().get("items", [])
    print("\n=== RECENT VIEWER COMMENTS ===")
    for c in cmts:
        sn = c["snippet"]["topLevelComment"]["snippet"]
        print(f"  [{sn['publishedAt'][:10]} | {sn['videoId']}] {sn['authorDisplayName']}: {sn['textDisplay'][:110]}")


def cmd_upload(alias: str, video_path: Path, title: str, description: str, tags: list[str], publish: bool = False) -> None:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    assert video_path.exists(), f"Missing video: {video_path}"
    reg = _load_registry()
    info = reg.get(alias)
    if not info:
        raise SystemExit(f"Unknown channel alias '{alias}'. Run `auth --channel {alias}` first.")
    creds = _get_oauth_creds(alias)
    yt = build("youtube", "v3", credentials=creds)

    mine = yt.channels().list(mine=True, part="id,snippet").execute().get("items") or []
    active_id = mine[0]["id"] if mine else None
    active_title = mine[0]["snippet"]["title"] if mine else "unknown"
    target_id = info["channel_id"]
    if active_id != target_id:
        raise SystemExit(
            f"OAuth token for '{alias}' uploads to '{active_title}' ({active_id}), NOT target '{info.get('title')}' ({target_id}).\n"
            f"Run: .venv/bin/python automation/youtube_bridge.py auth --channel {alias} --force  and pick the target channel."
        )

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "27",
            "defaultLanguage": "hi",
        },
        "status": {
            "privacyStatus": "public" if publish else "private",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  Uploading {int(status.progress() * 100)}%...", flush=True)
    print(f"UPLOADED to {active_title} ({body['status']['privacyStatus']}): https://www.youtube.com/watch?v={resp['id']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Eternal AI Studio Multi-Channel YouTube Bridge")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-channels", help="List all registered channels and upload/analytics status")

    p_pub = sub.add_parser("public-audit", help="Inspect any public channel via yt-dlp")
    p_pub.add_argument("channel_url")
    p_pub.add_argument("--limit", type=int, default=30)

    p_auth = sub.add_parser("auth", help="Authorize and bind a YouTube channel alias via OAuth 2.0")
    p_auth.add_argument("--channel", default="tech_channel", help="Alias e.g. eternal_student or tech_channel")
    p_auth.add_argument("--force", action="store_true")

    p_an = sub.add_parser("analytics", help="Fetch YouTube Analytics retention & traffic metrics")
    p_an.add_argument("--channel", default="eternal_student")
    p_an.add_argument("--days", type=int, default=90)

    p_lat = sub.add_parser("latest", help="Fetch latest uploads and viewer comments")
    p_lat.add_argument("--channel", default="eternal_student")
    p_lat.add_argument("--limit", type=int, default=10)

    p_up = sub.add_parser("upload", help="Upload MP4 safely to verified target channel (private by default)")
    p_up.add_argument("video", type=Path)
    p_up.add_argument("--channel", required=True, help="Target channel alias")
    p_up.add_argument("--title", required=True)
    p_up.add_argument("--desc", default="")
    p_up.add_argument("--tags", default="TechExplainer,Hinglish,HowItWorks")
    p_up.add_argument("--publish", action="store_true")

    args = ap.parse_args()
    if args.cmd == "list-channels":
        cmd_list_channels()
    elif args.cmd == "public-audit":
        cmd_public_audit(args.channel_url, args.limit)
    elif args.cmd == "auth":
        _get_oauth_creds(args.channel, force_reauth=args.force)
    elif args.cmd == "analytics":
        cmd_analytics(args.channel, args.days)
    elif args.cmd == "latest":
        cmd_latest(args.channel, args.limit)
    elif args.cmd == "upload":
        cmd_upload(args.channel, args.video, args.title, args.desc, [t.strip() for t in args.tags.split(",") if t.strip()], args.publish)


if __name__ == "__main__":
    main()
