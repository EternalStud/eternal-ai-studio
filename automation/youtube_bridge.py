"""End-to-end YouTube Channel Analytics & Upload Bridge for Eternal AI Studio.

Two sanctioned integration tiers:
1. Instant Public Channel Audit (`public-audit <channel_url>` via `yt-dlp`, zero OAuth required):
   Extracts public video titles, durations, view counts, likes, and upload dates to benchmark hooks/lengths.
2. Full OAuth 2.0 YouTube Studio Bridge (`auth`, `analytics`, `upload`, `comments`):
   Uses official `google-api-python-client` + `google-auth-oauthlib` with user-supplied
   `credentials/youtube_client_secret.json` -> stores refresh token in `credentials/youtube_token.json`
   (both gitignored under `credentials/`). Uploads default to `private` unless `--publish` is explicitly passed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CREDS_DIR = ROOT / "credentials"
TOKEN_FILE = CREDS_DIR / "youtube_token.json"


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

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def cmd_public_audit(channel_url: str, limit: int = 30) -> None:
    """Inspect public video performance via yt-dlp without requiring OAuth credentials."""
    raw = subprocess.check_output(
        [
            "yt-dlp",
            "--flat-playlist",
            "--dump-single-json",
            "--playlist-end",
            str(limit),
            channel_url,
        ],
        text=True,
    )
    data = json.loads(raw)
    entries = data.get("entries") or []
    rows = []
    for e in entries:
        rows.append({
            "id": e.get("id"),
            "title": e.get("title"),
            "duration_s": e.get("duration"),
            "view_count": e.get("view_count"),
            "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
        })
    out_p = ROOT / "build" / "youtube_public_audit.json"
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps({"channel": data.get("channel") or channel_url, "videos": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Found {len(rows)} public videos -> saved {out_p}")
    for r in rows[:15]:
        print(f"  [{r['view_count'] or 0:>6} views | {r['duration_s'] or 0:>4}s] {r['title']}")


def _get_oauth_creds(force_reauth: bool = False):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit(
            "Install YouTube API deps first: .venv/bin/pip install google-api-python-client google-auth-oauthlib"
        ) from exc

    creds = None
    if TOKEN_FILE.exists() and not force_reauth:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and not force_reauth:
            creds.refresh(Request())
        else:
            secret_path = _find_client_secret()
            flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)
            creds = flow.run_local_server(port=0, prompt="select_account consent")
        CREDS_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def cmd_analytics(days: int = 90, handle: str = "@Etrnll0v") -> None:
    from googleapiclient.discovery import build

    creds = _get_oauth_creds()
    yt = build("youtube", "v3", credentials=creds)
    yta = build("youtubeAnalytics", "v2", credentials=creds)

    ch_resp = yt.channels().list(forHandle=handle, part="snippet,statistics,contentDetails").execute()
    items = ch_resp.get("items") or yt.channels().list(mine=True, part="snippet,statistics,contentDetails").execute().get("items") or []
    if not items:
        raise SystemExit("No YouTube channel found for authorized Google account.")
    ch = items[0]
    ch_id = ch["id"]
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

    # Map video IDs to exact titles via Data API v3
    rows = rep.get("rows") or []
    titles = {}
    if rows:
        vid_ids = [r[0] for r in rows]
        v_resp = yt.videos().list(id=",".join(vid_ids), part="snippet,contentDetails").execute()
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

    out_p = ROOT / "build" / "youtube_analytics_report.json"
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps({"channel": ch, "analytics": rep, "titles": titles, "traffic_sources": traffic}, indent=2), encoding="utf-8")
    print(f"Saved full {days}-day retention & analytics report -> {out_p}")
    print("\n=== TOP VIDEOS BY VIEWS (LAST", days, "DAYS) ===")
    for row in rows:
        vid, views, mins, avg_dur, avg_pct, subs, likes, cmts = row
        t = titles.get(vid, vid)[:52]
        print(f"  {vid} | {views:>5}v | {mins:>4}m watch | avg {avg_dur:>4.0f}s ({avg_pct:>5.1f}%) | +{subs} subs | {likes}👍 | {t}")
    print("\n=== TRAFFIC SOURCES ===")
    for tr in traffic.get("rows", []):
        print(f"  {tr[0]:<26} {tr[1]:>6} views | {tr[2]:>6} watch mins")


def cmd_upload(video_path: Path, title: str, description: str, tags: list[str], publish: bool = False, target_channel_id: str = "UCU7tyDOES8n9XqIDJ86gSrQ") -> None:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    assert video_path.exists(), f"Missing video: {video_path}"
    creds = _get_oauth_creds()
    yt = build("youtube", "v3", credentials=creds)
    mine = yt.channels().list(mine=True, part="id,snippet").execute().get("items") or []
    active_id = mine[0]["id"] if mine else None
    active_title = mine[0]["snippet"]["title"] if mine else "unknown"
    if active_id != target_channel_id:
        raise SystemExit(
            f"Active OAuth channel is '{active_title}' ({active_id}), NOT Eternal Student ({target_channel_id}).\n"
            "Run: .venv/bin/python automation/youtube_bridge.py auth --force  and select 'Eternal Student' on Google's channel picker."
        )
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education / Tech
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
    print(f"UPLOADED ({body['status']['privacyStatus']}): https://www.youtube.com/watch?v={resp['id']}")


def cmd_latest_and_comments(handle: str = "@Etrnll0v", limit: int = 10) -> None:
    from googleapiclient.discovery import build

    creds = _get_oauth_creds()
    yt = build("youtube", "v3", credentials=creds)
    ch = yt.channels().list(forHandle=handle, part="id,snippet,statistics,contentDetails").execute()["items"][0]
    ch_id = ch["id"]
    pl_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = yt.playlistItems().list(playlistId=pl_id, part="contentDetails", maxResults=limit).execute()["items"]
    vids = [i["contentDetails"]["videoId"] for i in items]
    vinfo = yt.videos().list(id=",".join(vids), part="snippet,statistics,contentDetails").execute()["items"]
    print(f"=== LATEST {len(vinfo)} UPLOADS ON {ch['snippet']['title']} ===")
    for v in vinfo:
        s = v["statistics"]
        print(f"  {v['id']} | {v['snippet']['publishedAt'][:10]} | {s.get('viewCount',0):>5}v | {s.get('likeCount',0):>2}👍 | {s.get('commentCount',0):>2}💬 | {v['contentDetails']['duration']:<9} | {v['snippet']['title'][:60]}")

    cmts = yt.commentThreads().list(allThreadsRelatedToChannelId=ch_id, part="snippet", maxResults=15).execute().get("items", [])
    print("\n=== RECENT VIEWER COMMENTS ===")
    for c in cmts:
        sn = c["snippet"]["topLevelComment"]["snippet"]
        print(f"  [{sn['publishedAt'][:10]} | {sn['videoId']}] {sn['authorDisplayName']}: {sn['textDisplay'][:110]}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Eternal AI Studio YouTube Bridge")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_pub = sub.add_parser("public-audit", help="Inspect public channel stats via yt-dlp")
    p_pub.add_argument("channel_url")
    p_pub.add_argument("--limit", type=int, default=30)

    p_auth = sub.add_parser("auth", help="Run OAuth 2.0 consent flow and save refresh token")
    p_auth.add_argument("--force", action="store_true", help="Force re-auth to pick Brand Account (Eternal Student)")

    p_an = sub.add_parser("analytics", help="Fetch private YouTube Analytics retention & metrics")
    p_an.add_argument("--days", type=int, default=28)

    p_up = sub.add_parser("upload", help="Upload MP4 via YouTube Data API v3 (private by default)")
    p_up.add_argument("video", type=Path)
    p_up.add_argument("--title", required=True)
    p_up.add_argument("--desc", default="")
    p_up.add_argument("--tags", default="GoogleMaps,TechExplainer,EternalStudent,Hindi")
    p_up.add_argument("--publish", action="store_true")

    p_lat = sub.add_parser("latest", help="Fetch real-time stats for latest uploads & viewer comments")
    p_lat.add_argument("--limit", type=int, default=10)

    args = ap.parse_args()
    if args.cmd == "public-audit":
        cmd_public_audit(args.channel_url, args.limit)
    elif args.cmd == "auth":
        _get_oauth_creds(force_reauth=args.force)
        print(f"OAuth token verified & cached at {TOKEN_FILE}")
    elif args.cmd == "analytics":
        cmd_analytics(args.days)
    elif args.cmd == "upload":
        cmd_upload(args.video, args.title, args.desc, [t.strip() for t in args.tags.split(",") if t.strip()], args.publish)
    elif args.cmd == "latest":
        cmd_latest_and_comments(limit=args.limit)


if __name__ == "__main__":
    main()
