"""Vidsum server-side: YouTube link -> Gemini (reads the URL itself, so Render's
blocked IP never touches YouTube) -> detailed RTL summary stored as an article
served at /vidsum/article/<slug>."""
import json, math, os, re, threading, uuid, time, html as _html, unicodedata
import urllib.request, urllib.parse, urllib.error

import multiuser
from multiuser import secret, GEMINI_MODEL, BudgetExhausted, current_user
from multiuser import log as _mlog

_SECRET_RE = re.compile(r"(lr_[0-9a-fA-F]{16,}|Bearer\s+\S+|AIza[\w-]{20,}|key=[^&\s'\"]+)")


def _scrub(msg):
    """Never let an API key reach logs or the public job-status endpoint."""
    return _SECRET_RE.sub("[redacted]", str(msg))


def log(msg):
    _mlog(_scrub(msg))

ART_DIR = os.path.join(multiuser.DATA_DIR, "vidsum_articles")
JOBS_PATH = os.path.join(multiuser.DATA_DIR, "vidsum_jobs.json")
LOCK = threading.Lock()
WORKER = threading.Semaphore(1)          # one Gemini video job at a time
PUBLIC_DAILY_CAP = 15                    # non-admin submissions per day (admin unlimited)
MAX_ACTIVE = 8
ACCENT = "#2c5f7c"
HEADNOTE = "Summarized by Pawed (by Mr. Brosh)"

_YT_RE = re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/|v/))([\w-]{11})")


def yt_id(url):
    m = _YT_RE.search(url or "")
    return m.group(1) if m else None


# ------------------------------------------------------------------ store ---
def _load_jobs():
    try:
        with open(JOBS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_jobs(j):
    os.makedirs(os.path.dirname(JOBS_PATH), exist_ok=True)
    tmp = JOBS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
    os.replace(tmp, JOBS_PATH)


EVENTS_PATH = os.path.join(multiuser.DATA_DIR, "vidsum_events.jsonl")
EV_LOCK = threading.Lock()
_STAGE = {"needs_transcript": "queued", "running": "writing", "queued": "transcript", "done": "done",
          "failed": "failed", "no_captions": "no_captions"}


def _event(vid, stage, detail="", rec=None):
    """Append one line to the live activity log shown at /vidsum/logs."""
    rec = rec or {}
    ev = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), "vid": vid, "stage": stage, "title": rec.get("title") or "",
          "channel": rec.get("channel") or "", "detail": _scrub(detail)[:300], "slug": rec.get("slug") or ""}
    try:
        with EV_LOCK:
            os.makedirs(os.path.dirname(EVENTS_PATH), exist_ok=True)
            with open(EVENTS_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            if os.path.getsize(EVENTS_PATH) > 3_000_000:            # keep the newest half
                with open(EVENTS_PATH, encoding="utf-8") as f:
                    lines = f.readlines()
                with open(EVENTS_PATH, "w", encoding="utf-8") as f:
                    f.writelines(lines[len(lines) // 2:])
    except OSError:
        pass


def _recent_events(limit=300):
    try:
        with EV_LOCK, open(EVENTS_PATH, encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
    except OSError:
        return []
    out = []
    for ln in reversed(lines):
        try:
            out.append(json.loads(ln))
        except ValueError:
            pass
    return out


def _set_job(vid, **kw):
    with LOCK:
        jobs = _load_jobs()
        if "error" in kw:
            kw["error"] = _scrub(kw["error"])
        jobs.setdefault(vid, {}).update(kw)
        jobs[vid]["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        _save_jobs(jobs)
        rec = dict(jobs[vid])
    if "status" in kw and kw["status"] in _STAGE:
        _event(vid, _STAGE[kw["status"]], kw.get("error") or kw.get("detail") or "", rec)


def slugify(title):
    s = unicodedata.normalize("NFKC", title or "").lower()
    s = re.sub(r"[^\w֐-׿]+", "-", s).strip("-_")
    return s[:70].strip("-_") or "summary"


def _rel(a):
    """Episode release moment as 'YYYY-MM-DD HH:MM:SS' (UTC). Unknown dates sort LAST: the moment we processed an
    episode says nothing about when it came out, so it is never used for ordering."""
    pa = (a.get("published_at") or "").replace("T", " ").replace("Z", "")[:19]
    if len(pa) == 19:
        return pa
    if (a.get("published") or "")[:10].count("-") == 2:
        return a["published"][:10] + " 12:00:00"
    return ""


def _articles():
    out = []
    try:
        names = os.listdir(ART_DIR)
    except OSError:
        return out
    for n in names:
        if n.endswith(".json"):
            try:
                with open(os.path.join(ART_DIR, n), encoding="utf-8") as f:
                    out.append(json.load(f))
            except Exception:
                pass
    out.sort(key=_rel, reverse=True)                   # newest release first, everywhere
    return out


def _find_by_vid(vid):
    for a in _articles():
        if a.get("vid") == vid:
            return a
    return None


def _unique_slug(title, vid):
    base = slugify(title)
    taken = {a["slug"] for a in _articles()}
    if base not in taken:
        return base
    return f"{base}-{vid[:5].lower()}"


# ----------------------------------------------------------------- gemini ---
TOPICS = ["פוליטיקה", "טכנולוגיה", "כלכלה", "ספורט", "תרבות", "רכילות", "בריאות"]
SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "standfirst": {"type": "STRING"},
        "topic": {"type": "STRING", "enum": TOPICS},
        "lead": {"type": "STRING"},
        "key_points": {"type": "ARRAY", "items": {"type": "STRING"}},
        "blocks": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "type": {"type": "STRING", "enum": ["h2", "p", "quote", "list"]},
            "text": {"type": "STRING"},
            "ts": {"type": "STRING"},
            "speaker": {"type": "STRING"},
            "items": {"type": "ARRAY", "items": {"type": "STRING"}}},
            "required": ["type", "text", "ts"]}},
    },
    "required": ["title", "standfirst", "topic", "lead", "key_points", "blocks"],
}


_META = {}
_LAST_USAGE = {}


def _dur_from_usage():
    """Video length from Gemini's own token accounting (audio = 32 tokens/s) when the watch page is unreachable."""
    for d in (_LAST_USAGE.get('promptTokensDetails') or []):
        if d.get('modality') == 'AUDIO' and d.get('tokenCount'):
            return round(d['tokenCount'] / 32)
    return None


def _video_meta(vid):
    """(length in seconds, publish date YYYY-MM-DD) from the watch page; None where unavailable."""
    if vid in _META:
        return _META[vid]
    dur = pub = None
    try:
        h = _http(f"https://www.youtube.com/watch?v={vid}")
        m = re.search(r'"lengthSeconds":"(\d+)"', h)
        dur = int(m.group(1)) if m else None
        m = re.search(r'"publishDate":"(\d{4}-\d\d-\d\d)', h)
        pub = m.group(1) if m else None
    except Exception:
        pass
    _META[vid] = (dur, pub)
    return _META[vid]


def _duration(vid):
    return _video_meta(vid)[0]


def _fmt(sec):
    h, r = divmod(int(sec), 3600)
    return f"{h}:{r // 60:02d}:{r % 60:02d}" if h else f"{r // 60}:{r % 60:02d}"


def _norm_ts(ts):
    """m:ss with minutes >= 60 -> h:mm:ss."""
    sec = _ts_sec(ts)
    return _fmt(sec) if sec is not None else ""


def _prompt(title, channel, dur=None, retry=False):
    m = (dur or 0) / 60
    words = min(1800, round(500 + 10 * m)) if dur else 900
    quotes = max(3, min(8, round(m / 12))) if dur else 4
    extra = ""
    if dur:
        extra = (f"\nThe video is EXACTLY {_fmt(dur)} long ({dur} seconds). No timestamp may exceed {_fmt(dur)}. "
                 + ("Use h:mm:ss for any time past 59:59. " if dur >= 3600 else "")
                 + "Only give a timestamp you can actually place in the audio; never space them evenly or guess.")
    if retry:
        extra += "\nYour previous attempt had timestamps beyond the video length or invented evenly-spaced ones. Re-listen and give real ones."
    return f"""You are a news editor turning the attached YouTube video ("{title}", channel "{channel}") into a Hebrew NEWS ARTICLE for a news portal.{extra}
Write like an Israeli news site feature, not like a meeting summary:
- title: a sharp, specific Hebrew headline stating the main claim or story (no clickbait, no question marks unless essential). standfirst: 1-2 sentences under the headline. lead: one 200-char teaser.
- topic: the single best-fitting section from the allowed list.
- key_points: 4-5 short Hebrew sentences ("עיקרי הדברים").
- blocks: the article body, in order. Every block MUST carry its content in "text" (for "list" blocks put the bullets in "items" and leave "text" empty). Use type "h2" for subheadings (a new one every 2-4 paragraphs), "p" for flowing prose paragraphs, "list" (with "items") at most once for a real enumeration, and "quote" for pull quotes.
- About {words} Hebrew words in total across the "p" blocks. Third person, past/present tense news style, attribute claims ("לדבריו", "לטענתו"), keep concrete names, numbers, examples and the logic of the argument. Do not invent facts; do not editorialize.
- Every "p" block has "ts": the timestamp (m:ss or h:mm:ss) where its content is said. Cover the whole video to the end, chronologically.
- Include {quotes} "quote" blocks: the MOST PROVOCATIVE, punchy, quotable statements actually spoken, copied as close to verbatim as you can hear them, each under 25 words, with "speaker" (name + a few words of context, e.g. "אלון אולמן, על מנהיגות") and "ts". Place each quote right after the paragraph it relates to.
Return only JSON matching the schema."""


def _gemini(parts, media_low=True, schema=None, max_out=32768):
    key = (secret("GEMINI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")
    gc = {"temperature": 0.3, "response_mime_type": "application/json",
          "response_schema": schema or SCHEMA, "maxOutputTokens": max_out}
    if media_low:
        gc["mediaResolution"] = "MEDIA_RESOLUTION_LOW"   # ~100 tok/s of video instead of ~300
    body = {"contents": [{"role": "user", "parts": parts}], "generationConfig": gc}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
    last = None
    for attempt in range(3):
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                res = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            last = e.read().decode()[:600]
            if e.code == 429 and "spending cap" in last:
                raise BudgetExhausted(last)
            if e.code == 400 and media_low and "mediaResolution" in last:
                return _gemini(parts, media_low=False, schema=schema, max_out=max_out)
            if e.code in (429, 500, 503) and attempt < 2:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"gemini {e.code}: {last}")
    cand = res["candidates"][0]
    text = cand["content"]["parts"][0]["text"]
    data = json.loads(text)
    tokens = int((res.get("usageMetadata") or {}).get("totalTokenCount") or 0)
    global _LAST_USAGE
    _LAST_USAGE = res.get("usageMetadata") or {}
    return data, tokens, cand.get("finishReason")


# ------------------------------------------------- LunaRoute (text-only, free) ---
LUNA_URL = "https://gw.lunaroute.com"
LUNA_MODEL = os.environ.get("VIDSUM_LUNA_MODEL", "deepseek-4.1-flash")
SCHEMA_HINT = """{"title": str, "standfirst": str, "topic": one of %s, "lead": str, "key_points": [str],
 "blocks": [{"type": "h2"|"p"|"quote"|"list", "text": str, "ts": "m:ss or h:mm:ss", "speaker": str (quotes only), "items": [str] (list only)}]}""" % json.dumps(TOPICS, ensure_ascii=False)


def _luna(prompt, max_tokens=24000):
    key = (secret("LUNAROUTE_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("LUNAROUTE_API_KEY missing")
    body = {"model": LUNA_MODEL, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
    last = None
    for attempt in range(4):
        req = urllib.request.Request(LUNA_URL + "/v1/messages", data=json.dumps(body).encode(),
                                     headers={"Authorization": "Bearer " + key, "anthropic-version": "2023-06-01",
                                              "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                res = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = e.read().decode()[:400]
            if e.code in (429, 500, 502, 503, 529) and attempt < 3:
                time.sleep(15 * (attempt + 1))
                continue
            raise RuntimeError(f"luna {e.code}: {last}")
        text = "".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        i, j = text.find("{"), text.rfind("}")
        usage = res.get("usage") or {}
        try:
            if i < 0 or j < i:
                raise ValueError("no JSON in reply: " + text[:120])
            return (json.loads(text[i:j + 1]), int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0)),
                    res.get("stop_reason"))
        except ValueError as e:                      # malformed JSON (often an unescaped quote in Hebrew): ask again
            last = str(e)[:200]
            log(f"vidsum luna bad JSON (attempt {attempt + 1}): {last}")
    raise RuntimeError("luna kept returning invalid JSON: " + str(last))


def _text_prompt(title, channel, dur, transcript, retry=False):
    p = _prompt(title, channel, dur, retry).replace("the attached YouTube video", "the video whose transcript is below")
    p = p.replace("Return only JSON matching the schema.", "")
    return (p + "\nThe transcript is auto-generated Hebrew speech recognition and contains word errors: infer the intended words "
            "from context and fix obvious mistakes (names, numbers), never copy garbled text.\n"
            "Return ONLY one valid JSON object, no markdown. Never use the ASCII double-quote character inside a string value (use ״ or single quotes instead), so the JSON stays valid. Shape:\n" + SCHEMA_HINT +
            "\n\nTRANSCRIPT (each line starts with its timestamp in brackets):\n" + transcript)


def _oembed(vid):
    try:
        with urllib.request.urlopen("https://www.youtube.com/oembed?format=json&url=" +
                                    urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}", safe=""),
                                    timeout=20) as r:
            o = json.loads(r.read().decode())
        return o.get("title") or "", o.get("author_name") or ""
    except Exception:
        return "", ""


def _captions_fallback(vid):
    """Best-effort transcript via yt-dlp (often blocked from datacenter IPs)."""
    import subprocess, sys, tempfile, glob
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "yt_dlp", "--skip-download", "--write-auto-subs", "--write-subs",
                        "--sub-langs", "he,en.*,iw", "--sub-format", "vtt", "--no-warnings",
                        "-o", os.path.join(tmp, "s"), f"https://www.youtube.com/watch?v={vid}"],
                       capture_output=True, timeout=120)
        files = glob.glob(os.path.join(tmp, "*.vtt"))
        if not files:
            raise RuntimeError("no captions available")
        raw = open(files[0], encoding="utf-8", errors="ignore").read()
    lines, last = [], ""
    ts = ""
    for ln in raw.splitlines():
        m = re.match(r"(\d\d):(\d\d):(\d\d)\.\d+ -->", ln)
        if m:
            h, mi, s = int(m[1]), int(m[2]), int(m[3])
            ts = f"{h}:{mi:02d}:{s:02d}" if h else f"{mi}:{s:02d}"
            continue
        ln = re.sub(r"<[^>]+>", "", ln).strip()
        if ln and ln != last and not ln.startswith(("WEBVTT", "Kind:", "Language:")):
            lines.append(f"[{ts}] {ln}")
            last = ln
    return "\n".join(lines)[:900000]


def _all_ts(data):
    return [b.get("ts") for b in data.get("blocks", []) if b.get("type") in ("p", "quote")]


def _ts_ok(data, dur):
    ps = [b for b in data.get("blocks", []) if b.get("type") == "p"]
    secs = [t for t in (_ts_sec(x) for x in _all_ts(data)) if t is not None]
    if not secs or len(secs) < 0.8 * len([b for b in data.get("blocks", []) if b.get("type") in ("p", "quote")]):
        return False                                   # most blocks must carry a usable timestamp
    if dur:
        if max(secs) > dur * 1.02 + 10:
            return False                               # beyond the end of the video
        if max(secs) < dur * 0.8:
            return False                               # did not cover the whole video
    return True


def summarize(vid):
    url = f"https://www.youtube.com/watch?v={vid}"
    title, channel = _oembed(vid)
    dur, published = _video_meta(vid)
    method = None
    data = tokens = fin = None
    for retry in (False, True):
        prompt = _prompt(title, channel, dur, retry)
        try:
            data, tokens, fin = _gemini([{"file_data": {"file_uri": url}}, {"text": prompt}])
            method = "gemini-video"
        except BudgetExhausted:
            raise
        except Exception as e:
            log(f"vidsum {vid} video path failed ({str(e)[:200]}); trying captions")
            try:
                tr = _captions_fallback(vid)
            except Exception as e2:
                raise RuntimeError(f"Gemini could not read the video ({str(e)[:230]}); captions: {str(e2)[:60]}")
            data, tokens, fin = _gemini([{"text": prompt + "\n\nTranscript with timestamps:\n" + tr}])
            method = "gemini-captions"
        if not dur:
            dur = _dur_from_usage()
            if dur:
                log(f"vidsum {vid} duration from tokens: {dur}s")
        if _ts_ok(data, dur):
            break
        log(f"vidsum {vid} bad timestamps (dur={dur}); {'retrying' if not retry else 'clamping'}")
    return _finalize(data, dur, {"channel": channel, "src_title": title, "tokens": tokens, "method": method,
                                 "finish": fin, "published": published})


def _finalize(data, dur, extra):
    blocks = []
    for b in data.get("blocks", []):
        t = b.get("type")
        if t in ("p", "quote") and not (b.get("text") or "").strip() and b.get("items"):
            b = {**b, "text": " ".join(str(i) for i in b["items"])}      # model put prose in items
        if t == "list" and b.get("items"):
            blocks.append({"type": "list", "items": [str(i) for i in b["items"]]})
        elif t in ("h2", "p", "quote") and (b.get("text") or "").strip():
            ts = b.get("ts") or ""
            sec = _ts_sec(ts)
            ts = "" if (sec is None or (dur and sec > dur + 5)) else _norm_ts(ts)
            nb = {"type": t, "text": b["text"].strip(), "ts": ts}
            if t == "quote":
                nb["speaker"] = (b.get("speaker") or "").strip()
            blocks.append(nb)
    if sum(1 for b in blocks if b["type"] == "p") < 3:
        raise RuntimeError(f"empty article: blocks={[(b.get('type'), len(b.get('text') or '')) for b in data.get('blocks', [])][:12]} keys={list(data)}")
    return {"title": data["title"].strip(), "standfirst": data.get("standfirst", "").strip(), "blocks": blocks,
            "key_points": [k.strip() for k in data.get("key_points", []) if k.strip()][:6],
            "topic": data.get("topic") if data.get("topic") in TOPICS else "תרבות",
            "lead": (data.get("lead") or data.get("standfirst") or "").strip(),
            "duration": dur, **extra}


def _release_from_feeds(vid, source_id=None):
    """Real release moment (UTC ISO) of a video from the public RSS feed of its source / its channel."""
    import datetime as _dt
    feeds = []
    if source_id and not source_id.startswith("pending-"):
        feeds.append(source_id)
    try:
        with urllib.request.urlopen("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(
                f"https://www.youtube.com/watch?v={vid}", safe=""), timeout=20) as r:
            au = (json.loads(r.read().decode()).get("author_url") or "")
        if au:
            cid, _n = resolve_channel(au)
            if cid not in feeds:
                feeds.append(cid)
    except Exception:
        pass
    for fid in feeds:
        try:
            x = _http(_feed_url(fid))
        except Exception:
            continue
        m = re.search(r"<yt:videoId>" + re.escape(vid) + r"</yt:videoId>.*?<published>([^<]+)</published>", x, re.S)
        if m:
            try:
                dt = _dt.datetime.fromisoformat(m.group(1).replace("Z", "+00:00")).astimezone(_dt.timezone.utc)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                pass
    return None


def _save_article(vid, d):
    if not d.get("published_at"):
        try:
            pa = _release_from_feeds(vid, _load_jobs().get(vid, {}).get("source"))
            if pa:
                d = {**d, "published_at": pa, "published": pa[:10]}
        except Exception as e:
            log(f"vidsum {vid} release lookup failed: {str(e)[:100]}")
    slug = _unique_slug(d["title"], vid)
    src_id = _load_jobs().get(vid, {}).get("source")
    if src_id:
        d = {**d, "source_id": src_id}
    art = {"slug": slug, "vid": vid, "url": f"https://www.youtube.com/watch?v={vid}",
           "created": time.strftime("%Y-%m-%d %H:%M:%S"), **d}
    os.makedirs(ART_DIR, exist_ok=True)
    tmp = os.path.join(ART_DIR, slug + ".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(art, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(ART_DIR, slug + ".json"))
    _set_job(vid, status="done", slug=slug, title=d["title"], error="",
             detail=f"{d.get('method', '')} · {d.get('tokens', 0):,} tokens", channel=d.get("channel") or "")
    log(f"vidsum {vid} DONE slug={slug} tokens={d.get('tokens')} via {d.get('method')}")


def _run(vid):
    """Gemini path: Google reads the YouTube URL itself (costs tokens)."""
    with WORKER:
        _set_job(vid, status="running", started=time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            _save_article(vid, summarize(vid))
        except Exception as e:
            log(f"vidsum {vid} FAILED: {str(e)[:400]}")
            _set_job(vid, status="failed", error=str(e)[:300])


# ----------------------------------------------- transcript relay (free path) ---
TR_DIR = os.path.join(multiuser.DATA_DIR, "vidsum_transcripts")
MAX_WAITING = 800


def _run_luna(vid):
    """LunaRoute path: the Mac relay supplied captions; DeepSeek writes the article."""
    with WORKER:
        _set_job(vid, status="running", started=time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            with open(os.path.join(TR_DIR, vid + ".json"), encoding="utf-8") as f:
                tr = json.load(f)
            dur, pub = tr.get("duration"), tr.get("published")
            title, channel = tr.get("title", ""), tr.get("channel", "")
            data = fin = None
            for retry in (False, True):
                prompt = _text_prompt(title, channel, dur, tr["transcript"], retry)
                if tr.get("description"):
                    prompt += "\n\nVIDEO DESCRIPTION (use for names and context):\n" + tr["description"][:2500]
                data, tokens, fin = _luna(prompt)
                if _ts_ok(data, dur):
                    break
                log(f"vidsum {vid} luna bad timestamps (dur={dur}); {'retrying' if not retry else 'accepting'}")
            _save_article(vid, _finalize(data, dur, {"channel": channel, "src_title": title, "tokens": tokens,
                                                     "method": "luna-captions", "finish": fin, "published": pub,
                                                     "published_at": tr.get("published_at")}))
        except Exception as e:
            log(f"vidsum {vid} luna FAILED: {str(e)[:400]}")
            _set_job(vid, status="failed", error=str(e)[:300])


def submit(url, admin, engine="luna", source=None):
    """-> (http_code, payload). engine "luna": wait for the Mac relay's transcript; "gemini": immediate (costs tokens)."""
    vid = yt_id(url)
    if not vid:
        return 400, {"ok": False, "error": "not a YouTube link"}
    ex = _find_by_vid(vid)
    if ex:
        return 200, {"ok": True, "id": vid, "status": "done", "slug": ex["slug"], "existing": True}
    with LOCK:
        jobs = _load_jobs()
        cur = jobs.get(vid)
        if cur and cur.get("status") in ("queued", "running", "needs_transcript") and not (
                engine == "gemini" and cur.get("status") == "needs_transcript"):
            return 200, {"ok": True, "id": vid, "status": cur["status"]}
        active = sum(1 for j in jobs.values() if j.get("status") in ("queued", "running"))
        waiting = sum(1 for j in jobs.values() if j.get("status") == "needs_transcript")
        if (active >= MAX_ACTIVE and not admin) or waiting >= MAX_WAITING:
            return 429, {"ok": False, "error": "busy, try again in a few minutes"}
        if not admin:
            today = time.strftime("%Y-%m-%d")
            n = sum(1 for j in jobs.values() if j.get("public") and (j.get("submitted") or "").startswith(today))
            if n >= PUBLIC_DAILY_CAP:
                return 429, {"ok": False, "error": "daily limit reached"}
        status = "needs_transcript" if engine == "luna" else "queued"
        jobs[vid] = {"status": status, "engine": engine, "public": not admin, "source": source or (cur or {}).get("source"),
                     "submitted": time.strftime("%Y-%m-%d %H:%M:%S")}
        _save_jobs(jobs)
    if engine != "luna":
        threading.Thread(target=_run, args=(vid,), daemon=True).start()
    return 202, {"ok": True, "id": vid, "status": status}


def relay_discovered(req):
    """The Mac relay scanned a source's feed (YouTube answers it, not Render): apply the same rules the server watcher uses."""
    sid = str(req.get("source_id") or "")
    today = time.strftime("%Y-%m-%d")
    out = {"submitted": 0, "skipped": 0, "deferred": 0}
    with LOCK:
        d = _load_ch()
        ch = next((c for c in d["channels"] if c["id"] == sid), None)
        if not ch:
            return out
        seen = set(ch.setdefault("seen", []))
        used = sum(1 for e in d["log"] if e.get("day") == today and e.get("kind") == "submit")
        owner_used = sum(1 for e in d["log"] if e.get("day") == today and e.get("kind") == "submit"
                         and ch.get("owner_id") and e.get("owner") == ch.get("owner_id"))
        added = (ch.get("added") or "")[:19]
        for it in sorted(req.get("items") or [], key=lambda i: i.get("published", "")):
            vid = str(it.get("vid") or "")
            if not re.fullmatch(r"[\w-]{11}", vid) or vid in seen:
                continue
            pub = (it.get("published") or "").replace("T", " ").replace("Z", "")[:19]
            if (pub and pub < added and not ch.get("backfill")) or (it.get("duration") or 999) < 150:
                seen.add(vid); out["skipped"] += 1               # older than the subscription, or a Short
                continue
            if used >= WATCH_DAILY_CAP or (ch.get("owner_id") and owner_used >= USER_DAILY_VIDEOS):
                out["deferred"] += 1                              # not marked seen: picked up on a later run
                continue
            code, payload = submit(f"https://www.youtube.com/watch?v={vid}", True, "luna", sid)
            seen.add(vid)
            if code == 202:                                      # genuinely new (already-known videos answer 200)
                used += 1
                owner_used += 1 if ch.get("owner_id") else 0
                out["submitted"] += 1
                d["log"].append({"day": today, "kind": "submit", "vid": vid, "channel": ch["name"], "owner": ch.get("owner_id"),
                                 "at": time.strftime("%H:%M:%S")})
                log(f"vidsum relay discovery: {ch['name']} -> {vid} ({payload.get('status')})")
        ch["seen"] = sorted(seen)[-300:]
        ch["checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
        ch["error"] = ""
        ch.pop("backfill", None) if ch.get("backfill") and out["deferred"] == 0 else None
        _save_ch(d)
    return out


def relay_queue(limit=15):
    return [{"vid": v, "url": f"https://www.youtube.com/watch?v={v}", "submitted": j.get("submitted")}
            for v, j in sorted(_load_jobs().items(), key=lambda kv: kv[1].get("submitted", ""))
            if j.get("status") == "needs_transcript"][:limit]


def relay_transcript(req):
    vid = str(req.get("vid") or "")
    if not re.fullmatch(r"[\w-]{11}", vid) or len(req.get("transcript") or "") < 200:
        raise ValueError("bad vid or transcript too short")
    os.makedirs(TR_DIR, exist_ok=True)
    with open(os.path.join(TR_DIR, vid + ".json"), "w", encoding="utf-8") as f:
        json.dump({k: req.get(k) for k in ("transcript", "duration", "published", "published_at", "title", "channel", "description", "source")},
                  f, ensure_ascii=False)
    _set_job(vid, status="queued", error="", title=req.get("title") or "", channel=req.get("channel") or "")
    threading.Thread(target=_run_luna, args=(vid,), daemon=True).start()


def resume_stuck():
    """Server restart mid-job: re-run anything left queued/running."""
    for vid, j in _load_jobs().items():
        if j.get("status") in ("queued", "running"):
            threading.Thread(target=_run, args=(vid,), daemon=True).start()


# ------------------------------------------------------------------ pages ---
def _ts_sec(ts):
    try:
        p = [int(x) for x in str(ts).split(":")]
        return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]
    except Exception:
        return None


CSS = """:root{--ink:#1c1b19;--muted:#6f6a61;--line:#e6e2d9;--bg:#f7f6f1;--accent:%(a)s;--chip:#eef3f6;--chiptext:%(a)s}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Heebo","Assistant","Segoe UI",system-ui,sans-serif;direction:rtl;text-align:right;line-height:1.75}
.wrap{max-width:840px;margin:0 auto;padding:48px 26px 80px}
.kicker{color:var(--accent);font-weight:700;font-size:.82rem;margin:0 0 8px}.kicker a{color:inherit;text-decoration:none}
h1{font-size:1.7rem;line-height:1.26;margin:0 0 10px}
.sub{color:var(--muted);font-size:.92rem;margin:0 0 8px}
.meta{color:var(--muted);font-size:.85rem;margin:0 0 30px}.meta a{color:var(--accent);text-decoration:none}.meta a:hover{text-decoration:underline}
.headnote{color:var(--muted);font-style:italic;font-size:.85rem;margin:-18px 0 30px}
section{margin:0 0 28px}
h2{font-size:1.1rem;margin:0 0 12px;padding-bottom:8px;border-bottom:2px solid var(--line)}
.secnum{color:var(--accent);font-weight:800;margin-inline-end:10px}
ul{margin:0;padding:0;list-style:none}
li{position:relative;margin:0 0 13px;padding-inline-start:16px}
li::before{content:"\\2014";position:absolute;right:-14px;color:var(--accent);font-weight:700}
.ts{display:inline-block;margin-inline-start:6px;padding:1px 8px;background:var(--chip);color:var(--chiptext);border-radius:20px;font-size:.78rem;font-weight:600;text-decoration:none;white-space:nowrap;direction:ltr}
.list a.item{display:block;padding:14px 18px;margin:0 0 10px;background:#fff;border:1px solid var(--line);border-radius:10px;color:var(--ink);text-decoration:none}
.list a.item:hover{border-color:var(--accent)}.list small{display:block;color:var(--muted)}
@media(prefers-color-scheme:dark){:root{--ink:#ece9e1;--muted:#a39d92;--line:#35332e;--bg:#171614;--chip:#232a2f;--chiptext:#8fc1dc;--accent:#8fc1dc}
.list a.item{background:#1f1e1b}}
""" % {"a": ACCENT}


def _page(title, body, desc=""):
    e = _html.escape
    return (f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<style>{CSS}</style></head><body><div class="wrap">{body}</div></body></html>')


def article_html(a):
    e = _html.escape
    out = ['<p class="kicker"><a href="/vidsum/articles">Pawed &middot; כל הסיכומים</a></p>',
           f'<h1>{e(a["title"])}</h1>']
    if a.get("subtitle"):
        out.append(f'<p class="sub">{e(a["subtitle"])}</p>')
    out.append(f'<p class="meta"><a href="{e(a["url"])}">פתיחת המקור ↗</a></p>')
    out.append(f'<p class="headnote">{e(HEADNOTE)}</p>')
    for i, s in enumerate(a["sections"], 1):
        out.append(f'<section><h2><span class="secnum">{i}</span>{e(s["title"])}</h2><ul>')
        for b in s["bullets"]:
            li = e(b["text"])
            sec = _ts_sec(b.get("ts"))
            if sec is not None:
                li += f' <a class="ts" href="{e(a["url"])}&amp;t={sec}s">▶ {e(b["ts"])}</a>'
            out.append(f"<li>{li}</li>")
        out.append("</ul></section>")
    return _page(a["title"], "".join(out), a.get("subtitle", ""))


def index_html():
    e = _html.escape
    arts = _articles()
    items = "".join(
        f'<a class="item" href="/vidsum/article/{urllib.parse.quote(a["slug"])}">{e(a["title"])}'
        f'<small>{e(a.get("channel", ""))} &middot; {e(a["created"][:10])}</small></a>' for a in arts)
    body = ('<p class="kicker"><a href="/vidsum">&larr; Pawed</a></p><h1>סיכומי וידאו</h1>'
            f'<div class="list">{items or "<p class=sub>אין עדיין סיכומים.</p>"}</div>')
    return _page("סיכומי וידאו", body)



import vidsum_render
DISCLAIMER = "הדברים המובאים הם של המרואיינים ולא נבדקו. הכתבה נערכה אוטומטית מתוך תמלול של השיחה."


def render_article(a):
    if a.get("blocks"):
        return vidsum_render.render(a, news_items(), base="", disclaimer=a.get("disclaimer") or DISCLAIMER)
    return article_html(a)



# ------------------------------------------------ generated cover art (no usable YouTube thumbnail) ---
_COVER_ACC = {"כלכלה": "#e0a43a", "פוליטיקה": "#6fbf5a", "טכנולוגיה": "#ff6b4a", "ספורט": "#ff9a3c",
              "תרבות": "#b07be0", "רכילות": "#f07ab0", "בריאות": "#3fcfb4"}
_KEYS = [("chip", r"\bAI\b|בינה מלאכותית|GPT|סוכן|סוכנים|אלגוריתם|סייבר|הייטק|רובוט|OpenAI|אנטרופיק|צ'אט"),
         ("chart", r"מניות|בורסה|S&P|נאסד|שוק ההון|השקעות|מסחר|וול סטריט|כלכל|ריבית|אינפלציה|מטבע|קריפטו|דולר"),
         ("ball", r"כדורגל|ליגה|שחקן|קבוצ|מונדיאל|יורו|מאמן|כדורסל|ספורט|משחק"),
         ("columns", r"בחירות|ממשלה|כנסת|נתניהו|פוליטי|קואליציה|ראש הממשלה|שר |סקר|מפלגה"),
         ("heart", r"בריאות|רפוא|מחל|סוכר|תזונה|מוח|דיאטה|שינה|רופא|טיפול"),
         ("mic", r"פודקאסט|ראיון|תרבות|מוזיק|סרט|טלוויזיה|סלבס|רכילות|אופנה|קומדי|סאטיר")]
_TOPIC_MOTIF = {"טכנולוגיה": "chip", "כלכלה": "chart", "ספורט": "ball", "פוליטיקה": "columns", "בריאות": "heart",
                "תרבות": "mic", "רכילות": "mic"}


def _motif_name(a):
    text = f"{a.get('title', '')} {a.get('lead', '')} {a.get('standfirst', '')}"
    for name, rx in _KEYS:
        if name == _TOPIC_MOTIF.get(a.get("topic")) and re.search(rx, text, re.I):
            return name
    for name, rx in _KEYS[:2]:                        # AI / markets override the section when clearly the subject
        if re.search(rx, a.get("title", ""), re.I):
            return name
    return _TOPIC_MOTIF.get(a.get("topic"), "mic")


def _motif_svg(m, acc):
    w, k = "#ffffff", acc
    if m == "chip":
        pins = "".join(f'<line x1="{x}" y1="215" x2="{x}" y2="170" /><line x1="{x}" y1="505" x2="{x}" y2="550" />' for x in range(520, 761, 40))
        pins += "".join(f'<line x1="505" y1="{y}" x2="460" y2="{y}" /><line x1="775" y1="{y}" x2="820" y2="{y}" />' for y in range(260, 461, 50))
        nodes = [(250, 200), (300, 360), (230, 520), (1030, 190), (990, 370), (1060, 520), (640, 90), (640, 640)]
        lines = "".join(f'<path d="M{x} {y} L{640 + (-1 if x < 640 else 1) * 195} 360" opacity=".45"/><circle cx="{x}" cy="{y}" r="9" fill="{k}" stroke="none"/>' for x, y in nodes)
        return (f'<g fill="none" stroke="{w}" stroke-width="5" stroke-linecap="round">{lines}{pins}'
                f'<rect x="500" y="230" width="280" height="260" rx="26" fill="rgba(255,255,255,.08)"/>'
                f'<rect x="545" y="275" width="190" height="170" rx="14" stroke="{k}"/></g>'
                f'<text x="640" y="395" text-anchor="middle" font-family="Arial Black,Arial" font-weight="900" font-size="110" fill="{w}">AI</text>')
    if m == "chart":
        bars = [(380, 430, 150, 560), (450, 400, 130, 520), (520, 360, 200, 540), (590, 330, 110, 470), (660, 290, 170, 480),
                (730, 250, 120, 410), (800, 215, 190, 430), (870, 190, 100, 330)]
        g = ""
        for i, (x, top, hgt, wick) in enumerate(bars):
            up = i % 3 != 1
            col = k if up else "#ffffff"
            g += (f'<line x1="{x + 20}" y1="{top - 40}" x2="{x + 20}" y2="{top + hgt + 40}" stroke="{col}" stroke-width="5"/>'
                  f'<rect x="{x}" y="{top}" width="40" height="{hgt}" rx="5" fill="{col}" opacity="{.95 if up else .45}"/>')
        grid = "".join(f'<line x1="300" y1="{y}" x2="980" y2="{y}" stroke="#fff" stroke-opacity=".12" stroke-width="2"/>' for y in range(180, 600, 70))
        return grid + g + f'<path d="M330 540 L450 500 L520 470 L600 430 L690 380 L760 320 L850 270 L930 205" fill="none" stroke="{w}" stroke-width="7" stroke-linecap="round" stroke-dasharray="2 16"/>'
    if m == "ball":
        pitch = f'<g fill="none" stroke="{w}" stroke-opacity=".2" stroke-width="4"><circle cx="640" cy="360" r="300"/><line x1="640" y1="60" x2="640" y2="660"/><rect x="140" y="210" width="190" height="300"/><rect x="950" y="210" width="190" height="300"/></g>'
        def _pg(cx, cy, r, scale):
            pts = " ".join("%.0f,%.0f" % (cx + r * scale * math.cos(math.radians(d)), cy + r * scale * math.sin(math.radians(d)))
                           for d in range(-90, 270, 72))
            return '<polygon points="%s" fill="#15131a" opacity=".85"/>' % pts
        pent = _pg(640, 360, 46, 1) + _pg(490, 310, 30, .9) + _pg(790, 310, 30, .9) + _pg(545, 495, 30, .9) + _pg(735, 495, 30, .9)
        return pitch + f'<circle cx="640" cy="360" r="185" fill="{w}"/>' + pent + f'<circle cx="640" cy="360" r="185" fill="none" stroke="{k}" stroke-width="10"/>'
    if m == "columns":
        cols = "".join(f'<rect x="{x}" y="320" width="46" height="200" rx="8" fill="{w}" opacity=".92"/><rect x="{x - 8}" y="300" width="62" height="24" rx="6" fill="{w}"/><rect x="{x - 8}" y="516" width="62" height="20" rx="6" fill="{w}"/>' for x in range(430, 800, 82))
        return (f'<polygon points="380,300 640,170 900,300" fill="{k}"/><rect x="380" y="296" width="520" height="12" fill="{w}"/>{cols}'
                f'<rect x="360" y="536" width="560" height="22" rx="6" fill="{w}"/><rect x="330" y="558" width="620" height="22" rx="6" fill="{w}" opacity=".8"/>'
                f'<circle cx="640" cy="262" r="26" fill="{w}" opacity=".9"/>')
    if m == "heart":
        return (f'<path d="M640 560 C 380 400 400 210 540 200 C 600 196 630 230 640 262 C 650 230 680 196 740 200 C 880 210 900 400 640 560 Z" fill="{k}" opacity=".95"/>'
                f'<path d="M280 380 L470 380 L520 300 L590 470 L650 330 L700 400 L770 400 L840 380 L1000 380" fill="none" stroke="{w}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
    # mic (culture, gossip, general talk)
    waves = "".join(f'<path d="M{640 - r} 330 A{r} {r} 0 0 0 {640 + r} 330" fill="none" stroke="{w}" stroke-opacity="{o}" stroke-width="6" stroke-linecap="round" transform="rotate(180 640 330)" />' for r, o in ((210, .55), (270, .35), (330, .2)))
    spark = "".join(f'<path d="M{x} {y - s} L{x + s * .28} {y - s * .28} L{x + s} {y} L{x + s * .28} {y + s * .28} L{x} {y + s} L{x - s * .28} {y + s * .28} L{x - s} {y} L{x - s * .28} {y - s * .28} Z" fill="{k}"/>' for x, y, s in ((300, 220, 34), (990, 190, 26), (1050, 470, 38), (250, 500, 22)))
    return (waves + f'<rect x="580" y="170" width="120" height="230" rx="60" fill="{w}"/><path d="M540 330 A100 100 0 0 0 740 330" fill="none" stroke="{w}" stroke-width="12" stroke-linecap="round"/>'
            f'<line x1="640" y1="430" x2="640" y2="520" stroke="{w}" stroke-width="12"/><rect x="570" y="520" width="140" height="16" rx="8" fill="{w}"/>' + spark)


def cover_svg(a):
    acc = _COVER_ACC.get(a.get("topic"), "#e0a43a")
    seed = sum(ord(c) for c in a.get("vid", "x"))
    dots = "".join(f'<circle cx="{(seed * (i + 3) * 37) % 1280}" cy="{(seed * (i + 5) * 53) % 720}" r="{3 + (seed * (i + 1)) % 5}" fill="#fff" opacity=".14"/>' for i in range(26))
    e = _html.escape
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" preserveAspectRatio="xMidYMid slice">'
            f'<defs><radialGradient id="g" cx="50%" cy="46%" r="75%"><stop offset="0" stop-color="{acc}" stop-opacity=".55"/><stop offset=".62" stop-color="#1b1722"/><stop offset="1" stop-color="#0e0c12"/></radialGradient></defs>'
            f'<rect width="1280" height="720" fill="url(#g)"/>{dots}{_motif_svg(_motif_name(a), acc)}'
            f'<rect x="56" y="48" rx="22" ry="22" width="{40 + 24 * len(a.get("topic", ""))}" height="48" fill="{acc}"/>'
            f'<text x="{56 + (40 + 24 * len(a.get("topic", ""))) / 2}" y="82" text-anchor="middle" font-family="Arial" font-weight="800" font-size="30" fill="#17120a">{e(a.get("topic", ""))}</text>'
            f'<text x="1224" y="676" text-anchor="end" font-family="Arial" font-weight="700" font-size="34" fill="#fff" fill-opacity=".72">{e((a.get("channel") or "").strip()[:42])}</text></svg>')

# ------------------------------------------------------------- news portal ---
CLS_SCHEMA = {"type": "OBJECT", "properties": {"topic": {"type": "STRING", "enum": TOPICS},
                                               "lead": {"type": "STRING"}}, "required": ["topic", "lead"]}


def backfill():
    """Older articles lack topic/lead: classify them from their text (cheap, text-only)."""
    for a in _articles():
        if (a.get("topic") and a.get("lead")) or a.get("blocks"):
            continue
        try:
            txt = a["title"] + "\n" + "\n".join(b["text"] for s in a["sections"][:3] for b in s["bullets"][:3])
            d, _, _ = _gemini([{"text": "Classify this Hebrew video summary into one news section and write a 1-2 sentence "
                                        "Hebrew teaser (max 220 chars) stating the core story.\n\n" + txt[:6000]}],
                              schema=CLS_SCHEMA, max_out=1024)
            a["topic"] = d["topic"] if d.get("topic") in TOPICS else "תרבות"
            a["lead"] = d.get("lead", "").strip()
            tmp = os.path.join(ART_DIR, a["slug"] + ".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(a, f, ensure_ascii=False, indent=1)
            os.replace(tmp, os.path.join(ART_DIR, a["slug"] + ".json"))
            log(f"vidsum backfill {a['slug']} -> {a['topic']}")
        except Exception as e:
            log(f"vidsum backfill failed {a.get('slug')}: {str(e)[:200]}")


def _length_min(a):
    if a.get("duration"):
        return round(a["duration"] / 60)
    m = 0
    items = [b for s in a.get("sections", []) for b in s.get("bullets", [])] + list(a.get("blocks", []))
    for b in items:
        t = _ts_sec(b.get("ts"))
        if t and t > m:
            m = t
    return round(m / 60)


def news_items():
    return [{"slug": a["slug"], "title": a["title"], "lead": a.get("lead") or a.get("standfirst") or a.get("subtitle", ""),
             "topic": a.get("topic") or "תרבות", "channel": a.get("channel", ""), "vid": a.get("vid"),
             "source_id": a.get("source_id"), "created": a.get("created"), "released": _rel(a),
             "released_time": len((a.get("published_at") or "")) >= 19, "minutes": _length_min(a)} for a in _articles()]


# ------------------------------------------------- users: prefs + visibility ---
MAX_USER_SOURCES = 10
USER_DAILY_VIDEOS = 8


def _vdb():
    c = multiuser.db()
    c.execute("CREATE TABLE IF NOT EXISTS vidsum_prefs(user_id TEXT PRIMARY KEY, hide_base INTEGER DEFAULT 0, "
              "hide_name INTEGER DEFAULT 0, muted TEXT DEFAULT '[]')")
    return c


def get_vprefs(uid):
    with _vdb() as c:
        r = c.execute("SELECT * FROM vidsum_prefs WHERE user_id=?", (uid,)).fetchone()
    if not r:
        return {"hideBase": False, "hideName": False, "muted": []}
    try:
        muted = json.loads(r["muted"] or "[]")
    except ValueError:
        muted = []
    return {"hideBase": bool(r["hide_base"]), "hideName": bool(r["hide_name"]), "muted": muted}


def set_vprefs(uid, req):
    p = get_vprefs(uid)
    if "hideBase" in req:
        p["hideBase"] = bool(req["hideBase"])
    if "hideName" in req:
        p["hideName"] = bool(req["hideName"])
    if isinstance(req.get("muted"), list):
        p["muted"] = [str(x)[:40] for x in req["muted"]][:200]
    with _vdb() as c:
        c.execute("INSERT INTO vidsum_prefs(user_id,hide_base,hide_name,muted) VALUES(?,?,?,?) "
                  "ON CONFLICT(user_id) DO UPDATE SET hide_base=excluded.hide_base, hide_name=excluded.hide_name, muted=excluded.muted",
                  (uid, int(p["hideBase"]), int(p["hideName"]), json.dumps(p["muted"])))
    return p


def _hidden_names():
    with _vdb() as c:
        return {r["user_id"] for r in c.execute("SELECT user_id FROM vidsum_prefs WHERE hide_name=1")}


def _viewer(handler):
    u = current_user(handler)
    if not u or u.get("id") == "admin-token":
        return u
    return u


def _visible_source_ids(viewer):
    """Source ids a signed-in viewer sees in their own view (None = no filtering)."""
    if not viewer or viewer.get("id") == "admin-token":
        return None
    p = get_vprefs(viewer["id"])
    out = set()
    for c in _load_ch()["channels"]:
        owner = c.get("owner_id")
        if owner == viewer["id"]:
            out.add(c["id"])
        elif owner is None:
            if not p["hideBase"]:
                out.add(c["id"])
        elif owner not in p["muted"]:
            out.add(c["id"])
    return out


def _can_edit_source(c, user):
    return bool(user and (user.get("admin") or (c.get("owner_id") and c.get("owner_id") == user.get("id"))))


# ------------------------------------------------------- channel watcher ---
CH_PATH = os.path.join(multiuser.DATA_DIR, "vidsum_channels.json")
WATCH_DAILY_CAP = 30
WATCH_EVERY_S = 3 * 3600
_UA = {"User-Agent": "Mozilla/5.0 (jarcud-vidsum)", "Accept-Language": "en"}


LANGS = {"he": "עברית", "en": "English", "other": "אחר"}
_SEED = {  # url / language / vertical for sources subscribed before the sources table existed
    "UCkfjrjH3vuHaM_Pa_MMSi5Q": ("https://www.youtube.com/@DanielDushi", "he", "תרבות"),
    "UCMjZQzhn3nt7aJIHfYdjc9g": ("https://www.youtube.com/@NadavEyal", "he", "פוליטיקה"),
    "PLZPgleW4baxpCtioKMLwGfWxeUUIuZi49": ("https://www.youtube.com/playlist?list=PLZPgleW4baxpCtioKMLwGfWxeUUIuZi49", "he", "פוליטיקה"),
    "UCwywdccdYsNS_Cs6tS0U_dg": ("https://www.youtube.com/@TrashTechNews", "he", "טכנולוגיה"),
}


def _load_ch():
    try:
        with open(CH_PATH, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {"channels": [], "log": []}
    d.setdefault("channels", [])
    d.setdefault("log", [])
    for c in d["channels"]:
        url, lang, vert = _SEED.get(c["id"], (None, "he", "תרבות"))
        if c["id"].startswith("pending-"):
            c.setdefault("url", "")
        else:
            c.setdefault("url", url or (f"https://www.youtube.com/channel/{c['id']}" if c["id"].startswith("UC")
                                        else f"https://www.youtube.com/playlist?list={c['id']}"))
        c.setdefault("language", lang)
        c.setdefault("vertical", vert)
    return d


def _save_ch(d):
    d["log"] = d["log"][-60:]
    tmp = CH_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CH_PATH)


def _http(url, timeout=20):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _feed_url(fid):
    return ("https://www.youtube.com/feeds/videos.xml?playlist_id=" if not fid.startswith("UC")
            else "https://www.youtube.com/feeds/videos.xml?channel_id=") + fid


def resolve_channel(ref):
    """channel URL / @handle / UC… id / playlist URL (list=PL…) -> (feed_id, name)"""
    ref = ref.strip()
    if ref.startswith("http"):
        host = (urllib.parse.urlparse(ref).hostname or "").lower()
        if not (host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")):
            raise ValueError("only YouTube channel or playlist links are allowed")
    pl = re.search(r"[?&]list=([\w-]+)", ref)
    if pl:
        feed = _http(_feed_url(pl.group(1)))
        n = re.search(r"<title>([^<]+)</title>", feed)
        return pl.group(1), _html.unescape(n.group(1)) if n else pl.group(1)
    m = re.search(r"(UC[\w-]{22})", ref)
    if m:
        cid = m.group(1)
    else:
        if ref.startswith("@"):
            ref = "https://www.youtube.com/" + ref
        if not ref.startswith("http"):
            ref = "https://www.youtube.com/@" + ref
        html = _http(ref.split("?")[0])
        m = (re.search(r'"channelId":"(UC[\w-]{22})"', html) or re.search(r'channel_id=(UC[\w-]{22})', html)
             or re.search(r'youtube\.com/channel/(UC[\w-]{22})', html))
        if not m:
            raise RuntimeError("could not resolve channel id")
        cid = m.group(1)
    feed = _http(_feed_url(cid))
    n = re.search(r"<title>([^<]+)</title>", feed)
    return cid, _html.unescape(n.group(1)) if n else cid


def _is_short(vid):
    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    try:
        op = urllib.request.build_opener(NoRedir)
        op.open(urllib.request.Request(f"https://www.youtube.com/shorts/{vid}", headers=_UA, method="HEAD"), timeout=15)
        return True            # 200 = it is a Short
    except urllib.error.HTTPError as e:
        return e.code not in (301, 302, 303, 307, 308) and e.code == 200
    except Exception:
        return False


def watch_once():
    """Look at every channel feed; summarize videos published after the channel was added."""
    d = _load_ch()
    today = time.strftime("%Y-%m-%d")
    used = sum(1 for e in d["log"] if e.get("day") == today and e.get("kind") == "submit")
    for ch in d["channels"]:
        if ch["id"].startswith("pending-"):          # name only, no YouTube URL yet: not a valid source
            continue
        try:
            feed = _http(_feed_url(ch["id"]))
        except Exception as e:
            ch["error"] = str(e)[:120]
            continue
        ch["error"] = ""
        ch["checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
        seen = set(ch.setdefault("seen", []))
        entries = re.findall(r"<entry>.*?</entry>", feed, re.S)
        for ent in reversed(entries):                       # oldest first
            vm = re.search(r"<yt:videoId>([\w-]{11})</yt:videoId>", ent)
            pm = re.search(r"<published>([^<]+)</published>", ent)
            if not vm or not pm:
                continue
            vid, pub = vm.group(1), pm.group(1)
            if vid in seen:
                continue
            if pub[:19].replace("T", " ") < ch["added"][:19] and not ch.get("backfill"):
                seen.add(vid)                                # older than the subscription: ignore
                continue
            if used >= WATCH_DAILY_CAP:
                break
            if ch.get("owner_id"):
                owner_used = sum(1 for e in d["log"] if e.get("day") == today and e.get("kind") == "submit"
                                 and e.get("owner") == ch["owner_id"])
                if owner_used >= USER_DAILY_VIDEOS:
                    continue
            if _is_short(vid):
                seen.add(vid)
                continue
            code, payload = submit(f"https://www.youtube.com/watch?v={vid}", True, "luna", ch["id"])
            seen.add(vid)
            if code in (200, 202):
                used += 1
                d["log"].append({"day": today, "kind": "submit", "vid": vid, "channel": ch["name"], "owner": ch.get("owner_id"),
                                 "at": time.strftime("%H:%M:%S")})
                log(f"vidsum watcher: {ch['name']} -> {vid} ({payload.get('status')})")
        ch["seen"] = sorted(seen)[-200:]
        if ch.get("backfill") and all(m in seen for m in re.findall(r"<yt:videoId>([\w-]{11})</yt:videoId>", feed)):
            ch["backfill"] = False
    _save_ch(d)


def _watch_loop():
    time.sleep(90)
    while True:
        try:
            watch_once()
        except Exception as e:
            log(f"vidsum watcher error: {str(e)[:200]}")
        time.sleep(WATCH_EVERY_S)


def start_background():
    resume_stuck()
    threading.Thread(target=backfill, daemon=True).start()
    threading.Thread(target=_watch_loop, daemon=True).start()


_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
NEWS_PAGE = os.path.join(_ASSETS, "vidsum_news.html")
V1_PAGE = os.path.join(_ASSETS, "vidsum_discover.html")
SOURCES_PAGE = os.path.join(_ASSETS, "vidsum_sources.html")
LOGS_PAGE = os.path.join(_ASSETS, "vidsum_logs.html")


def _serve(handler, path):
    try:
        with open(path, "rb") as f:
            handler._html(f.read(), "no-store")
    except OSError:
        handler._json({"error": "page missing"}, 404)


def sources_view(viewer=None):
    hidden = _hidden_names()
    vis = _visible_source_ids(viewer)
    out = []
    for c in _load_ch()["channels"]:
        if vis is not None and c["id"] not in vis:
            continue
        owner = c.get("owner_id")
        label = "Pawed" if owner is None else ("אנונימי" if owner in hidden else (c.get("owner_name") or "משתמש"))
        out.append({"id": c["id"], "name": c["name"], "language": c["language"], "url": c["url"],
                    "vertical": c["vertical"], "added": c.get("added", ""), "pending": c["id"].startswith("pending-"),
                    "owner_id": owner, "owner_label": label, "mine": bool(viewer and owner and owner == viewer.get("id")),
                    "base": owner is None, "can_edit": _can_edit_source(c, viewer)})
    return out


def sources_hidden_count(viewer):
    """How many sources the viewer's own preferences are hiding."""
    vis = _visible_source_ids(viewer)
    if vis is None:
        return 0
    return sum(1 for c in _load_ch()["channels"] if c["id"] not in vis)


def add_source(req, user=None):
    url = str(req.get("url") or "").strip()
    name = str(req.get("name") or "").strip()
    lang = req.get("language") if req.get("language") in LANGS else "he"
    vert = req.get("vertical") if req.get("vertical") in TOPICS else "תרבות"
    admin = bool(user and user.get("admin"))
    owner_id = None if admin else user["id"]
    owner_name = None if admin else (user.get("name") or (user.get("email") or "").split("@")[0] or "משתמש")
    if not admin:
        mine = sum(1 for c in _load_ch()["channels"] if c.get("owner_id") == owner_id)
        if mine >= MAX_USER_SOURCES:
            raise ValueError(f"you can have up to {MAX_USER_SOURCES} sources")
    if not url:                                   # pod name only: stays inactive until a YouTube URL is attached
        if not name:
            raise ValueError("enter a podcast name, or a YouTube URL")
        with LOCK:
            d = _load_ch()
            if any(c["name"].strip() == name and c.get("owner_id") == owner_id for c in d["channels"]):
                raise ValueError("this podcast is already in the table")
            cid = "pending-" + uuid.uuid4().hex[:8]
            d["channels"].append({"id": cid, "name": name[:120], "url": "", "language": lang, "vertical": vert,
                                  "added": time.strftime("%Y-%m-%d %H:%M:%S"), "owner_id": owner_id, "owner_name": owner_name})
            _save_ch(d)
        return cid
    cid, found = resolve_channel(url)
    with LOCK:
        d = _load_ch()
        if any(c["id"] == cid for c in d["channels"]):
            raise ValueError("this source is already in the table")
        d["channels"].append({"id": cid, "name": (name or found)[:120], "url": url[:300],
                              "language": lang, "vertical": vert, "added": time.strftime("%Y-%m-%d %H:%M:%S"),
                              "owner_id": owner_id, "owner_name": owner_name,
                              "backfill": bool(req.get("backfill")) and admin})
        _save_ch(d)
    return cid

# ---------------------------------------------------------------- routing ---
ART_PREFIX = "/vidsum/article/"


def handle_get(handler, path, qs):
    if path in ("/vidsum/articles", "/vidsum/articles/"):
        handler._html(index_html(), "no-store")
        return True
    if path.startswith(ART_PREFIX):
        slug = urllib.parse.unquote(path[len(ART_PREFIX):]).strip("/")
        a = None
        if slug and "/" not in slug and ".." not in slug:
            try:
                with open(os.path.join(ART_DIR, slug + ".json"), encoding="utf-8") as f:
                    a = json.load(f)
            except Exception:
                a = None
        if not a:
            handler._json({"error": "article not found"}, 404)
        else:
            handler._html(render_article(a), "no-store")
        return True
    if path in ("/vidsum", "/vidsum/"):
        _serve(handler, NEWS_PAGE)
        return True
    if path in ("/vidsum/news", "/vidsum/news/"):            # old address of the portal
        handler.send_response(302)
        handler.send_header("Location", "/vidsum")
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return True
    if path.startswith("/vidsum/cover/") and path.endswith(".svg"):
        vid = path[len("/vidsum/cover/"):-4]
        a = _find_by_vid(vid) if re.fullmatch(r"[\w-]{11}", vid) else None
        body = cover_svg(a or {"vid": vid, "topic": "תרבות", "title": ""}).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "image/svg+xml")
        handler.send_header("Content-Length", str(len(body)))
        handler.send_header("Cache-Control", "public, max-age=3600")
        handler.end_headers()
        handler.wfile.write(body)
        return True
    if path == "/vidsum/pawed-logo.png":
        try:
            with open(os.path.join(_ASSETS, "pawed-logo.png"), "rb") as f:
                body = f.read()
            handler.send_response(200)
            handler.send_header("Content-Type", "image/png")
            handler.send_header("Content-Length", str(len(body)))
            handler.send_header("Cache-Control", "public, max-age=86400")
            handler.end_headers()
            handler.wfile.write(body)
        except OSError:
            handler._json({"error": "logo missing"}, 404)
        return True
    if path in ("/vidsum/v1", "/vidsum/v1/"):
        _serve(handler, V1_PAGE)
        return True
    if path in ("/vidsum/sources", "/vidsum/sources/"):
        _serve(handler, SOURCES_PAGE)
        return True
    if path in ("/vidsum/logs", "/vidsum/logs/"):
        _serve(handler, LOGS_PAGE)
        return True
    if path == "/api/vidsum/logs":
        jobs = _load_jobs()
        cnt = {}
        for j in jobs.values():
            cnt[j.get("status", "?")] = cnt.get(j.get("status", "?"), 0) + 1
        handler._json({"ok": True, "now": time.strftime("%Y-%m-%d %H:%M:%S"), "summary": cnt, "total": len(jobs),
                       "events": _recent_events(int((qs.get("limit") or ["300"])[0]))})
        return True
    if path == "/api/vidsum/sources":
        user = current_user(handler)
        signed = bool(user and user.get("id") != "admin-token")
        handler._json({"ok": True, "can_edit": bool(user), "admin": bool(user and user.get("admin")),
                       "me": ({"id": user["id"], "name": user.get("name") or user.get("email"), "avatar": user.get("avatar", "")}
                              if signed else None),
                       "prefs": get_vprefs(user["id"]) if signed else None, "hidden": sources_hidden_count(user) if signed else 0,
                       "limit": MAX_USER_SOURCES, "verticals": TOPICS, "languages": LANGS, "sources": sources_view(user)})
        return True
    if path == "/api/vidsum/news":
        user = current_user(handler)
        items = news_items()
        vis = _visible_source_ids(user)
        personal = vis is not None
        if personal:
            base_ok = not get_vprefs(user["id"])["hideBase"]
            items = [i for i in items if (i["source_id"] in vis) or (not i["source_id"] and base_ok)]
        handler._json({"ok": True, "topics": TOPICS, "items": items, "personal": personal,
                       "me": ({"name": user.get("name") or user.get("email")} if user and user.get("id") != "admin-token" else None)})
        return True
    if path == "/api/vidsum/channels":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            d = _load_ch()
            handler._json({"ok": True, "channels": [{k: v for k, v in c.items() if k != "seen"} | {"seen": len(c.get("seen", []))}
                                                    for c in d["channels"]], "log": d["log"][-20:]})
        return True
    if path == "/api/vidsum/articles":
        handler._json({"ok": True, "articles": [
            {k: a.get(k) for k in ("slug", "title", "subtitle", "vid", "channel", "created")} for a in _articles()]})
        return True
    if path == "/api/vidsum/relay/sources":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            handler._json({"ok": True, "sources": [
                {"id": c["id"], "name": c["name"], "added": c.get("added", ""), "backfill": bool(c.get("backfill")),
                 "seen": (c.get("seen") or [])[-300:]} for c in _load_ch()["channels"] if not c["id"].startswith("pending-")]})
        return True
    if path == "/api/vidsum/relay/queue":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            handler._json({"ok": True, "queue": relay_queue(int((qs.get("limit") or ["15"])[0])),
                           "need_dates": [a["vid"] for a in _articles() if a.get("vid") and not a.get("published_at")][:25]})
        return True
    if path == "/api/vidsum/diag":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
            return True
        vid = (qs.get("id") or ["h_hXk-1fP50"])[0]
        res = {}
        try:
            h = _http(f"https://www.youtube.com/watch?v={vid}")
            res["watch_page"] = {"bytes": len(h), "lengthSeconds": bool(re.search(r'"lengthSeconds"', h)),
                                 "bot_wall": ("confirm you" in h and "bot" in h), "consent": "consent.youtube" in h}
        except Exception as e:
            res["watch_page"] = {"error": str(e)[:160]}
        import subprocess, sys, tempfile, glob
        try:
            with tempfile.TemporaryDirectory() as tmp:
                p = subprocess.run([sys.executable, "-m", "yt_dlp", "--skip-download", "--write-auto-subs", "--sub-langs", "he,iw,en.*",
                                    "--sub-format", "vtt", "--no-warnings", "-o", os.path.join(tmp, "s"),
                                    f"https://www.youtube.com/watch?v={vid}"], capture_output=True, text=True, timeout=90)
                res["captions"] = {"files": [os.path.basename(f) for f in glob.glob(os.path.join(tmp, "*.vtt"))],
                                   "stderr": (p.stderr or "")[-300:]}
        except Exception as e:
            res["captions"] = {"error": str(e)[:200]}
        try:
            p = subprocess.run([sys.executable, "-m", "yt_dlp", "-f", "bestaudio", "-g", "--no-warnings",
                                f"https://www.youtube.com/watch?v={vid}"], capture_output=True, text=True, timeout=90)
            res["audio_url"] = {"ok": p.returncode == 0 and p.stdout.startswith("http"), "stderr": (p.stderr or "")[-300:]}
        except Exception as e:
            res["audio_url"] = {"error": str(e)[:200]}
        handler._json({"ok": True, **res})
        return True
    if path == "/api/vidsum/job":
        vid = (qs.get("id") or [""])[0]
        j = _load_jobs().get(vid)
        handler._json({"ok": bool(j), **(j or {})})
        return True
    return False


def delete_article(slug, vid=None):
    n = 0
    for a in _articles():
        if a["slug"] == slug or (vid and a.get("vid") == vid):
            try:
                os.remove(os.path.join(ART_DIR, a["slug"] + ".json"))
                n += 1
                with LOCK:
                    jobs = _load_jobs()
                    jobs.pop(a.get("vid"), None)
                    _save_jobs(jobs)
            except OSError:
                pass
    return n


def patch_release(vid, published_at):
    """Admin: set an article's real release moment (ISO, UTC)."""
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", published_at or ""):
        raise ValueError("published_at must look like 2026-10-17T09:30:00Z")
    for a in _articles():
        if a.get("vid") == vid:
            a["published_at"], a["published"] = published_at, published_at[:10]
            tmp = os.path.join(ART_DIR, a["slug"] + ".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(a, f, ensure_ascii=False, indent=1)
            os.replace(tmp, os.path.join(ART_DIR, a["slug"] + ".json"))
            return True
    return False


def import_article(req):
    """Admin: store a hand-edited article dict (must have title, standfirst, topic, vid, blocks)."""
    for k in ("title", "standfirst", "topic", "vid", "blocks"):
        if not req.get(k):
            raise ValueError(f"missing {k}")
    if req["topic"] not in TOPICS:
        raise ValueError("bad topic")
    vid = req["vid"]
    delete_article("", vid)
    dur, pub = _video_meta(vid)
    art = {"slug": _unique_slug(req["title"], vid), "url": f"https://www.youtube.com/watch?v={vid}",
           "created": time.strftime("%Y-%m-%d %H:%M:%S"), "duration": dur, "published": pub, "lead": req["standfirst"],
           "method": "manual", **{k: v for k, v in req.items() if k not in ("slug",)}}
    os.makedirs(ART_DIR, exist_ok=True)
    with open(os.path.join(ART_DIR, art["slug"] + ".json"), "w", encoding="utf-8") as f:
        json.dump(art, f, ensure_ascii=False, indent=1)
    _set_job(vid, status="done", slug=art["slug"], title=art["title"], error="")
    return art["slug"]


def handle_post(handler, path, req):
    if path.startswith("/api/vidsum/relay/") or path == "/api/vidsum/bulk":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
            return True
        try:
            if path == "/api/vidsum/relay/transcript":
                relay_transcript(req)
                handler._json({"ok": True})
            elif path == "/api/vidsum/relay/discovered":
                handler._json({"ok": True, **relay_discovered(req)})
            elif path == "/api/vidsum/relay/event":
                vid = str(req.get("vid") or "")
                stage = req.get("stage") if req.get("stage") in ("fetching", "rate_limited") else None
                if stage and re.fullmatch(r"[\w-]{11}", vid):
                    rec = _load_jobs().get(vid, {})
                    _event(vid, stage, str(req.get("detail") or ""), rec)
                handler._json({"ok": True})
            elif path == "/api/vidsum/relay/fail":
                _set_job(str(req.get("vid")), status="no_captions", error=str(req.get("reason") or "")[:200])
                handler._json({"ok": True})
            elif path == "/api/vidsum/bulk":
                res = {"added": 0, "existing": 0, "rejected": 0}
                for u in (req.get("urls") or [])[:500]:
                    code, p = submit(str(u), True, req.get("engine", "luna"), req.get("source"))
                    res["existing" if p.get("existing") else "added" if code in (200, 202) else "rejected"] += 1
                handler._json({"ok": True, **res})
            else:
                return False
        except Exception as e:
            handler._json({"ok": False, "error": str(e)[:200]}, 400)
        return True
    if path == "/api/vidsum/article/source":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            n = 0
            for a in _articles():
                sid = (req.get("map") or {}).get(a.get("vid"))
                if sid and a.get("source_id") != sid:
                    a["source_id"] = str(sid)[:80]
                    tmp = os.path.join(ART_DIR, a["slug"] + ".json.tmp")
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(a, f, ensure_ascii=False, indent=1)
                    os.replace(tmp, os.path.join(ART_DIR, a["slug"] + ".json"))
                    n += 1
            handler._json({"ok": True, "updated": n})
        return True
    if path == "/api/vidsum/article/release":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            try:
                handler._json({"ok": True, "updated": patch_release(str(req.get("vid") or ""), str(req.get("published_at") or ""))})
            except Exception as e:
                handler._json({"ok": False, "error": str(e)[:200]}, 400)
        return True
    if path == "/api/vidsum/article/import":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            try:
                handler._json({"ok": True, "slug": import_article(req)})
            except Exception as e:
                handler._json({"ok": False, "error": str(e)[:200]}, 400)
        return True
    if path == "/api/vidsum/prefs":
        user = current_user(handler)
        if not user or user.get("id") == "admin-token":
            handler._json({"ok": False, "error": "sign in with Google first"}, 401)
        else:
            handler._json({"ok": True, "prefs": set_vprefs(user["id"], req)})
        return True
    if path.startswith("/api/vidsum/sources/"):
        user = current_user(handler)
        if not user:
            handler._json({"ok": False, "error": "sign in with Google to edit sources"}, 401)
            return True
        try:
            if path == "/api/vidsum/sources/add":
                add_source(req, user)
            elif path in ("/api/vidsum/sources/remove", "/api/vidsum/sources/update"):
                with LOCK:
                    d = _load_ch()
                    hit = next((c for c in d["channels"] if c["id"] == req.get("id")), None)
                    if hit and not _can_edit_source(hit, user):
                        raise PermissionError("you can only change your own sources")
                    if path.endswith("/remove"):
                        d["channels"] = [c for c in d["channels"] if c["id"] != req.get("id")]
                    elif hit:
                        c = hit
                        if (req.get("url") or "").strip():
                            newid, _found = resolve_channel(req["url"].strip())      # raises if not a valid channel
                            if newid != c["id"] and any(x["id"] == newid for x in d["channels"]):
                                raise ValueError("this YouTube source is already in the table")
                            c["id"], c["url"] = newid, req["url"].strip()[:300]
                            c["added"] = time.strftime("%Y-%m-%d %H:%M:%S")
                            c.pop("seen", None)
                        if req.get("language") in LANGS:
                            c["language"] = req["language"]
                        if req.get("vertical") in TOPICS:
                            c["vertical"] = req["vertical"]
                        if (req.get("name") or "").strip():
                            c["name"] = req["name"].strip()[:120]
                    _save_ch(d)
            else:
                return False
            handler._json({"ok": True, "sources": sources_view(user), "hidden": sources_hidden_count(user)})
        except PermissionError as e:
            handler._json({"ok": False, "error": str(e)}, 403)
        except Exception as e:
            handler._json({"ok": False, "error": str(e)[:200]}, 400)
        return True
    if path.startswith("/api/vidsum/channels"):
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
            return True
        try:
            if path == "/api/vidsum/channels/add":
                cid, name = resolve_channel(str(req.get("channel") or ""))
                with LOCK:
                    d = _load_ch()
                    if not any(c["id"] == cid for c in d["channels"]):
                        d["channels"].append({"id": cid, "name": name, "added": time.strftime("%Y-%m-%d %H:%M:%S"),
                                              "backfill": bool(req.get("backfill"))})
                    _save_ch(d)
                handler._json({"ok": True, "id": cid, "name": name})
            elif path == "/api/vidsum/channels/remove":
                with LOCK:
                    d = _load_ch()
                    d["channels"] = [c for c in d["channels"] if c["id"] != req.get("id")]
                    _save_ch(d)
                handler._json({"ok": True})
            elif path == "/api/vidsum/channels/run":
                threading.Thread(target=watch_once, daemon=True).start()
                handler._json({"ok": True, "started": True})
            else:
                return False
        except Exception as e:
            handler._json({"ok": False, "error": str(e)[:200]}, 400)
        return True
    if path == "/api/vidsum/article/delete":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            handler._json({"ok": True, "deleted": delete_article(str(req.get("slug") or ""), req.get("vid"))})
        return True
    if path == "/api/vidsum/summarize":
        user = current_user(handler)
        is_admin = bool(user and user.get("admin"))
        code, payload = submit(str(req.get("url") or ""), is_admin, req.get("engine", "luna") if is_admin else "luna")
        handler._json(payload, code)
        return True
    return False
