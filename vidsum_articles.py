"""Vidsum server-side: YouTube link -> Gemini (reads the URL itself, so Render's
blocked IP never touches YouTube) -> detailed RTL summary stored as an article
served at /vidsum/article/<slug>."""
import json, os, re, threading, time, html as _html, unicodedata
import urllib.request, urllib.parse, urllib.error

import multiuser
from multiuser import secret, log, GEMINI_MODEL, BudgetExhausted, current_user

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
SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "subtitle": {"type": "STRING"},
        "sections": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "title": {"type": "STRING"},
            "bullets": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
                "text": {"type": "STRING"}, "ts": {"type": "STRING"}},
                "required": ["text", "ts"]}}},
            "required": ["title", "bullets"]}},
    },
    "required": ["title", "subtitle", "sections"],
}


def _prompt(title, channel):
    return f"""You are summarizing the attached YouTube video ("{title}", channel "{channel}").
Write a DETAILED summary in Hebrew (keep proper names / terms in their original language when natural).
Rules:
- title: a clear Hebrew article title (guest/topic specific, no clickbait). subtitle: one line (channel, speakers, length, date if known).
- Split the video into 6-14 chronological sections, each with a short descriptive Hebrew title.
- Each section holds 5-12 bullets, and overall roughly one bullet per 40-60 seconds of video (a 1-hour video should yield 70-100+ bullets). A bullet is a full, information-dense sentence or two: claims, numbers, names, examples, arguments, conclusions. No filler, no "the speaker says".
- Every bullet has "ts": the timestamp in the video where that point is made, format m:ss or h:mm:ss, accurate to within a few seconds, increasing through the video.
- Cover the whole video to the end, not only the beginning.
Return only JSON matching the schema."""


def _gemini(parts, media_low=True):
    key = secret("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")
    gc = {"temperature": 0.3, "response_mime_type": "application/json",
          "response_schema": SCHEMA, "maxOutputTokens": 32768}
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
                return _gemini(parts, media_low=False)
            if e.code in (429, 500, 503) and attempt < 2:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"gemini {e.code}: {last}")
    cand = res["candidates"][0]
    text = cand["content"]["parts"][0]["text"]
    data = json.loads(text)
    tokens = int((res.get("usageMetadata") or {}).get("totalTokenCount") or 0)
    return data, tokens, cand.get("finishReason")


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


def summarize(vid):
    url = f"https://www.youtube.com/watch?v={vid}"
    title, channel = _oembed(vid)
    prompt = _prompt(title, channel)
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
    secs = [s for s in data.get("sections", []) if s.get("bullets")]
    if not secs:
        raise RuntimeError("empty summary")
    return {"title": data["title"].strip(), "subtitle": data.get("subtitle", "").strip(), "sections": secs,
            "channel": channel, "src_title": title, "tokens": tokens, "method": method, "finish": fin}


def _run(vid):
    with WORKER:
        _set_job(vid, status="running", started=time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            d = summarize(vid)
            slug = _unique_slug(d["title"], vid)
            art = {"slug": slug, "vid": vid, "url": f"https://www.youtube.com/watch?v={vid}",
                   "created": time.strftime("%Y-%m-%d %H:%M:%S"), **d}
            os.makedirs(ART_DIR, exist_ok=True)
            tmp = os.path.join(ART_DIR, slug + ".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(art, f, ensure_ascii=False, indent=1)
            os.replace(tmp, os.path.join(ART_DIR, slug + ".json"))
            _set_job(vid, status="done", slug=slug, title=d["title"], error="")
            log(f"vidsum {vid} DONE slug={slug} tokens={d['tokens']} via {d['method']}")
        except Exception as e:
            log(f"vidsum {vid} FAILED: {str(e)[:400]}")
            _set_job(vid, status="failed", error=str(e)[:300])


def submit(url, admin):
    """-> (http_code, payload)"""
    vid = yt_id(url)
    if not vid:
        return 400, {"ok": False, "error": "not a YouTube link"}
    ex = _find_by_vid(vid)
    if ex:
        return 200, {"ok": True, "id": vid, "status": "done", "slug": ex["slug"], "existing": True}
    with LOCK:
        jobs = _load_jobs()
        cur = jobs.get(vid)
        if cur and cur.get("status") in ("queued", "running"):
            return 200, {"ok": True, "id": vid, "status": cur["status"]}
        active = sum(1 for j in jobs.values() if j.get("status") in ("queued", "running"))
        if active >= MAX_ACTIVE:
            return 429, {"ok": False, "error": "busy, try again in a few minutes"}
        if not admin:
            today = time.strftime("%Y-%m-%d")
            n = sum(1 for j in jobs.values() if j.get("public") and (j.get("submitted") or "").startswith(today))
            if n >= PUBLIC_DAILY_CAP:
                return 429, {"ok": False, "error": "daily limit reached"}
        jobs[vid] = {"status": "queued", "public": not admin, "submitted": time.strftime("%Y-%m-%d %H:%M:%S")}
        _save_jobs(jobs)
    threading.Thread(target=_run, args=(vid,), daemon=True).start()
    return 202, {"ok": True, "id": vid, "status": "queued"}


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
            handler._html(article_html(a), "no-store")
        return True
    if path == "/api/vidsum/articles":
        handler._json({"ok": True, "articles": [
            {k: a.get(k) for k in ("slug", "title", "subtitle", "vid", "channel", "created")} for a in _articles()]})
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


def handle_post(handler, path, req):
    if path == "/api/vidsum/article/delete":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            handler._json({"ok": True, "deleted": delete_article(str(req.get("slug") or ""), req.get("vid"))})
        return True
    if path == "/api/vidsum/summarize":
        user = current_user(handler)
        code, payload = submit(str(req.get("url") or ""), bool(user and user.get("admin")))
        handler._json(payload, code)
        return True
    return False
