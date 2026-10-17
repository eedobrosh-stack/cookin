"""Vidsum server-side: YouTube link -> Gemini (reads the URL itself, so Render's
blocked IP never touches YouTube) -> detailed RTL summary stored as an article
served at /vidsum/article/<slug>."""
import json, os, re, threading, time, html as _html, unicodedata
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
HEADNOTE = "Summarized by vidsum skill (by Mr. Brosh)"

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


def _set_job(vid, **kw):
    with LOCK:
        jobs = _load_jobs()
        if "error" in kw:
            kw["error"] = _scrub(kw["error"])
        jobs.setdefault(vid, {}).update(kw)
        jobs[vid]["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        _save_jobs(jobs)


def slugify(title):
    s = unicodedata.normalize("NFKC", title or "").lower()
    s = re.sub(r"[^\w֐-׿]+", "-", s).strip("-_")
    return s[:70].strip("-_") or "summary"


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
    out.sort(key=lambda a: a.get("created", ""), reverse=True)
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
            tr = _captions_fallback(vid)
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


def _save_article(vid, d):
    slug = _unique_slug(d["title"], vid)
    art = {"slug": slug, "vid": vid, "url": f"https://www.youtube.com/watch?v={vid}",
           "created": time.strftime("%Y-%m-%d %H:%M:%S"), **d}
    os.makedirs(ART_DIR, exist_ok=True)
    tmp = os.path.join(ART_DIR, slug + ".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(art, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(ART_DIR, slug + ".json"))
    _set_job(vid, status="done", slug=slug, title=d["title"], error="")
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
                                                     "method": "luna-captions", "finish": fin, "published": pub}))
        except Exception as e:
            log(f"vidsum {vid} luna FAILED: {str(e)[:400]}")
            _set_job(vid, status="failed", error=str(e)[:300])


def submit(url, admin, engine="luna"):
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
        if cur and cur.get("status") in ("queued", "running", "needs_transcript"):
            return 200, {"ok": True, "id": vid, "status": cur["status"]}
        active = sum(1 for j in jobs.values() if j.get("status") in ("queued", "running"))
        waiting = sum(1 for j in jobs.values() if j.get("status") == "needs_transcript")
        if active >= MAX_ACTIVE or waiting >= MAX_WAITING:
            return 429, {"ok": False, "error": "busy, try again in a few minutes"}
        if not admin:
            today = time.strftime("%Y-%m-%d")
            n = sum(1 for j in jobs.values() if j.get("public") and (j.get("submitted") or "").startswith(today))
            if n >= PUBLIC_DAILY_CAP:
                return 429, {"ok": False, "error": "daily limit reached"}
        status = "needs_transcript" if engine == "luna" else "queued"
        jobs[vid] = {"status": status, "engine": engine, "public": not admin,
                     "submitted": time.strftime("%Y-%m-%d %H:%M:%S")}
        _save_jobs(jobs)
    if engine != "luna":
        threading.Thread(target=_run, args=(vid,), daemon=True).start()
    return 202, {"ok": True, "id": vid, "status": status}


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
        json.dump({k: req.get(k) for k in ("transcript", "duration", "published", "title", "channel", "description", "source")},
                  f, ensure_ascii=False)
    _set_job(vid, status="queued", error="")
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
    out = ['<p class="kicker"><a href="/vidsum/articles">Vidsum &middot; כל הסיכומים</a></p>',
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
    body = ('<p class="kicker"><a href="/vidsum">&larr; Vidsum</a></p><h1>סיכומי וידאו</h1>'
            f'<div class="list">{items or "<p class=sub>אין עדיין סיכומים.</p>"}</div>')
    return _page("סיכומי וידאו", body)



import vidsum_render
DISCLAIMER = "הדברים המובאים הם של המרואיינים ולא נבדקו. הכתבה נערכה אוטומטית מתוך תמלול של השיחה."


def render_article(a):
    if a.get("blocks"):
        return vidsum_render.render(a, news_items(), base="", disclaimer=a.get("disclaimer") or DISCLAIMER)
    return article_html(a)


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
             "created": a.get("created"), "minutes": _length_min(a)} for a in _articles()]


# ------------------------------------------------------- channel watcher ---
CH_PATH = os.path.join(multiuser.DATA_DIR, "vidsum_channels.json")
WATCH_DAILY_CAP = 10
WATCH_EVERY_S = 3 * 3600
_UA = {"User-Agent": "Mozilla/5.0 (jarcud-vidsum)", "Accept-Language": "en"}


def _load_ch():
    try:
        with open(CH_PATH, encoding="utf-8") as f:
            d = json.load(f)
        d.setdefault("channels", [])
        d.setdefault("log", [])
        return d
    except Exception:
        return {"channels": [], "log": []}


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
            if _is_short(vid):
                seen.add(vid)
                continue
            code, payload = submit(f"https://www.youtube.com/watch?v={vid}", True)
            seen.add(vid)
            if code in (200, 202):
                used += 1
                d["log"].append({"day": today, "kind": "submit", "vid": vid, "channel": ch["name"],
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


NEWS_PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "vidsum_news.html")

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
    if path in ("/vidsum/news", "/vidsum/news/"):
        try:
            with open(NEWS_PAGE, "rb") as f:
                handler._html(f.read(), "no-store")
        except OSError:
            handler._json({"error": "news page missing"}, 404)
        return True
    if path == "/api/vidsum/news":
        handler._json({"ok": True, "topics": TOPICS, "items": news_items()})
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
    if path == "/api/vidsum/relay/queue":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            handler._json({"ok": True, "queue": relay_queue(int((qs.get("limit") or ["15"])[0]))})
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
            elif path == "/api/vidsum/relay/fail":
                _set_job(str(req.get("vid")), status="no_captions", error=str(req.get("reason") or "")[:200])
                handler._json({"ok": True})
            elif path == "/api/vidsum/bulk":
                res = {"added": 0, "existing": 0, "rejected": 0}
                for u in (req.get("urls") or [])[:500]:
                    code, p = submit(str(u), True, req.get("engine", "luna"))
                    res["existing" if p.get("existing") else "added" if code in (200, 202) else "rejected"] += 1
                handler._json({"ok": True, **res})
            else:
                return False
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
