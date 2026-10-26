"""Server-side YouTube access without the Mac relay (Render's IP is blocked by YouTube itself, so two helpers do the talking):

  * YouTube Data API v3 (free key, any IP): list a channel/playlist's latest videos, read a video's metadata.
  * A caption service (Supadata): fetch a video's captions through the provider's own proxies.

Both are optional: with no keys the Mac relay keeps doing everything, exactly as before. Keys come from multiuser.secret():
YOUTUBE_API_KEY and SUPADATA_API_KEY (Render environment variables).
"""
import json, re, time, urllib.error, urllib.parse, urllib.request

import multiuser

YT = "https://www.googleapis.com/youtube/v3"
SUPADATA = "https://api.supadata.ai/v1"


class NoCaptions(RuntimeError):
    pass


class RateLimited(RuntimeError):
    def __init__(self, msg="rate limited", after=10):
        super().__init__(msg)
        self.after = after


def _key(name):
    return (multiuser.secret(name) or "").strip()


def api_enabled():
    return bool(_key("YOUTUBE_API_KEY"))


def captions_enabled():
    return api_enabled() and bool(_key("SUPADATA_API_KEY"))


def _get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "pawed/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8", "replace") or "{}")


def _iso_dur(s):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return None
    d, h, mi, se = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + se


def _videos_meta(ids):
    """videos.list for up to 50 ids -> {vid: {title, channel, published_at, duration, description, lang}}"""
    out = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        q = urllib.parse.urlencode({"part": "snippet,contentDetails", "id": ",".join(chunk), "key": _key("YOUTUBE_API_KEY")})
        _, d = _get(f"{YT}/videos?{q}")
        for it in d.get("items", []):
            sn, cd = it.get("snippet", {}), it.get("contentDetails", {})
            out[it["id"]] = {"title": sn.get("title") or "", "channel": sn.get("channelTitle") or "", "published_at": sn.get("publishedAt"),
                             "duration": _iso_dur(cd.get("duration")), "description": (sn.get("description") or "")[:3000],
                             "lang": (sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "")[:2].lower()}
    return out


def list_videos(source_id, n=10):
    """Newest-first [{vid, title, published, duration}] for a channel (UC...) or playlist (PL...) id."""
    pl = "UU" + source_id[2:] if source_id.startswith("UC") else source_id
    q = urllib.parse.urlencode({"part": "contentDetails", "playlistId": pl, "maxResults": min(50, n), "key": _key("YOUTUBE_API_KEY")})
    _, d = _get(f"{YT}/playlistItems?{q}")
    ids = [it["contentDetails"]["videoId"] for it in d.get("items", []) if it.get("contentDetails", {}).get("videoId")]
    meta = _videos_meta(ids)
    rows = [{"vid": v, "title": meta[v]["title"], "published": meta[v]["published_at"], "duration": meta[v]["duration"]} for v in ids if v in meta]
    rows.sort(key=lambda r: r["published"] or "", reverse=True)
    return rows


def _fmt(sec):
    h, r = divmod(int(sec), 3600)
    return f"{h}:{r // 60:02d}:{r % 60:02d}" if h else f"{r // 60}:{r % 60:02d}"


def _blocks(segments):
    """[(start_seconds, text)] -> '[m:ss] text ...' blocks of ~30 s, the same shape the Mac relay produces"""
    blocks, cur, buf = [], None, []
    for sec, text in segments:
        if cur is None:
            cur = sec
        buf.append(text)
        if sec - cur >= 30:
            blocks.append(f"[{_fmt(cur)}] " + " ".join(buf))
            cur, buf = None, []
    if buf and cur is not None:
        blocks.append(f"[{_fmt(cur)}] " + " ".join(buf))
    return "\n".join(blocks)


_QUOTA_LOGGED = 0.0


def _note_quota(code, body):
    """one log line per 10 minutes with the provider's own words, so 'plan used up' is told apart from 'too fast'"""
    global _QUOTA_LOGGED
    if time.time() - _QUOTA_LOGGED > 600:
        _QUOTA_LOGGED = time.time()
        multiuser.log(f"vidsum caption service QUOTA: HTTP {code} {body[:240]}")


def _supadata(vid, lang):
    """-> list of (seconds, text). Raises NoCaptions / RateLimited."""
    key = _key("SUPADATA_API_KEY")
    q = {"url": f"https://www.youtube.com/watch?v={vid}", "text": "false", "mode": "native"}
    if lang:
        q["lang"] = lang
    try:
        status, d = _get(f"{SUPADATA}/transcript?{urllib.parse.urlencode(q)}", {"x-api-key": key, "User-Agent": "pawed/1.0"}, timeout=60)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        if e.code in (402, 429):
            try:
                after = int(float(e.headers.get("Retry-After") or 0))
            except ValueError:
                after = 0
            low = body.lower()
            quota = e.code == 402 or any(w in low for w in ("quota", "credit", "upgrade", "plan", "monthly", "limit exceeded", "usage"))
            if quota:                                           # not a burst limit: the plan is used up, so stay away for a while (the Mac covers meanwhile)
                _note_quota(e.code, body)
                raise RateLimited(f"caption service quota exhausted ({e.code}): {body[:140]}", 1800)
            raise RateLimited(f"caption service rate limit ({e.code}): {body[:140]}", min(60, max(5, after or 10)))
        if e.code in (400, 404, 206) or "unavailable" in body.lower() or "not-found" in body.lower():
            raise NoCaptions("no captions available")
        raise RuntimeError(f"caption service {e.code}: {body}")
    if status == 202 and d.get("jobId"):                       # long videos are processed asynchronously
        for _ in range(30):
            time.sleep(2)
            status, d = _get(f"{SUPADATA}/transcript/{d['jobId']}", {"x-api-key": key, "User-Agent": "pawed/1.0"}, timeout=30)
            if d.get("status") in ("completed", None) and d.get("content") is not None:
                break
            if d.get("status") == "failed":
                raise NoCaptions("no captions available")
    content = d.get("content")
    if isinstance(content, str):                                # provider sent plain text: no timestamps, spread them evenly later
        raise NoCaptions("caption service returned no timed segments")
    segs = [(int((c.get("offset") or 0) // 1000), (c.get("text") or "").replace("\n", " ").strip()) for c in content or []]
    segs = [s for s in segs if s[1]]
    if not segs:
        raise NoCaptions("no captions available")
    return segs


def captions(vid):
    """Same dict the Mac relay posts to /api/vidsum/relay/transcript: transcript + metadata."""
    meta = _videos_meta([vid]).get(vid)
    if not meta:
        raise NoCaptions("video not found or private")
    if meta.get("duration") and meta["duration"] < 150:
        raise RuntimeError(f"too short ({meta['duration']}s), skipped")
    segs = None
    for lang in [meta.get("lang"), "he", "en", None]:             # the video's own language first, then the usual two, then whatever exists
        if lang is None and segs is not None:
            break
        try:
            segs = _supadata(vid, lang)
            break
        except NoCaptions:
            continue
    if not segs:
        raise NoCaptions("no captions available")
    return {"transcript": _blocks(segs), "duration": meta["duration"], "published_at": meta["published_at"],
            "published": (meta["published_at"] or "")[:10] or None, "title": meta["title"], "channel": meta["channel"],
            "description": meta["description"], "source": "captions:supadata"}
