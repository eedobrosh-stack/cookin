"""Vidsum server-side: YouTube link -> Gemini (reads the URL itself, so Render's
blocked IP never touches YouTube) -> detailed RTL summary stored as an article
served at /vidsum/article/<slug>."""
import calendar, datetime, json, math, os, re, sys, threading, uuid, time, html as _html, unicodedata
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
LUNA_WORKER = threading.Semaphore(3)     # LunaRoute (DeepSeek) writes up to 3 articles at once; Gemini stays one at a time
TOK_PATH = os.path.join(multiuser.DATA_DIR, "vidsum_tokens.jsonl")
_TOK = threading.local()
_TOK_LOCK = threading.Lock()


class tok_ctx:
    """with tok_ctx("article", vid, owner): ...  -> every LLM call inside is logged to vidsum_tokens.jsonl with this task / vid / owner."""
    def __init__(self, task, vid=None, owner=None):
        self.c = {"task": task, "vid": vid, "owner": owner}

    def __enter__(self):
        self.prev = getattr(_TOK, "c", None)
        _TOK.c = self.c

    def __exit__(self, *a):
        _TOK.c = self.prev


def _tok_log(model, tin, tout):
    c = getattr(_TOK, "c", None) or {}
    rec = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), "model": model, "in": int(tin or 0), "out": int(tout or 0),
           "task": c.get("task") or "other", "vid": c.get("vid"), "owner": c.get("owner")}
    try:
        with _TOK_LOCK, open(TOK_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass

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


RELAY_STATUS_PATH = os.path.join(multiuser.DATA_DIR, "vidsum_relay_status.json")


def relay_status_get():
    try:
        with open(RELAY_STATUS_PATH, encoding="utf-8") as f:
            st = json.load(f)
    except Exception:
        st = {}
    rss = [c.get("checked") for c in _load_ch()["channels"] if c.get("kind") == "rss" and c.get("checked")]
    if rss:
        st["rss_checked_at"] = calendar.timegm(time.strptime(max(rss), "%Y-%m-%d %H:%M:%S"))
    st["now"] = time.time()
    return st


def relay_status_set(req):
    st = relay_status_get()
    st.pop("now", None)
    st.pop("rss_checked_at", None)
    now = time.time()
    st["tick_at"] = now                                       # the Mac relay is alive
    if req.get("kind") == "discover":
        st["discover_at"] = now
        st["discover"] = {"sources": int(req.get("sources") or 0), "reachable": int(req.get("reachable") or 0), "found": int(req.get("found") or 0)}
    if req.get("kind") == "tick":
        st["waiting"] = int(req.get("waiting") or 0)
    tmp = RELAY_STATUS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f)
    os.replace(tmp, RELAY_STATUS_PATH)


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


_IDX_FILES = {}                                   # file name -> ((mtime_ns, size), slim article)
_IDX = {"sig": None, "items": []}
_IDX_LOCK = threading.Lock()
_SLIM_DROP = ("blocks", "key_points", "sections", "en")


def _slim(a):
    """An article without its body text and without the English edition's body: what the lists, lookups and the news feed need.
    A full article (blocks + 'en' blocks) is tens of KB of Python objects; 200 of them parsed on every call is what ran the 512 MB instance out of memory."""
    s = {k: v for k, v in a.items() if k not in _SLIM_DROP}
    s["_min"] = _length_min(a)
    en = a.get("en")
    if en:
        s["en"] = {"title": en.get("title", ""), "lead": en.get("lead", ""), "standfirst": en.get("standfirst", ""), "original": bool(en.get("original"))}
    return s


def _article_index():
    """Slim copies of every article, newest release first. Cached: a file is read again only when its mtime or size changed. Read-only: callers
    that rewrite an article use _articles() (the full ones)."""
    try:
        names = sorted(n for n in os.listdir(ART_DIR) if n.endswith(".json"))
    except OSError:
        return []
    sig = []
    for n in names:
        try:
            st = os.stat(os.path.join(ART_DIR, n))
            sig.append((n, st.st_mtime_ns, st.st_size))
        except OSError:
            pass
    sig = tuple(sig)
    with _IDX_LOCK:
        if _IDX["sig"] == sig:
            return _IDX["items"]
        files, items = {}, []
        for n, mt, sz in sig:
            old = _IDX_FILES.get(n)
            if old and old[0] == (mt, sz):
                files[n] = old
            else:
                try:
                    with open(os.path.join(ART_DIR, n), encoding="utf-8") as f:
                        files[n] = ((mt, sz), _slim(json.load(f)))
                except Exception:
                    continue
            items.append(files[n][1])
        items.sort(key=_rel, reverse=True)
        _IDX_FILES.clear()
        _IDX_FILES.update(files)
        _IDX["sig"], _IDX["items"] = sig, items
        return items


def _find_by_vid(vid):
    for a in _article_index():
        if a.get("vid") == vid:
            return a
    return None


def _unique_slug(title, vid):
    base = slugify(title)
    taken = {a["slug"] for a in _article_index()}
    if base not in taken:
        return base
    return f"{base}-{vid[:5].lower()}"


# ----------------------------------------------------------------- gemini ---
TOPICS = ["פוליטיקה", "טכנולוגיה", "כלכלה", "ספורט", "תרבות", "לייפסטייל", "בריאות"]
LIFESTYLE_HINT = ("לייפסטייל = ONLY advice and everyday-living subjects: relationships, psychology and wellbeing tips, parenting, food, beauty and fashion, personal growth. "
                  "A news event, incident, security, political or economic story is NEVER לייפסטייל, even when it is told as a personal testimony or a lessons-learned story")
SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "standfirst": {"type": "STRING"},
        "topic": {"type": "STRING", "enum": TOPICS},
        "topics": {"type": "ARRAY", "items": {"type": "STRING", "enum": TOPICS}},
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
- topic: the single best-fitting section from the allowed list. topics: the primary section first (same as topic) plus at most ONE secondary section, and only when the episode substantially covers it (e.g. tech business = טכנולוגיה + כלכלה). The primary section is what the episode is mostly ABOUT (a TV-history conversation is תרבות even if it mentions money).
- key_points: 4-5 short Hebrew sentences ("עיקרי הדברים").
- blocks: the article body, in order. Every block MUST carry its content in "text" (for "list" blocks put the bullets in "items" and leave "text" empty). Use type "h2" for subheadings (a new one every 2-4 paragraphs), "p" for flowing prose paragraphs, "list" (with "items") at most once for a real enumeration, and "quote" for pull quotes.
- About {words} Hebrew words in total across the "p" blocks. Third person, past/present tense news style, attribute claims ("לדבריו", "לטענתו"), keep concrete names, numbers, examples and the logic of the argument. Do not invent facts; do not editorialize.
- Every "p" block has "ts": the timestamp (m:ss or h:mm:ss) where its content is said. Cover the whole video to the end, chronologically.
- Include {quotes} "quote" blocks: the MOST PROVOCATIVE, punchy, quotable statements actually spoken, copied as close to verbatim as you can hear them, each under 25 words, with "speaker" (name + a few words of context, e.g. "אלון אולמן, על מנהיגות") and "ts". Place each quote right after the paragraph it relates to.
Return only JSON matching the schema."""


# Gemini pacing: one big video request at a time, and a gap after each one proportional to the tokens it used, so the
# per-minute token limit is not hit by back-to-back ~300k-token requests (every rejected attempt also shows up as an error in AI Studio).
GEM_TOKENS_PER_SEC = int(os.environ.get("VIDSUM_GEMINI_TPS", "5000"))     # gap seconds = last request tokens / this
GEM_MIN_GAP_S = int(os.environ.get("VIDSUM_GEMINI_MIN_GAP", "20"))
_GEM_LOCK = threading.Lock()
_GEM_NEXT_OK = 0.0


def _gem_wait():
    global _GEM_NEXT_OK
    wait = _GEM_NEXT_OK - time.time()
    if wait > 0:
        time.sleep(min(wait, 180))


def _gem_after(tokens):
    global _GEM_NEXT_OK
    _GEM_NEXT_OK = time.time() + max(GEM_MIN_GAP_S, tokens / GEM_TOKENS_PER_SEC)


def _retry_delay(body_text, attempt):
    m = re.search(r'retryDelay"?\s*:\s*"?(\d+(?:\.\d+)?)s', body_text or "")
    return min(float(m.group(1)) + 2, 120) if m else min(20 * (2 ** attempt), 120)


def _gemini(parts, media_low=True, schema=None, max_out=32768, vid=None):
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
    with _GEM_LOCK:
        for attempt in range(4):
            _gem_wait()
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=900) as r:
                    res = json.loads(r.read().decode())
                break
            except urllib.error.HTTPError as e:
                last = e.read().decode()[:700]
                if e.code == 429 and "spending cap" in last:
                    raise BudgetExhausted(last)
                if e.code == 400 and media_low and "mediaResolution" in last:
                    return _gemini(parts, media_low=False, schema=schema, max_out=max_out, vid=vid)
                if e.code in (429, 500, 503) and attempt < 3:
                    d = _retry_delay(last, attempt)
                    why = "rate limit (not the spend cap)" if e.code == 429 else f"HTTP {e.code}"
                    log(f"vidsum gemini {why}, waiting {d:.0f}s: {' '.join(last.split())[:160]}")
                    if vid:
                        _event(vid, "rate_limited", f"Gemini {why}: waiting {d:.0f}s", _load_jobs().get(vid, {}))
                    _GEM_NEXT_OK_set(time.time() + d)
                    continue
                raise RuntimeError(f"gemini {e.code}: {last}")
        cand = res["candidates"][0]
        text = cand["content"]["parts"][0]["text"]
        data = json.loads(text)
        tokens = int((res.get("usageMetadata") or {}).get("totalTokenCount") or 0)
        _um = res.get("usageMetadata") or {}
        _tok_log(GEMINI_MODEL, _um.get("promptTokenCount", 0), max(0, tokens - int(_um.get("promptTokenCount") or 0)))
        global _LAST_USAGE
        _LAST_USAGE = res.get("usageMetadata") or {}
        _gem_after(tokens)
    return data, tokens, cand.get("finishReason")


def _GEM_NEXT_OK_set(t):
    global _GEM_NEXT_OK
    _GEM_NEXT_OK = t


# ------------------------------------------------- LunaRoute (text-only, free) ---
LUNA_URL = "https://gw.lunaroute.com"
LUNA_MODEL = os.environ.get("VIDSUM_LUNA_MODEL", "deepseek-4.1-flash")
SCHEMA_HINT = """{"title": str, "standfirst": str, "topic": one of %s, "topics": [primary, optional secondary: from the same list], "lead": str, "key_points": [str],
 "blocks": [{"type": "h2"|"p"|"quote"|"list", "text": str, "ts": "m:ss or h:mm:ss", "speaker": str (quotes only), "items": [str] (list only)}]}""" % (json.dumps(TOPICS, ensure_ascii=False))
SCHEMA_HINT += "\n" + LIFESTYLE_HINT


def _clean_topics(topics, primary):
    """1-3 valid sections, primary first."""
    out = [primary] if primary in TOPICS else []
    for t in (topics if isinstance(topics, list) else []):
        if t in TOPICS and t not in out:
            out.append(t)
    return out[:2] or ["תרבות"]                       # one primary section and at most one secondary


def article_topics(a):
    return _clean_topics(a.get("topics"), a.get("topic") or "תרבות")


def _write_article(a):
    tmp = os.path.join(ART_DIR, a["slug"] + ".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(a, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(ART_DIR, a["slug"] + ".json"))


def backfill_topics(limit=12, redo=False, only=None):
    """Existing articles: ask the model (text-only) for ONE primary section (what the episode is mostly about) and at most one
    secondary. redo=True re-judges articles classified under the older rules too (marker topics_v == 3)."""
    done = 0
    for a in _articles():
        if done >= limit:
            break
        if not a.get("blocks") or (a.get("topics_v") == 4 if redo else a.get("topics")):
            continue
        if only and only not in article_topics(a):          # re-judge just the articles currently filed under one section
            continue
        txt = a["title"] + "\n" + (a.get("standfirst") or "") + "\n" + "\n".join(a.get("key_points") or []) + "\n" + \
            " ".join(b.get("text", "") for b in a["blocks"] if b.get("type") == "p")[:1200]
        prompt = ("Choose the news sections for this Hebrew podcast article. Allowed sections: " + json.dumps(TOPICS, ensure_ascii=False) + " (" + LIFESTYLE_HINT + ")"
                  + ". primary = the section the episode is mostly ABOUT (judge the subject, not the vocabulary: a conversation about a TV "
                  "show's history is תרבות even if it mentions money; stock-market analysis is כלכלה). secondary = ONE other section only if the "
                  'episode substantially covers it, otherwise null. Reply with only JSON: {"primary": "..", "secondary": ".." or null}\n\n' + txt[:3500])
        try:
            with tok_ctx("topics", a.get("vid")):
                d, _, _ = _luna(prompt, max_tokens=300)
            prim = d.get("primary") if d.get("primary") in TOPICS else (a.get("topic") or "תרבות")
            sec = d.get("secondary") if d.get("secondary") in TOPICS and d.get("secondary") != prim else None
            a["topic"], a["topics"], a["topics_v"] = prim, [prim] + ([sec] if sec else []), 4
            _write_article(a)
            log(f"vidsum topics {a['slug']} -> {a['topics']}")
            done += 1
        except Exception as e:
            log(f"vidsum topics failed {a.get('slug')}: {str(e)[:160]}")
    return done


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
        _tok_log(LUNA_MODEL, usage.get("input_tokens", 0), usage.get("output_tokens", 0))
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


def _hebrew_share(text):
    letters = [c for c in (text or "") if c.isalpha()]
    return sum(1 for c in letters if "\u0590" <= c <= "\u05ff") / len(letters) if letters else 1.0


def _text_prompt_en(title, channel, dur, transcript, retry=False):
    """The same news-article brief, written in ENGLISH straight from a non-Hebrew transcript (never translated back from Hebrew)."""
    p = _prompt(title, channel, dur, retry).replace("the attached YouTube video", "the video whose transcript is below")
    for a, b in (("into a Hebrew NEWS ARTICLE", "into an English NEWS ARTICLE"), ("Write like an Israeli news site feature", "Write like a quality English-language news feature"),
                 ("a sharp, specific Hebrew headline", "a sharp, specific English headline"),
                 ('4-5 short Hebrew sentences ("עיקרי הדברים")', "4-5 short English sentences (the key points)"), ("Hebrew words in total", "English words in total"),
                 ('("לדבריו", "לטענתו")', '("he said", "according to her", "he claimed")'), ('"אלון אולמן, על מנהיגות"', '"Alon Ullman, on leadership"'),
                 ("Return only JSON matching the schema.", "")):
        p = p.replace(a, b)
    return (p + "\nWrite everything in English (names in their original English spelling). The topic and topics values must be copied EXACTLY, in Hebrew, from the allowed section list. "
            "The transcript is automatic speech recognition and contains word errors: infer the intended words from context and fix obvious mistakes "
            "(names, numbers), never copy garbled text.\n"
            "Return ONLY one valid JSON object, no markdown. Never use the ASCII double-quote character inside a string value (use single quotes instead), so the JSON stays valid. Shape:\n" + SCHEMA_HINT
            + "\n\nTRANSCRIPT (each line starts with its timestamp in brackets):\n" + transcript)


def _oembed(vid):
    try:
        with urllib.request.urlopen("https://www.youtube.com/oembed?format=json&url=" +
                                    urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}", safe=""),
                                    timeout=20) as r:
            o = json.loads(r.read().decode())
        return o.get("title") or "", o.get("author_name") or ""
    except Exception:
        return "", ""


def _norm_title(t):
    return re.sub(r"[\W_]+", " ", (t or "").lower()).strip()


def find_duplicate(title, vid, source_id=None, channel=None, pub=None):
    """The same episode re-uploaded under a new video id (the channel replaced a video): an article for a DIFFERENT vid with the
    same original title, from the same source / channel, released within 3 days. -> that article or None."""
    nt = _norm_title(title)
    if len(nt) < 8:
        return None
    for a in _article_index():
        if a.get("vid") == vid or _norm_title(a.get("src_title")) != nt:
            continue
        if not ((source_id and a.get("source_id") == source_id) or (channel and (a.get("channel") or "").strip() == channel.strip())):
            continue
        if pub and _rel(a)[:10]:
            try:
                d1 = datetime.date.fromisoformat(str(pub)[:10])
                d2 = datetime.date.fromisoformat(_rel(a)[:10])
                if abs((d1 - d2).days) > 3:
                    continue
            except ValueError:
                pass
        return a
    return None


def _mark_duplicate(vid, art):
    """Close a job whose episode already has an article (re-upload): no more retries, the log says why."""
    _set_job(vid, status="done", slug=art["slug"], title=art.get("src_title") or art["title"], channel=art.get("channel") or "",
             detail=f"duplicate of an existing article ({art['vid']}): same episode re-uploaded", error="")


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
            data, tokens, fin = _gemini([{"file_data": {"file_uri": url}}, {"text": prompt}], vid=vid)
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
            "topics": _clean_topics(data.get("topics"), data.get("topic")),
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
    owner_id = _load_jobs().get(vid, {}).get("owner")
    if owner_id:
        d = {**d, "submitted_by": owner_id}
    art = {"slug": slug, "vid": vid, "url": f"https://www.youtube.com/watch?v={vid}",
           "created": time.strftime("%Y-%m-%d %H:%M:%S"), **d}
    os.makedirs(ART_DIR, exist_ok=True)
    tmp = os.path.join(ART_DIR, slug + ".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(art, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(ART_DIR, slug + ".json"))
    if src_id:
        with LOCK:
            dch = _load_ch()
            sc = next((x for x in dch["channels"] if x["id"] == src_id), None)
            if sc and sc.pop("vertical_auto", False):                  # a source added without a section takes the one its first article got
                sc["vertical"] = art.get("topic") if art.get("topic") in TOPICS else sc.get("vertical")
                _save_ch(dch)
    _set_job(vid, status="done", slug=slug, title=d["title"], error="",
             detail=f"{d.get('method', '')} · {d.get('tokens', 0):,} tokens", channel=d.get("channel") or "")
    log(f"vidsum {vid} DONE slug={slug} tokens={d.get('tokens')} via {d.get('method')}")


def _run(vid):
    with tok_ctx("article-gemini", vid, _job_owner(vid)):
        return _run_inner(vid)


def _run_inner(vid):
    """Gemini path: Google reads the YouTube URL itself (costs tokens)."""
    with WORKER:
        _set_job(vid, status="running", started=time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            _save_article(vid, summarize(vid))
        except Exception as e:
            log(f"vidsum {vid} FAILED: {str(e)[:400]}")
            _set_job(vid, status="failed", error=str(e)[:300])


# ------------------------------------------------ automatic Gemini fallback ---
FALLBACK_AFTER_MIN = int(os.environ.get("VIDSUM_FALLBACK_AFTER_MIN", "180"))   # captions still missing after this long
FALLBACK_DAILY_CAP = int(os.environ.get("VIDSUM_GEMINI_DAILY_CAP", "10"))     # hard daily ceiling on Gemini fallbacks


def _gemini_today():
    today = time.strftime("%Y-%m-%d")
    return sum(1 for j in _load_jobs().values() if j.get("fallback") and (j.get("fallback_at") or "").startswith(today))


def fallback_sweep():
    """LunaRoute stays the default. A video falls back to Gemini only when its captions never arrive: YouTube has blocked the
    relay for FALLBACK_AFTER_MIN minutes, or the video has no captions at all. Capped per day so spend stays bounded."""
    jobs = _load_jobs()
    now = time.time()
    cands = []
    for vid, j in jobs.items():
        if j.get("fallback") or j.get("engine", "luna") != "luna":
            continue
        st = j.get("status")
        if st == "no_captions":
            try:
                age0 = (now - calendar.timegm(time.strptime(j.get("submitted", ""), "%Y-%m-%d %H:%M:%S"))) / 60
            except ValueError:
                age0 = 0
            if int(j.get("attempts", 0)) >= 1 and age0 >= FALLBACK_AFTER_MIN:      # free path already retried and still nothing
                cands.append((j.get("updated") or "", vid, "no captions after automatic retries"))
        elif st == "needs_transcript":
            try:      # job timestamps are server time (UTC)
                age = (now - calendar.timegm(time.strptime(j.get("submitted", ""), "%Y-%m-%d %H:%M:%S"))) / 60
            except ValueError:
                continue
            if age >= FALLBACK_AFTER_MIN:
                cands.append((j.get("submitted") or "", vid, f"captions still blocked after {int(age)} min"))
    for _t, vid, why in sorted(cands):
        if _gemini_today() >= FALLBACK_DAILY_CAP:
            log(f"vidsum fallback: daily Gemini cap ({FALLBACK_DAILY_CAP}) reached, {len(cands)} waiting")
            break
        with LOCK:
            jobs = _load_jobs()
            j = jobs.get(vid) or {}
            if j.get("fallback"):
                continue
            j.update({"engine": "gemini", "status": "queued", "fallback": True, "error": "",
                      "fallback_at": time.strftime("%Y-%m-%d %H:%M:%S")})
            jobs[vid] = j
            _save_jobs(jobs)
        _event(vid, "queued", f"fallback to Gemini: {why}", j)
        threading.Thread(target=_run, args=(vid,), daemon=True).start()


RETRY_FIRST_MIN = 10          # first automatic retry 10 min after a failure, then doubling
RETRY_MAX_MIN = 360           # ...but never wait longer than 6 hours: failed videos are always being tried again


def retry_sweep():
    """Rule: a failed attempt is never final. Every failed / no-captions job goes back to the free path (LunaRoute) after a
    growing delay (20 min, 40, 80 ... up to 6 h) and keeps being retried for as long as it stays failed."""
    now = time.time()
    due = []
    for vid, j in _load_jobs().items():
        if j.get("status") not in ("failed", "no_captions"):
            continue
        try:
            failed_at = calendar.timegm(time.strptime(j.get("updated", ""), "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            continue
        delay = min(RETRY_MAX_MIN, RETRY_FIRST_MIN * (2 ** int(j.get("attempts", 0)))) * 60
        if now - failed_at >= delay:
            due.append((failed_at, vid))
    for _t, vid in sorted(due)[:40]:
        j0 = _load_jobs().get(vid) or {}
        if j0.get("status") not in ("failed", "no_captions"):
            continue
        ttl, ch_name = j0.get("title") or "", j0.get("channel") or ""
        if not ttl and j0.get("kind") != "rss":
            ttl, au = _oembed(vid)                              # a deleted video has no title: nothing to compare, retry as usual
            ch_name = ch_name or au
        dup = find_duplicate(ttl, vid, j0.get("source"), ch_name) if ttl else None
        if dup:                                                 # the channel replaced this video with a new upload of the same episode
            _mark_duplicate(vid, dup)
            continue
        with LOCK:
            jobs = _load_jobs()
            j = jobs.get(vid) or {}
            if j.get("status") not in ("failed", "no_captions"):
                continue
            n = int(j.get("attempts", 0)) + 1
            has_tr = os.path.exists(os.path.join(TR_DIR, vid + ".json"))
            j.update({"attempts": n, "engine": "luna", "error": "", "status": "queued" if has_tr else "needs_transcript"})
            jobs[vid] = j
            _save_jobs(jobs)
        nxt = min(RETRY_MAX_MIN, RETRY_FIRST_MIN * (2 ** n))
        _event(vid, "queued", f"automatic retry #{n} (if it fails again, next try in {nxt} min)", j)
        if has_tr:
            threading.Thread(target=_run_luna, args=(vid,), daemon=True).start()


def _fallback_loop():
    time.sleep(120)
    while True:
        try:
            retry_sweep()
        except Exception as e:
            log(f"vidsum retry sweep error: {str(e)[:200]}")
        try:
            fallback_sweep()
        except Exception as e:
            log(f"vidsum fallback sweep error: {str(e)[:200]}")
        time.sleep(600)


# ----------------------------------------------- transcript relay (free path) ---
TR_DIR = os.path.join(multiuser.DATA_DIR, "vidsum_transcripts")
MAX_WAITING = 800


def _job_owner(vid):
    """who a job is billed to: the user who submitted it, else the owner of its source (None = Pawed / admin)"""
    j = _load_jobs().get(vid, {})
    if j.get("owner"):
        return j["owner"]
    src = j.get("source")
    if src:
        return next((c.get("owner_id") for c in _load_ch()["channels"] if c["id"] == src), None)
    return None


def _run_luna(vid):
    with tok_ctx("article", vid, _job_owner(vid)):
        return _run_luna_inner(vid)


GEMINI_TEXT_DAILY_CAP = int(os.environ.get("VIDSUM_GEMINI_TEXT_DAILY_CAP", "30"))   # LunaRoute-outage fallbacks per day (text only, cheap)


def _provider_down(e):
    """LunaRoute itself is unavailable (5xx / rate limit after its own retries, or the connection failed): not a problem with the article"""
    return bool(re.match(r"luna (429|5\d\d)", str(e))) or isinstance(e, (urllib.error.URLError, TimeoutError, ConnectionError))


def _gemini_text_today():
    today = time.strftime("%Y-%m-%d")
    return sum(1 for j in _load_jobs().values() if (j.get("gemini_text") or "").startswith(today))


def _write_text(vid, prompt):
    """LunaRoute first; if the provider is down, Gemini writes the same article from the same transcript (capped per day).
    -> (data, tokens, finish, method_override)"""
    try:
        d, t, f = _luna(prompt)
        return d, t, f, None
    except Exception as e:
        if not _provider_down(e) or not (secret("GEMINI_API_KEY") or "").strip():
            raise
        if _gemini_text_today() >= GEMINI_TEXT_DAILY_CAP:
            log(f"vidsum {vid}: LunaRoute down but the Gemini text cap ({GEMINI_TEXT_DAILY_CAP}/day) is used up")
            raise
        log(f"vidsum {vid}: LunaRoute unavailable ({str(e)[:80]}), writing with Gemini text instead")
        _set_job(vid, gemini_text=time.strftime("%Y-%m-%d %H:%M:%S"))
        _event(vid, "fallback", "LunaRoute unavailable: Gemini writes the article", _load_jobs().get(vid, {}))
        d, t, f = _gemini([{"text": prompt}], media_low=False, vid=vid)
        return d, t, f, "gemini-text"


def _run_luna_inner(vid):
    """LunaRoute path: the Mac relay supplied captions; DeepSeek writes the article."""
    with LUNA_WORKER:
        _set_job(vid, status="running", started=time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            with open(os.path.join(TR_DIR, vid + ".json"), encoding="utf-8") as f:
                tr = json.load(f)
            dur, pub = tr.get("duration"), tr.get("published")
            title, channel = tr.get("title", ""), tr.get("channel", "")
            job = _load_jobs().get(vid, {})
            rss_extra = ({"kind": "rss", "url": job.get("page") or job.get("audio"), "audio": job.get("audio"), "image": job.get("image") or ""}
                         if job.get("kind") == "rss" else {})
            foreign = _hebrew_share((tr.get("transcript") or "")[:30000]) < 0.3        # an English (or other non-Hebrew) episode
            if foreign:
                try:                                            # write it in English first, then translate THAT to Hebrew: the English never goes through Hebrew
                    import vidsum_translate
                    edata = None
                    for retry in (False, True):
                        prompt = _text_prompt_en(title, channel, dur, tr["transcript"], retry)
                        if tr.get("description"):
                            prompt += "\n\nVIDEO DESCRIPTION (use for names and context):\n" + tr["description"][:2500]
                        edata, tokens, fin, used = _write_text(vid, prompt)
                        if _ts_ok(edata, dur):
                            break
                        log(f"vidsum {vid} luna bad timestamps (dur={dur}); {'retrying' if not retry else 'accepting'}")
                    en_art = _finalize(edata, dur, {"channel": channel, "src_title": title, "tokens": tokens,
                                                    "method": (used or ("luna-gemini-audio" if tr.get("source") == "gemini-audio" else "luna-whisper" if rss_extra else "luna-captions")) + "+en-first",
                                                    "finish": fin, "published": pub, "published_at": tr.get("published_at"), **rss_extra})
                    he = vidsum_translate.to_hebrew(en_art)
                    art = dict(en_art, **he)
                    art["en"] = {"title": en_art["title"], "standfirst": en_art["standfirst"], "lead": en_art["lead"], "key_points": en_art["key_points"],
                                 "blocks": en_art["blocks"], "original": True, "at": time.strftime("%Y-%m-%d %H:%M:%S"), "model": LUNA_MODEL}
                    _save_article(vid, art)
                    return
                except Exception as e:
                    log(f"vidsum {vid} English-first failed ({str(e)[:200]}), writing the Hebrew article directly")
            data = fin = None
            for retry in (False, True):
                prompt = _text_prompt(title, channel, dur, tr["transcript"], retry)
                if tr.get("description"):
                    prompt += "\n\nVIDEO DESCRIPTION (use for names and context):\n" + tr["description"][:2500]
                data, tokens, fin, used = _write_text(vid, prompt)
                if _ts_ok(data, dur):
                    break
                log(f"vidsum {vid} luna bad timestamps (dur={dur}); {'retrying' if not retry else 'accepting'}")
            _save_article(vid, _finalize(data, dur, {"channel": channel, "src_title": title, "tokens": tokens,
                                                     "method": used or ("luna-gemini-audio" if tr.get("source") == "gemini-audio" else "luna-whisper" if rss_extra else "luna-captions"), "finish": fin, "published": pub,
                                                     "published_at": tr.get("published_at"), **rss_extra}))
        except Exception as e:
            log(f"vidsum {vid} luna FAILED: {str(e)[:400]}")
            _set_job(vid, status="failed", error=str(e)[:300])


DEFAULT_ENGINE = "luna"      # free path first (Mac relay fetches captions, LunaRoute writes); Gemini only as a fallback


def submit(url, admin, engine=DEFAULT_ENGINE, source=None, owner=None):
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
            if owner and sum(1 for j in jobs.values() if j.get("owner") == owner and (j.get("submitted") or "").startswith(today)) >= USER_DAILY_VIDEOS:
                return 429, {"ok": False, "error": f"you can add up to {USER_DAILY_VIDEOS} episodes a day"}
        status = "needs_transcript" if engine == "luna" else "queued"
        jobs[vid] = {"status": status, "engine": engine, "public": not admin, "source": source or (cur or {}).get("source"),
                     "submitted": time.strftime("%Y-%m-%d %H:%M:%S")}
        if owner:                                   # a standalone episode someone added by hand (not from a watched source)
            jobs[vid].update(owner=owner, standalone=not jobs[vid]["source"])
        _save_jobs(jobs)
    if engine != "luna":
        threading.Thread(target=_run, args=(vid,), daemon=True).start()
    return 202, {"ok": True, "id": vid, "status": status}


def relay_discovered(req):
    """The Mac relay scanned a source's feed (YouTube answers it, not Render): apply the same rules the server watcher uses.
    Decisions are taken under the lock; submit() (which takes the same lock) is called AFTER releasing it."""
    sid = str(req.get("source_id") or "")
    today = time.strftime("%Y-%m-%d")
    out = {"submitted": 0, "skipped": 0, "deferred": 0}
    to_submit = []
    with LOCK:
        d = _load_ch()
        ch = next((c for c in d["channels"] if c["id"] == sid), None)
        if not ch:
            return out
        seen = set(ch.setdefault("seen", []))
        used = _used_today(d, today)
        owner_used = _used_today(d, today, ch.get("owner_id")) if ch.get("owner_id") else 0
        added = (ch.get("added") or "")[:19]
        # a new subscription takes the newest episode (from the last 30 days) right away instead of waiting for the next one
        latest_set = set()                                   # the newest N episodes (N = take_latest, default 3 for a new source)
        if ch.get("take_latest"):
            cut = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() - 30 * 86400))
            fresh = [i for i in req.get("items") or [] if re.fullmatch(r"[\w-]{11}", str(i.get("vid") or "")) and str(i.get("vid")) not in seen
                     and (i.get("duration") or 999) >= 150 and (i.get("published") or "").replace("T", " ").replace("Z", "")[:19] >= cut]
            fresh.sort(key=lambda i: i.get("published", ""), reverse=True)
            latest_set = {str(i["vid"]) for i in fresh[:max(1, int(ch["take_latest"]))]}
            if req.get("items"):
                ch.pop("take_latest", None)
        for it in sorted(req.get("items") or [], key=lambda i: i.get("published", "")):
            vid = str(it.get("vid") or "")
            if not re.fullmatch(r"[\w-]{11}", vid) or vid in seen:
                continue
            pub = (it.get("published") or "").replace("T", " ").replace("Z", "")[:19]
            if latest_set and vid not in latest_set and pub < added:
                seen.add(vid); out["skipped"] += 1               # older than the newest one taken when subscribing
                continue
            if (pub and pub < added and not ch.get("backfill") and vid not in latest_set) or (it.get("duration") or 999) < 150:
                seen.add(vid); out["skipped"] += 1               # older than the subscription, or a Short
                continue
            if vid not in latest_set and (used >= WATCH_DAILY_CAP or (ch.get("owner_id") and owner_used >= USER_DAILY_VIDEOS)):
                out["deferred"] += 1                              # not marked seen: picked up on a later run
                log(f"vidsum discovery: {ch['name']} -> {vid} deferred (daily cap {used}/{WATCH_DAILY_CAP})")
                continue
            if it.get("title") and find_duplicate(it["title"], vid, sid, ch.get("name"), pub):
                seen.add(vid); out["skipped"] += 1               # same episode re-uploaded under a new video id
                log(f"vidsum relay discovery: {ch['name']} -> {vid} skipped (duplicate of an existing article)")
                continue
            seen.add(vid)
            to_submit.append(vid)
            if vid not in latest_set:                              # a new source's first episodes never use up the daily cap
                used += 1
                owner_used += 1 if ch.get("owner_id") else 0
        ch["seen"] = sorted(seen)[-300:]
        ch["checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
        ch["error"] = ""
        if req.get("cadence") in ("daily", "regular"):
            ch["cadence"] = req["cadence"]
        if isinstance(req.get("pub_days"), list):
            ch["pub_days"] = sorted({int(x) for x in req["pub_days"] if str(x).isdigit() and 0 <= int(x) <= 6})
        if ch.get("backfill") and out["deferred"] == 0:
            ch.pop("backfill", None)
        _save_ch(d)
        name, owner = ch["name"], ch.get("owner_id")
    new_logs = []
    for vid in to_submit:                                         # lock is free here
        code, payload = submit(f"https://www.youtube.com/watch?v={vid}", True, "luna", sid)
        if code == 202:                                           # genuinely new (already-known videos answer 200)
            out["submitted"] += 1
            new_logs.append({"day": today, "kind": "submit", "vid": vid, "channel": name, "owner": owner, "first": vid in latest_set,
                             "at": time.strftime("%H:%M:%S")})
            log(f"vidsum relay discovery: {name} -> {vid} ({payload.get('status')})")
    if new_logs:
        with LOCK:
            d = _load_ch()
            d["log"].extend(new_logs)
            _save_ch(d)
    return out


def relay_queue(limit=15, for_mac=True):
    out = []
    fresh = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() - 24 * 3600))
    new_src = {c["id"] for c in _load_ch()["channels"] if (c.get("added") or "") >= fresh}      # sources added in the last 24 h go first
    for v, j in sorted(_load_jobs().items(), key=lambda kv: (0 if kv[1].get("source") in new_src else 1, kv[1].get("submitted", ""))):
        if j.get("status") != "needs_transcript":
            continue
        if j.get("srv_claim") and time.time() - j["srv_claim"] < 240:              # the server is fetching this one itself
            continue
        if for_mac and j.get("kind") == "rss" and not j.get("gstt_next") and (secret("GEMINI_API_KEY") or "").strip() \
                and (j.get("duration") or 0) <= SERVER_PODCAST_MAX_MIN * 60:             # a long episode is the Mac's from the start (Whisper), no head start
            try:                                                                    # a fresh podcast episode: the server's Gemini path gets 4 minutes' head start
                if time.time() - calendar.timegm(time.strptime(j.get("submitted", ""), "%Y-%m-%d %H:%M:%S")) < 240:
                    continue
            except ValueError:
                pass
        row = {"vid": v, "url": f"https://www.youtube.com/watch?v={v}", "submitted": j.get("submitted")}
        if j.get("kind") == "rss":                  # podcast episode: the Mac downloads the audio and transcribes it (Whisper)
            row.update(kind="rss", url=j.get("page") or j.get("audio"), audio=j.get("audio"), title=j.get("title"), channel=j.get("channel"),
                       duration=j.get("duration"), published_at=j.get("published_at"), description=j.get("description"),
                       language=j.get("language") or "he")
        out.append(row)
    return out[:limit]


def queue_view(limit=80):
    """What is waiting, in the order it will be handled, for the log page."""
    now = time.time()
    chs = {c["id"]: c for c in _load_ch()["channels"]}
    srv_caps = ytserver.captions_enabled()
    rank = {"running": 0, "queued": 1, "needs_transcript": 2, "no_captions": 3, "failed": 3}
    rows = []
    for vid, j in _load_jobs().items():
        st = j.get("status")
        if st not in rank:
            continue
        podcast = j.get("kind") == "rss"
        try:
            sub = calendar.timegm(time.strptime(j.get("submitted", ""), "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            sub = now
        row = {"vid": vid, "status": st, "podcast": podcast, "title": j.get("title") or "", "submitted": j.get("submitted"),
               "waiting_min": max(0, int((now - sub) / 60)), "source": (chs.get(j.get("source")) or {}).get("name") or j.get("channel") or "",
               "attempts": int(j.get("attempts", 0)), "error": (j.get("error") or "")[:100]}
        if st == "running":
            row["handler"] = "server: writing"
        elif st == "queued":
            row["handler"] = "server: writing"
        elif st == "needs_transcript":
            row["handler"] = "Mac: Whisper" if podcast else ("server: caption service" if srv_caps else "Mac: captions")
        else:
            try:
                failed_at = calendar.timegm(time.strptime(j.get("updated", ""), "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                failed_at = now
            delay = min(RETRY_MAX_MIN, RETRY_FIRST_MIN * (2 ** row["attempts"])) * 60
            row["retry_in_min"] = max(0, int((failed_at + delay - now) / 60) + 1)
            row["handler"] = "automatic retry"
        row["_k"] = (rank[st], 0 if (chs.get(j.get("source")) or {}).get("added", "") >= time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(now - 86400)) else 1,
                     j.get("submitted", ""))
        rows.append(row)
    rows.sort(key=lambda r: r["_k"])
    for i, r in enumerate(rows, 1):
        r["pos"] = i
        r.pop("_k", None)
    return rows[:limit], len(rows)


def relay_transcript(req):
    vid = str(req.get("vid") or "")
    if not re.fullmatch(r"[\w-]{11}", vid) or len(req.get("transcript") or "") < 200:
        raise ValueError("bad vid or transcript too short")
    dup = find_duplicate(req.get("title") or "", vid, _load_jobs().get(vid, {}).get("source"), req.get("channel"),
                         req.get("published_at") or req.get("published"))
    if dup:
        _mark_duplicate(vid, dup)
        return
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
    arts = _article_index()
    items = "".join(
        f'<a class="item" href="/vidsum/article/{urllib.parse.quote(a["slug"])}">{e(a["title"])}'
        f'<small>{e(a.get("channel", ""))} &middot; {e(a["created"][:10])}</small></a>' for a in arts)
    body = ('<p class="kicker"><a href="/vidsum">&larr; Pawed</a></p><h1>סיכומי וידאו</h1>'
            f'<div class="list">{items or "<p class=sub>אין עדיין סיכומים.</p>"}</div>')
    return _page("סיכומי וידאו", body)



import vidsum_render
import vidsum_feeds
DISCLAIMER = "הדברים המובאים הם של המרואיינים ולא נבדקו. הכתבה נערכה אוטומטית מתוך תמלול של השיחה."


def render_article(a, lang="he"):
    if a.get("blocks"):
        return vidsum_render.render(a, news_items(), base="", disclaimer=a.get("disclaimer") or DISCLAIMER, lang=lang)
    return article_html(a)



# ------------------------------------------------ generated cover art (no usable YouTube thumbnail) ---
_COVER_ACC = {"כלכלה": "#e0a43a", "פוליטיקה": "#6fbf5a", "טכנולוגיה": "#ff6b4a", "ספורט": "#ff9a3c",
              "תרבות": "#b07be0", "לייפסטייל": "#f07ab0", "בריאות": "#3fcfb4"}
_KEYS = [("chip", r"\bAI\b|בינה מלאכותית|GPT|סוכן|סוכנים|אלגוריתם|סייבר|הייטק|רובוט|OpenAI|אנטרופיק|צ'אט"),
         ("chart", r"מניות|בורסה|S&P|נאסד|שוק ההון|השקעות|מסחר|וול סטריט|כלכל|ריבית|אינפלציה|מטבע|קריפטו|דולר"),
         ("ball", r"כדורגל|ליגה|שחקן|קבוצ|מונדיאל|יורו|מאמן|כדורסל|ספורט|משחק"),
         ("columns", r"בחירות|ממשלה|כנסת|נתניהו|פוליטי|קואליציה|ראש הממשלה|שר |סקר|מפלגה"),
         ("heart", r"בריאות|רפוא|מחל|סוכר|תזונה|מוח|דיאטה|שינה|רופא|טיפול"),
         ("mic", r"פודקאסט|ראיון|תרבות|מוזיק|סרט|טלוויזיה|סלבס|לייפסטייל|אופנה|קומדי|סאטיר")]
_TOPIC_MOTIF = {"טכנולוגיה": "chip", "כלכלה": "chart", "ספורט": "ball", "פוליטיקה": "columns", "בריאות": "heart",
                "תרבות": "mic", "לייפסטייל": "mic"}


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


def cover_svg(a, lang="he"):
    motif = _motif_name(a)                          # chosen from the Hebrew topic, before the label is translated
    if lang == "en":
        a = dict(a, topic=vidsum_render.EN_TOPICS.get(a.get("topic"), a.get("topic", "")), _acc_topic=a.get("topic"))
    acc = _COVER_ACC.get(a.get("_acc_topic") or a.get("topic"), "#e0a43a")
    seed = sum(ord(c) for c in a.get("vid", "x"))
    dots = "".join(f'<circle cx="{(seed * (i + 3) * 37) % 1280}" cy="{(seed * (i + 5) * 53) % 720}" r="{3 + (seed * (i + 1)) % 5}" fill="#fff" opacity=".14"/>' for i in range(26))
    e = _html.escape
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" preserveAspectRatio="xMidYMid slice">'
            f'<defs><radialGradient id="g" cx="50%" cy="46%" r="75%"><stop offset="0" stop-color="{acc}" stop-opacity=".55"/><stop offset=".62" stop-color="#1b1722"/><stop offset="1" stop-color="#0e0c12"/></radialGradient></defs>'
            f'<rect width="1280" height="720" fill="url(#g)"/>{dots}{_motif_svg(motif, acc)}'
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


def _norm_key(s):
    return re.sub(r"[^\w]", "", s or "").lower()


def _source_resolver(chs):
    """article -> source id for articles written before source tracking: (1) the channel's seen-video list, (2) channel name or
    @handle equal to / contained in the article's channel name."""
    vid_src, names = {}, []
    for c in chs:
        for x in (c.get("seen") or []):
            vid_src.setdefault(str(x), c["id"])
        keys = {_norm_key(c.get("name"))}
        m = re.search(r"youtube\.com/@([^/?#]+)", c.get("url") or "")
        if m:
            keys.add(_norm_key(m.group(1)))
        names.append((c["id"], [k for k in keys if len(k) >= 3]))

    def resolve(a):
        if a.get("source_id"):
            return a["source_id"]
        if a.get("vid") and str(a["vid"]) in vid_src:
            return vid_src[str(a["vid"])]
        ch = _norm_key(a.get("channel"))
        if len(ch) >= 3:
            for cid, keys in names:
                if any(k == ch or (min(len(k), len(ch)) >= 5 and (k in ch or ch in k)) for k in keys):
                    return cid
        return None
    return resolve


def news_items():
    nd = vidsum_render.nodash
    chs = _load_ch()["channels"]
    daily_ids = {c["id"] for c in chs if c.get("cadence") == "daily"}     # daily pods own the morning slots
    nohead_ids = {c["id"] for c in chs if c.get("no_headline")}           # good but spammy sources: never a headline
    resolve = _source_resolver(chs)
    out = []
    for a in _article_index():
        sid = resolve(a)
        out.append({"slug": a["slug"], "title": nd(a["title"]), "lead": nd(a.get("lead") or a.get("standfirst") or a.get("subtitle", "")),
                    "title_en": nd(((a.get("en") or {}).get("title")) or ""), "lead_en": nd(((a.get("en") or {}).get("lead") or (a.get("en") or {}).get("standfirst")) or ""),
                    "topic": a.get("topic") or "תרבות", "topics": article_topics(a), "channel": a.get("channel", ""), "vid": a.get("vid"),
                    "source_id": sid, "image": a.get("image") or "", "kind": a.get("kind") or "yt", "daily": sid in daily_ids, "nohead": sid in nohead_ids,
                    "submitted_by": a.get("submitted_by"), "created": a.get("created"), "released": _rel(a),
                    "released_time": len((a.get("published_at") or "")) >= 19, "minutes": a["_min"] if "_min" in a else _length_min(a)})
    return out



def removed_topics(viewer):
    """Sections a signed-in user has switched off: every Pawed-roster source of that section is off and none of their own sources
    in that section is on. Picking even one source (roster or their own) in a section brings the section back."""
    if not viewer or viewer.get("id") == "admin-token" or viewer.get("admin"):
        return set()
    p = get_vprefs(viewer["id"])
    base, own_on = {}, set()
    for c in _load_ch()["channels"]:
        v = c.get("vertical")
        if c.get("owner_id") is None:
            base.setdefault(v, []).append(c["id"])
        elif c.get("owner_id") == viewer["id"] and c["id"] not in p["hiddenBase"]:
            own_on.add(v)
    return {v for v, ids in base.items() if v in TOPICS and v not in own_on and all(p["hideBase"] or i in p["hiddenBase"] for i in ids)}


# ------------------------------------------------- users: prefs + visibility ---
MAX_USER_SOURCES = 10
USER_DAILY_VIDEOS = 8


def _vdb():
    c = multiuser.db()
    c.execute("CREATE TABLE IF NOT EXISTS vidsum_prefs(user_id TEXT PRIMARY KEY, hide_base INTEGER DEFAULT 0, "
              "hide_name INTEGER DEFAULT 0, muted TEXT DEFAULT '[]')")
    for ddl in ("ALTER TABLE vidsum_prefs ADD COLUMN hidden_base TEXT DEFAULT '[]'", "ALTER TABLE vidsum_prefs ADD COLUMN lang TEXT DEFAULT ''"):
        try:
            c.execute(ddl)
        except Exception:
            pass                                  # column already there
    return c


def get_vprefs(uid):
    with _vdb() as c:
        r = c.execute("SELECT * FROM vidsum_prefs WHERE user_id=?", (uid,)).fetchone()
    if not r:
        return {"hideBase": False, "hideName": False, "muted": [], "hiddenBase": [], "lang": ""}
    try:
        muted = json.loads(r["muted"] or "[]")
    except ValueError:
        muted = []
    try:
        hidden_base = json.loads(r["hidden_base"] or "[]")
    except (ValueError, IndexError, KeyError):
        hidden_base = []
    try:
        lang = r["lang"] or ""
    except (IndexError, KeyError):
        lang = ""
    return {"hideBase": bool(r["hide_base"]), "hideName": bool(r["hide_name"]), "muted": muted, "hiddenBase": hidden_base, "lang": lang}


def set_vprefs(uid, req):
    p = get_vprefs(uid)
    if "hideBase" in req:
        p["hideBase"] = bool(req["hideBase"])
    if "hideName" in req:
        p["hideName"] = bool(req["hideName"])
    if isinstance(req.get("muted"), list):
        p["muted"] = [str(x)[:40] for x in req["muted"]][:200]
    if isinstance(req.get("hiddenBase"), list):
        p["hiddenBase"] = [str(x)[:80] for x in req["hiddenBase"]][:300]
    if req.get("lang") in ("he", "en"):
        p["lang"] = req["lang"]
    with _vdb() as c:
        c.execute("INSERT INTO vidsum_prefs(user_id,hide_base,hide_name,muted,hidden_base,lang) VALUES(?,?,?,?,?,?) "
                  "ON CONFLICT(user_id) DO UPDATE SET hide_base=excluded.hide_base, hide_name=excluded.hide_name, muted=excluded.muted, "
                  "hidden_base=excluded.hidden_base, lang=excluded.lang",
                  (uid, int(p["hideBase"]), int(p["hideName"]), json.dumps(p["muted"]), json.dumps(p["hiddenBase"]), p.get("lang") or ""))
    return p


def request_lang(handler, qs=None):
    """Language of this request: ?lang= first, then the signed-in user's saved choice, then the pawed_lang cookie, else Hebrew."""
    q = ((qs or {}).get("lang") or [""])[0]
    if q in ("he", "en"):
        return q
    try:
        u = current_user(handler)
        if u and u.get("id") != "admin-token":
            l = get_vprefs(u["id"]).get("lang")
            if l in ("he", "en"):
                return l
    except Exception:
        pass
    m = re.search(r"(?:^|;\s*)pawed_lang=(he|en)\b", handler.headers.get("Cookie") or "")
    return m.group(1) if m else "he"


def _hidden_names():
    with _vdb() as c:
        return {r["user_id"] for r in c.execute("SELECT user_id FROM vidsum_prefs WHERE hide_name=1")}


def _viewer(handler):
    u = current_user(handler)
    if not u or u.get("id") == "admin-token":
        return u
    return u


def _visible_source_ids(viewer):
    """Source ids a viewer sees (None = no filtering, admins only). A user's own sources are private to them; the Pawed roster
    (owner None) is shown to everyone unless the signed-in viewer hid it whole or per source."""
    if viewer and (viewer.get("id") == "admin-token" or viewer.get("admin")):
        return None
    p = get_vprefs(viewer["id"]) if viewer else {"hideBase": False, "hiddenBase": [], "muted": []}
    out = set()
    for c in _load_ch()["channels"]:
        owner = c.get("owner_id")
        if viewer and owner == viewer["id"]:
            if c["id"] not in p["hiddenBase"]:             # a user can switch one of their own sources off without deleting it
                out.add(c["id"])
        elif owner is None and not p["hideBase"] and c["id"] not in p["hiddenBase"]:
            out.add(c["id"])
    return out


def _can_edit_source(c, user):
    return bool(user and (user.get("admin") or (c.get("owner_id") and c.get("owner_id") == user.get("id"))))


# ------------------------------------------------------- channel watcher ---
CH_PATH = os.path.join(multiuser.DATA_DIR, "vidsum_channels.json")
WATCH_DAILY_CAP = 120
SERVER_PODCAST_MAX_MIN = int(os.environ.get("VIDSUM_PODCAST_MAX_MIN", "40"))   # podcast episodes longer than this are transcribed by the Mac (Whisper), not Gemini audio


def _used_today(d, today, owner=None):
    """Distinct episodes the watchers submitted today (not log lines: a repeated line must not eat the daily cap)."""
    return len({e.get("vid") for e in d["log"] if e.get("day") == today and e.get("kind") == "submit" and not e.get("first")
                and (owner is None or e.get("owner") == owner)})
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


def _is_youtube_ref(ref):
    ref = (ref or "").strip()
    if not ref.startswith("http"):
        return ref.startswith("@") or bool(re.match(r"UC[\w-]{22}$", ref))
    host = (urllib.parse.urlparse(ref).hostname or "").lower()
    return host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")


def resolve_channel(ref):
    """channel URL / @handle / UC… id / playlist URL (list=PL…) -> (feed_id, name)"""
    ref = ref.strip()
    if ref.startswith("http"):
        host = (urllib.parse.urlparse(ref).hostname or "").lower()
        if not (host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")):
            raise ValueError("only YouTube channel or playlist links are allowed")
    pl = re.search(r"[?&]list=([\w-]+)", ref) or re.search(r"youtube\.com/show/VL(PL[\w-]+)", ref)    # a /show/ page is a playlist: VL + its id
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
        try:
            html = _http(ref.split("?")[0])
        except urllib.error.HTTPError as e:
            raise ValueError(f"YouTube could not open this link (HTTP {e.code}). Use a channel link (youtube.com/@name) or a playlist link (youtube.com/playlist?list=...)")
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
    used = _used_today(d, today)
    for ch in d["channels"]:
        if ch["id"].startswith("pending-") or ch.get("kind") == "rss":     # name only (not valid yet) / podcast feeds have their own loop
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
                owner_used = _used_today(d, today, ch["owner_id"])
                if owner_used >= USER_DAILY_VIDEOS:
                    continue
            if _is_short(vid):
                seen.add(vid)
                continue
            tm = re.search(r"<title>([^<]*)</title>", ent)
            if tm and find_duplicate(_html.unescape(tm.group(1)), vid, ch["id"], ch.get("name"), pub):
                seen.add(vid)                                # same episode re-uploaded: already has an article
                log(f"vidsum watcher: {ch['name']} -> {vid} skipped (duplicate of an existing article)")
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


RSS_EVERY_S = 20 * 60


def _submit_rss(ch, it):
    """Queue one podcast episode for the Mac relay (download audio + Whisper). -> True if queued."""
    vid = vidsum_feeds.episode_id(it)
    if _find_by_vid(vid):
        return True
    with LOCK:
        jobs = _load_jobs()
        cur = jobs.get(vid)
        if cur and cur.get("status") in ("queued", "running", "needs_transcript"):
            return True
        if sum(1 for j in jobs.values() if j.get("status") == "needs_transcript") >= MAX_WAITING:
            return False
        jobs[vid] = {"status": "needs_transcript", "engine": "luna", "public": False, "source": ch["id"], "kind": "rss",
                     "audio": it["audio"], "title": it["title"], "channel": ch["name"], "duration": it["duration"],
                     "published_at": it["published_at"], "page": it["link"], "image": it["image"],
                     "description": it["description"], "language": ch.get("language") or "he",
                     "submitted": time.strftime("%Y-%m-%d %H:%M:%S")}
        _save_jobs(jobs)
    return True


def watch_rss():
    """Podcast-feed sources: queue episodes published after the source was added (the newest one right away on a new source)."""
    d = _load_ch()
    today = time.strftime("%Y-%m-%d")
    used = _used_today(d, today)
    for ch in d["channels"]:
        if ch.get("kind") != "rss":
            continue
        try:
            feed = vidsum_feeds.parse_feed(vidsum_feeds.fetch(ch["feed_url"]))
        except Exception as e:
            ch["error"] = str(e)[:120]
            continue
        ch["error"] = ""
        ch["checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
        seen = set(ch.setdefault("seen", []))
        items = feed["items"]
        n_latest = int(ch.pop("take_latest", 0) or 0)
        if n_latest and items:                               # new subscription: the latest N episodes (if recent), nothing older
            fresh = [i for i in items if i["published_at"] and i["published_at"] >= time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 30 * 86400))]
            first = fresh[:n_latest]
            for i in items:
                if not any(i is f for f in first):
                    seen.add(vidsum_feeds.episode_id(i))
        else:
            first = []
        for it in reversed(items) if not first else first:   # oldest first
            eid = vidsum_feeds.episode_id(it)
            if eid in seen and not first:
                continue
            if not first:
                pub = (it["published_at"] or "").replace("T", " ").replace("Z", "")
                if (pub and pub < ch["added"][:19] and not ch.get("backfill")) or (it["duration"] or 999) < 150:
                    seen.add(eid)
                    continue
            is_first = bool(first)                                   # a new source's first episode never uses up the daily caps
            if not is_first and used >= WATCH_DAILY_CAP:
                break
            if not is_first and ch.get("owner_id") and _used_today(d, today, ch["owner_id"]) >= USER_DAILY_VIDEOS:
                continue
            if _submit_rss(ch, it):
                seen.add(eid)
                if not is_first:
                    used += 1
                if not any(e.get("vid") == eid and e.get("day") == today for e in d["log"]):
                    d["log"].append({"day": today, "kind": "submit", "vid": eid, "channel": ch["name"], "owner": ch.get("owner_id"), "first": is_first,
                                     "at": time.strftime("%H:%M:%S")})
                    log(f"vidsum rss: {ch['name']} -> {it['title'][:60]} ({eid})")
        ch["seen"] = sorted(seen)[-400:]
    _save_ch(d)


def _rss_loop():
    time.sleep(120)
    while True:
        try:
            watch_rss()
        except Exception as e:
            log(f"vidsum rss watcher error: {str(e)[:200]}")
        time.sleep(RSS_EVERY_S)


def _watch_loop():
    time.sleep(90)
    while True:
        try:
            watch_once()
        except Exception as e:
            log(f"vidsum watcher error: {str(e)[:200]}")
        time.sleep(WATCH_EVERY_S)



# ------------------------------------------- server-side YouTube (optional: YOUTUBE_API_KEY + SUPADATA_API_KEY) ---
import ytserver


def yt_api_watch():
    """Discovery without the Mac: list each YouTube source's latest videos via the Data API and apply the same rules as the relay."""
    if not ytserver.api_enabled():
        return
    n, tot = 0, {"submitted": 0, "skipped": 0, "deferred": 0}
    for ch in _load_ch()["channels"]:
        if ch.get("kind") == "rss" or ch["id"].startswith("pending-") or not re.fullmatch(r"(UC|PL|UU|OL|FL)[\w-]{10,}", ch["id"]):
            continue
        try:
            items = ytserver.list_videos(ch["id"], 10)
        except Exception as e:
            log(f"vidsum yt-api list failed for {ch['name']}: {str(e)[:120]}")
            continue
        if items:
            r = relay_discovered({"source_id": ch["id"], "items": items})
            for k in tot:
                tot[k] += r.get(k, 0)
        n += 1
    log(f"vidsum yt-api pass: {n} sources, submitted {tot['submitted']}, skipped {tot['skipped']}, deferred {tot['deferred']}")


def discover_now(source_id):
    """A source was just added: list its latest videos right away (Data API) instead of waiting for the next 10-minute pass."""
    def work():
        try:
            if ytserver.api_enabled():
                items = ytserver.list_videos(source_id, 10)
                if items:
                    relay_discovered({"source_id": source_id, "items": items})
                    for _ in range(12):                                     # a minute or two of quick passes for the rate-limited stragglers
                        if not server_captions_once():
                            break
                        time.sleep(10)
        except Exception as e:
            log(f"vidsum discover_now {source_id}: {str(e)[:160]}")
    threading.Thread(target=work, daemon=True).start()


def server_captions_once(limit=6):
    """Fetch captions for waiting YouTube jobs through the caption service (up to 3 at a time); anything it cannot do stays for the Mac."""
    if not ytserver.captions_enabled():
        return 0
    todo = []
    with LOCK:
        jobs = _load_jobs()
        for v, j in sorted(jobs.items(), key=lambda kv: kv[1].get("submitted", "")):
            if j.get("status") == "needs_transcript" and j.get("kind") != "rss" and not re.fullmatch(r"r[0-9a-f]{10}", v) and time.time() >= j.get("srv_next", 0) \
                    and not (j.get("srv_claim") and time.time() - j["srv_claim"] < 240):
                j["srv_claim"] = time.time()
                todo.append(v)
                if len(todo) >= limit:
                    break
        _save_jobs(jobs)

    def one(vid):
        try:
            _event(vid, "fetching", "caption service", _load_jobs().get(vid, {}))
            c = ytserver.captions(vid)
            relay_transcript({"vid": vid, **c})
        except ytserver.NoCaptions as e:
            if str(e) == "video not found or private":          # gone from YouTube (deleted / private): retrying can never work
                _set_job(vid, status="unavailable", error=str(e)[:200], srv_claim=0)
                log(f"vidsum {vid} unavailable on YouTube, no more retries")
            else:
                _set_job(vid, status="no_captions", error=str(e)[:200], srv_claim=0)
        except ytserver.RateLimited as e:                                   # the service allows only a few requests per second: try again shortly
            _set_job(vid, srv_claim=0, srv_next=time.time() + e.after)
        except RuntimeError as e:
            if str(e).startswith("too short"):
                _set_job(vid, status="no_captions", error=str(e)[:200], srv_claim=0)
            else:
                log(f"vidsum server captions {vid}: {str(e)[:160]}")
                _set_job(vid, srv_claim=0, srv_next=time.time() + 300)       # leave it to the Mac meanwhile
        except Exception as e:
            log(f"vidsum server captions {vid} error: {str(e)[:160]}")
            _set_job(vid, srv_claim=0, srv_next=time.time() + 300)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(one, todo))
    return len(todo)


def _yt_api_loop():
    time.sleep(150)
    while True:
        try:
            yt_api_watch()
        except Exception as e:
            log(f"vidsum yt-api watcher error: {str(e)[:200]}")
        time.sleep(10 * 60)


def _server_captions_loop():
    time.sleep(60)
    while True:
        try:
            busy = server_captions_once()
        except Exception as e:
            busy = 0
            log(f"vidsum server captions loop error: {str(e)[:200]}")
        time.sleep(10 if busy else 30)


def start_background():
    resume_stuck()
    threading.Thread(target=backfill, daemon=True).start()
    threading.Thread(target=_watch_loop, daemon=True).start()
    threading.Thread(target=_rss_loop, daemon=True).start()
    threading.Thread(target=_fallback_loop, daemon=True).start()
    threading.Thread(target=_yt_api_loop, daemon=True).start()
    threading.Thread(target=_server_captions_loop, daemon=True).start()
    import podstt
    threading.Thread(target=podstt.loop, daemon=True).start()
    import vidsum_translate
    vidsum_translate.start()


_ERR_RX = re.compile(r"fail|error|exception|traceback|quota|unavailable|memory|\b(?:4\d\d|5\d\d)\b|reset by peer|timed? ?out|stopped early|malformed|repeats", re.I)
_BOOT = time.time()


def _norm_msg(line):
    """one error 'kind' per distinct message: ids, numbers and slugs removed so the same problem groups together"""
    m = re.sub(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d ", "", line.strip())
    m = re.sub(r"\b(?:r[0-9a-f]{10}|[\w-]{11})\b(?= (?:DONE|FAILED|video|failed|unavailable|luna|gemini|error|server))", "<id>", m)
    m = re.sub(r"slug=\S+", "slug=<s>", m)
    m = re.sub(r"vidsum translate \S+ ", "vidsum translate <slug> ", m)
    m = re.sub(r"\d+(?:[.,]\d+)?", "N", m)
    return m[:200]


def _tail_lines(path, max_bytes=1_500_000):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - max_bytes))
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return []
    return data.splitlines()[1 if size > max_bytes else 0:]


def health_report(qs=None):
    """Admin: what the server knows about its own health, for the QA agent: memory, uptime, loops, disk, and the error lines of the
    persistent log grouped by kind (the log survives restarts and out-of-memory kills, unlike the dashboard's live tail)."""
    import shutil
    qs = qs or {}
    rss = peak = None
    try:
        with open("/proc/self/status") as f:
            st = dict(l.split(":", 1) for l in f.read().splitlines() if ":" in l)
        rss = int(st["VmRSS"].split()[0]) // 1024
        peak = int(st["VmHWM"].split()[0]) // 1024
    except Exception:
        try:
            import resource
            peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024 if sys.platform == "darwin" else 1024))
        except Exception:
            pass
    du = shutil.disk_usage(multiuser.DATA_DIR)
    hours = float((qs.get("hours") or ["24"])[0])
    since = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - hours * 3600))
    ts_rx = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d ")
    lines, cur, in_tb = [], "", False                  # lines with a timestamp; a Python traceback block becomes ONE line "<time> traceback: <exception line>"
    for l in _tail_lines(multiuser.LOG_PATH + ".1", 600_000) + _tail_lines(multiuser.LOG_PATH):
        if ts_rx.match(l):
            cur, in_tb = l[:19], False
            if cur >= since:
                lines.append(l)
        elif l.startswith("Traceback"):
            in_tb = True
        elif in_tb and l and not l[0].isspace():        # the exception line that ends the block
            in_tb = False
            if cur >= since:
                lines.append(f"{cur} traceback: {l}")
    groups = {}
    for l in lines:
        if _ERR_RX.search(l):
            k = _norm_msg(l)
            g = groups.setdefault(k, {"kind": k, "count": 0, "first": l[:19], "last": l[:19], "example": l[:400]})
            g["count"] += 1
            g["last"] = l[:19]
    last = lambda needle: next((l[:19] for l in reversed(lines) if needle in l), None)
    jobs = {}
    for j in _load_jobs().values():
        jobs[j.get("status", "?")] = jobs.get(j.get("status", "?"), 0) + 1
    raw_q = (qs.get("q") or [""])[0]
    raw = [l for l in lines if re.search(raw_q, l, re.I)][-int((qs.get("limit") or ["40"])[0]):] if raw_q else []
    import vidsum_translate, pawed_alerts
    rep = {"ok": True, "now": time.strftime("%Y-%m-%d %H:%M:%S"), "uptime_min": int((time.time() - _BOOT) / 60), "rss_mb": rss, "peak_mb": peak,
            "disk_free_mb": du.free // 1048576, "disk_used_mb": du.used // 1048576, "log_mb": round(os.path.getsize(multiuser.LOG_PATH) / 1048576, 1) if os.path.exists(multiuser.LOG_PATH) else 0,
            "threads": sorted({t.name for t in threading.enumerate()})[:30], "thread_count": threading.active_count(),
            "last": {"yt_pass": last("vidsum yt-api pass"), "rss_found": last("vidsum rss:"), "translate": last("vidsum translate"), "done": last(" DONE "),
                     "quota": last("caption service QUOTA")},
            "jobs": jobs, "translate_pending": vidsum_translate.pending(), "hours": hours, "log_lines": len(lines),
            "errors": sorted(groups.values(), key=lambda g: -g["count"])[:60], "raw": raw}
    for g in rep["errors"]:
        g["class"] = pawed_alerts.classify(g["example"])
    rep["alerts"] = pawed_alerts.system_alerts({**rep, "relay": relay_status_get()}) + [
        {"severity": g["class"]["severity"], "id": g["class"]["id"], "title": g["kind"], "count": g["count"], "last": g["last"], "first": g["first"],
         "meaning": g["class"]["meaning"], "next": g["class"]["next"], "who": g["class"]["who"], "example": g["example"], "source": "log"} for g in rep["errors"]]
    order = {"crit": 0, "warn": 1, "info": 2}
    rep["alerts"].sort(key=lambda a: (order[a["severity"]], -a["count"]))
    return rep


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
    real_names = {_norm_key(c["name"]) for c in _load_ch()["channels"] if not c["id"].startswith("pending-")}
    vis = _visible_source_ids(viewer)
    out = []
    for c in _load_ch()["channels"]:
        owner = c.get("owner_id")
        mine_c = bool(viewer and owner and owner == viewer.get("id"))
        if c["id"].startswith("pending-") and not (viewer and viewer.get("admin")) and _norm_key(c["name"]) in real_names:
            continue                                                   # a name-only placeholder next to the real source of the same name
        if vis is not None and owner is not None and not mine_c:      # other users' sources are private; the whole Pawed roster is always listed
            continue                                                   # (hidden ones too, so the viewer can switch them back on)
        label = "Pawed" if owner is None else ("אנונימי" if owner in hidden else (c.get("owner_name") or "משתמש"))
        out.append({"id": c["id"], "name": c["name"], "language": c["language"], "url": c["url"],
                    "vertical": c["vertical"], "added": c.get("added", ""), "pending": c["id"].startswith("pending-"),
                    "daily": c.get("cadence") == "daily", "pub_days": c.get("pub_days") or [], "owner_id": owner, "owner_label": label, "mine": bool(viewer and owner and owner == viewer.get("id")),
                    "base": owner is None, "kind": c.get("kind") or "yt", "no_headline": bool(c.get("no_headline")), "can_edit": _can_edit_source(c, viewer)})
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
    v_auto = req.get("vertical") not in TOPICS            # no section chosen: it follows the first article's section once one is written
    admin = bool(user and user.get("admin"))
    owner_id = None if admin else user["id"]
    owner_name = None if admin else (user.get("name") or (user.get("email") or "").split("@")[0] or "משתמש")
    if not admin:
        mine = sum(1 for c in _load_ch()["channels"] if c.get("owner_id") == owner_id)
        if mine >= MAX_USER_SOURCES:
            raise ValueError(f"you can have up to {MAX_USER_SOURCES} sources")
    if not url and name and len(name) >= 3:        # pod name only: look the show up on Apple Podcasts first
        try:
            url = vidsum_feeds.itunes_find(name) or ""
        except Exception:
            url = ""
    if not url:                                   # pod name only: stays inactive until a YouTube URL is attached
        if not name:
            raise ValueError("enter a podcast name, or a YouTube URL")
        with LOCK:
            d = _load_ch()
            if any(c["name"].strip() == name and c.get("owner_id") == owner_id for c in d["channels"]):
                raise ValueError("this podcast is already in the table")
            cid = "pending-" + uuid.uuid4().hex[:8]
            d["channels"].append({"id": cid, "name": name[:120], "url": "", "language": lang, "vertical": vert, "vertical_auto": v_auto,
                                  "added": time.strftime("%Y-%m-%d %H:%M:%S"), "owner_id": owner_id, "owner_name": owner_name})
            _save_ch(d)
        return cid
    if not _is_youtube_ref(url):                    # a podcast page, an RSS feed or a show name: read it as a podcast feed
        info = vidsum_feeds.resolve_feed(url, name)
        cid = info["id"]
        with LOCK:
            d = _load_ch()
            if any(c["id"] == cid for c in d["channels"]):
                raise ValueError("this source is already in the table")
            d["channels"].append({"id": cid, "kind": "rss", "feed_url": info["feed_url"], "image": info["image"],
                                  "name": (name or info["name"])[:120], "url": url[:300], "language": req.get("language") if req.get("language") in LANGS else info["language"],
                                  "vertical": vert, "vertical_auto": v_auto, "added": time.strftime("%Y-%m-%d %H:%M:%S"), "take_latest": 1,   # podcasts: 1 until transcription is server-side (Whisper on the Mac is serial)
                                  "owner_id": owner_id, "owner_name": owner_name})
            _save_ch(d)
        return cid
    cid, found = resolve_channel(url)
    with LOCK:
        d = _load_ch()
        if any(c["id"] == cid for c in d["channels"]):
            raise ValueError("this source is already in the table")
        d["channels"].append({"id": cid, "name": (name or found)[:120], "url": url[:300],
                              "language": lang, "vertical": vert, "vertical_auto": v_auto, "added": time.strftime("%Y-%m-%d %H:%M:%S"),
                              "owner_id": owner_id, "owner_name": owner_name, "take_latest": 3,
                              "backfill": bool(req.get("backfill")) and admin})
        _save_ch(d)
    discover_now(cid)
    return cid


# ------------------------------------------------- Live Shows (upcoming Israeli events from Supercaly) ---
LIVE_URL = "https://superca.ly/api/events?country=Israel&categories=Music,Comedy,Dance,Festival&limit=500&start_date=%s"
_LIVE = {"t": 0.0, "items": []}


def live_events():
    """Upcoming Israeli shows from the Supercaly API, cached 30 min; the stale copy is served if Supercaly is down."""
    if _LIVE["items"] and time.time() - _LIVE["t"] < 1800:
        return _LIVE["items"]
    try:
        raw = json.loads(_http(LIVE_URL % time.strftime("%Y-%m-%d"), timeout=40))
        if not isinstance(raw, list):
            raise ValueError("unexpected reply")
    except Exception as e:
        log(f"vidsum live fetch failed: {str(e)[:120]}")
        return _LIVE["items"]
    seen, out = set(), []
    for e in raw:
        if not isinstance(e, dict) or not e.get("name") or not e.get("start_date"):
            continue
        key = (_html.unescape(e["name"]).strip().lower(), e["start_date"], (e.get("venue_name") or "").lower())
        if key in seen:
            continue
        seen.add(key)
        img = e.get("image_url") or ""
        cats = e.get("categories") or []
        out.append({"id": e.get("id"), "name": _html.unescape(e["name"]).strip(), "date": e["start_date"], "time": (e.get("start_time") or "")[:5],
                    "venue": _html.unescape(e.get("venue_name") or ""), "city": e.get("venue_city") or "", "image": img if img.startswith("https://") else "",
                    "link": e.get("purchase_link") or "", "price": e.get("price"), "currency": e.get("price_currency") or "",
                    "cat": cats[0] if cats else "Music", "cats": cats[:3]})
    out.sort(key=lambda x: (x["date"], x["time"] or "99", x["name"]))
    _LIVE["t"], _LIVE["items"] = time.time(), out
    return out


# ------------------------------------------------- מבשלים: dishes of the day from the cookin site ---
DISHES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "pawed_dishes.json")
DISH_GROUPS = [("beef", "בקר"), ("chicken", "עוף"), ("fish", "דגים"), ("veg", "צמחוני")]


def cooking_today():
    """2 dishes per group (beef / chicken / fish / vegetarian), a different pair every Israeli calendar day (stable within the day)."""
    import hashlib
    try:
        from zoneinfo import ZoneInfo
        day = datetime.datetime.now(ZoneInfo("Asia/Jerusalem")).strftime("%Y-%m-%d")
    except Exception:
        day = time.strftime("%Y-%m-%d")
    with open(DISHES_PATH, encoding="utf-8") as f:
        d = json.load(f)
    groups = []
    for key, label in DISH_GROUPS:
        pool = [x for x in d["dishes"] if x["group"] == key]
        pool.sort(key=lambda x: hashlib.md5((day + x["id"]).encode()).hexdigest())
        groups.append({"key": key, "label": label, "dishes": [dict(x, image="https://cookin.jarcud.com/images/" + x["image"]) for x in pool[:2]],
                       "count": len(pool)})
    return {"ok": True, "day": day, "total": d["total"], "groups": groups, "site": "https://cookin.jarcud.com"}

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
            lang = request_lang(handler, qs)
            if lang == "en" and a.get("blocks") and not a.get("en"):
                import vidsum_translate
                vidsum_translate.want(a["slug"])                       # not translated yet: do this one next
            handler._html(render_article(a, lang), "no-store")
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
        body = cover_svg(a or {"vid": vid, "topic": "תרבות", "title": ""}, "en" if (qs.get("lang") or [""])[0] == "en" else "he").encode("utf-8")
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
    if path == "/vidsum/pawed-wordmark.png":
        try:
            with open(os.path.join(_ASSETS, "pawed-wordmark.png"), "rb") as f:
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
    if path == "/vidsum/addep.js":
        try:
            with open(os.path.join(_ASSETS, "vidsum_addep.js"), "rb") as f:
                body = f.read()
            handler.send_response(200)
            handler.send_header("Content-Type", "application/javascript; charset=utf-8")
            handler.send_header("Content-Length", str(len(body)))
            handler.send_header("Cache-Control", "no-cache")
            handler.end_headers()
            handler.wfile.write(body)
        except OSError:
            handler._json({"error": "script missing"}, 404)
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
        qrows, qtotal = queue_view()
        handler._json({"ok": True, "now": time.strftime("%Y-%m-%d %H:%M:%S"), "summary": cnt, "total": len(jobs),
                       "events": _recent_events(int((qs.get("limit") or ["300"])[0])), "relay": relay_status_get(),
                       "queue": qrows, "queue_total": qtotal})
        return True
    if path == "/api/vidsum/lang":
        handler._json({"ok": True, "lang": request_lang(handler, qs)})
        return True
    if path == "/api/vidsum/sources":
        user = current_user(handler)
        signed = bool(user and user.get("id") != "admin-token")
        handler._json({"ok": True, "can_edit": bool(user), "admin": bool(user and user.get("admin")),
                       "me": ({"id": user["id"], "name": user.get("name") or user.get("email"), "avatar": user.get("avatar", "")}
                              if signed else None),
                       "prefs": get_vprefs(user["id"]) if signed else None, "hidden": sources_hidden_count(user) if signed else 0,
                       "hidden_base": ([{"id": c["id"], "name": c["name"]} for c in _load_ch()["channels"]
                                        if c.get("owner_id") is None and c["id"] in get_vprefs(user["id"])["hiddenBase"]]
                                       if signed else []),
                       "limit": MAX_USER_SOURCES, "verticals": TOPICS, "languages": LANGS, "sources": sources_view(user)})
        return True
    if path == "/api/vidsum/admin/stt-compare":
        import stt_test
        return stt_test.handle_get(handler, qs)
    if path == "/api/vidsum/admin/health":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "not found"}, 404)
            return True
        handler._json(health_report(qs))
        return True
    if path == "/api/vidsum/admin/ytcheck":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "not found"}, 404)
            return True
        res = {"api_key": ytserver.api_enabled(), "captions_key": ytserver.captions_enabled()}
        src = (qs.get("source") or [""])[0] or next((c["id"] for c in _load_ch()["channels"] if c.get("kind") != "rss" and c["id"][:2] in ("UC", "PL")), "")
        if res["api_key"] and src:
            t0 = time.time()
            try:
                rows = ytserver.list_videos(src, 5)
                res["list"] = {"ok": True, "source": src, "n": len(rows), "ms": int((time.time() - t0) * 1000),
                               "newest": [{"vid": r["vid"], "title": r["title"][:50], "published": r["published"], "duration": r["duration"]} for r in rows[:3]]}
            except Exception as e:
                rows = []
                res["list"] = {"ok": False, "error": _scrub(str(e))[:240]}
            vid = (qs.get("vid") or [""])[0] or (rows[0]["vid"] if rows else "")
            if res["captions_key"] and vid:
                t0 = time.time()
                try:
                    c = ytserver.captions(vid)
                    res["captions"] = {"ok": True, "vid": vid, "ms": int((time.time() - t0) * 1000), "blocks": c["transcript"].count("\n") + 1,
                                       "chars": len(c["transcript"]), "source": c["source"], "title": c["title"][:50], "sample": c["transcript"][:80]}
                except Exception as e:
                    res["captions"] = {"ok": False, "vid": vid, "error": _scrub(str(e))[:300], "kind": type(e).__name__}
        handler._json({"ok": True, **res})
        return True
    if path == "/api/vidsum/admin/tokens":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "not found"}, 404)
            return True
        days = max(1, min(60, int((qs.get("days") or ["7"])[0])))
        cut = time.strftime("%Y-%m-%d", time.localtime(time.time() - (days - 1) * 86400))
        rows = []
        try:
            with open(TOK_PATH, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    if r["t"][:10] >= cut:
                        rows.append(r)
        except OSError:
            pass
        with multiuser.db() as c:
            names = {r["id"]: (r["name"] or r["email"]) for r in c.execute("SELECT id,name,email FROM users").fetchall()}
        agg = lambda key: [dict(zip(("key", "calls", "in", "out"), (k, *v))) for k, v in sorted(
            ((k, [sum(1 for r in rows if key(r) == k), sum(r["in"] for r in rows if key(r) == k), sum(r["out"] for r in rows if key(r) == k)])
             for k in {key(r) for r in rows}), key=lambda kv: -(kv[1][1] + kv[1][2]))]
        handler._json({"ok": True, "days": days, "since": cut, "calls": len(rows), "total_in": sum(r["in"] for r in rows), "total_out": sum(r["out"] for r in rows),
                       "by_task": agg(lambda r: r["task"] + " · " + r["model"]), "by_day": agg(lambda r: r["t"][:10]),
                       "by_user": agg(lambda r: names.get(r["owner"], "Pawed (admin)") if r["owner"] else "Pawed (admin)")})
        return True
    if path == "/api/vidsum/admin/users":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "not found"}, 404)
            return True
        chs = _load_ch()["channels"]
        base_n = sum(1 for c in chs if c.get("owner_id") is None)
        with multiuser.db() as c:
            urows = {r["id"]: dict(r) for r in c.execute("SELECT id,email,name,last_seen FROM users").fetchall()}
        with _vdb() as c:
            prefs = {r["user_id"]: r for r in c.execute("SELECT * FROM vidsum_prefs").fetchall()}
        out = []
        for uid in set(urows) & ({c.get("owner_id") for c in chs if c.get("owner_id")} | set(prefs)):
            u, p = urows[uid], get_vprefs(uid)
            mine = [{"name": c["name"], "language": c.get("language"), "vertical": c.get("vertical"), "kind": c.get("kind") or "yt",
                     "off": c["id"] in p["hiddenBase"], "added": c.get("added", "")} for c in chs if c.get("owner_id") == uid]
            hid_base = [c["id"] for c in chs if c.get("owner_id") is None and c["id"] in p["hiddenBase"]]
            if not mine and not p["hideBase"] and not hid_base:
                continue
            out.append({"id": uid, "name": u.get("name") or "", "email": u.get("email") or "", "last_seen": u.get("last_seen") or "",
                        "sources": mine, "hide_all_base": p["hideBase"], "hidden_base": len(hid_base), "base_total": base_n})
        out.sort(key=lambda x: x["last_seen"], reverse=True)
        handler._json({"ok": True, "users": out})
        return True
    if path.startswith("/api/vidsum/catalog/"):
        user = current_user(handler)
        if not user:
            handler._json({"ok": False, "error": "sign in with Google first"}, 401)
            return True
        import podscanner
        if path == "/api/vidsum/catalog/suggest":
            handler._json({"ok": True, "pods": podscanner.catalog_suggest((qs.get("q") or [""])[0])})
        elif path == "/api/vidsum/catalog/options":
            langs, ctry = podscanner.catalog_options()
            handler._json({"ok": True, "languages": langs, "countries": ctry, "topics": TOPICS, "rules": podscanner.QUALITY})
        elif path == "/api/vidsum/catalog/browse":
            g = lambda k: (qs.get(k) or [""])[0]
            pods, total = podscanner.catalog_browse(g("language"), g("country"), g("topic"))
            handler._json({"ok": True, "pods": pods, "total": total})
        else:
            return False
        return True
    if path == "/api/vidsum/cooking":
        try:
            handler._json(cooking_today())
        except Exception as e:
            log(f"vidsum cooking failed: {str(e)[:120]}")
            handler._json({"ok": False, "error": "dishes unavailable"}, 500)
        return True
    if path == "/api/vidsum/live":
        handler._json({"ok": True, "items": live_events(), "source": "https://superca.ly"})
        return True
    if path == "/api/vidsum/me":
        user = current_user(handler)
        handler._json({"signed": bool(user), "admin": bool(user and user.get("admin"))})
        return True
    if path == "/api/vidsum/news":
        user = current_user(handler)
        as_id = (qs.get("as") or [""])[0]
        if as_id and user and user.get("admin"):                      # admin preview: the homepage exactly as that user gets it
            with multiuser.db() as c:
                r = c.execute("SELECT id,email,name FROM users WHERE id=?", (as_id,)).fetchone()
            if r:
                user = {"id": r["id"], "email": r["email"], "name": r["name"], "admin": False}
        items = news_items()
        vis = _visible_source_ids(user)
        personal = vis is not None and bool(user)
        if vis is not None:                              # guests and signed-in users: private sources and one-off episodes stay private
            uid = user["id"] if user else None
            pr = get_vprefs(uid) if uid else {"hideBase": False, "hiddenBase": []}
            base_ok = not pr["hideBase"]
            custom = bool(pr["hideBase"] or pr["hiddenBase"])        # an article we cannot tie to a source is only shown to people on the default roster
            items = [i for i in items if (i["source_id"] in vis) or (not i["source_id"] and not i.get("submitted_by") and base_ok and not custom)
                     or (uid and i.get("submitted_by") == uid)]
        if vis is None and user and user.get("admin") and user.get("id") != "admin-token":
            owners = {c["id"]: c.get("owner_id") for c in _load_ch()["channels"]}        # an admin's homepage is the Pawed roster, not other users' private sources
            items = [i for i in items if not owners.get(i["source_id"]) and not i.get("submitted_by")]
        gone = removed_topics(user)
        if gone:                                         # a switched-off section loses its tab and every article filed under it
            items = [dict(i, topics=[t for t in i["topics"] if t not in gone]) for i in items if i["topic"] not in gone]
        handler._json({"ok": True, "topics": [t for t in TOPICS if t not in gone], "items": items, "personal": personal,
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
                 "daily": c.get("cadence") == "daily", "pub_days": c.get("pub_days") or [], "seen": (c.get("seen") or [])[-300:]} for c in _load_ch()["channels"] if not c["id"].startswith("pending-") and c.get("kind") != "rss"]})
        return True
    if path == "/api/vidsum/links/todo":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            lim = int((qs.get("limit") or ["20"])[0])
            today = time.strftime("%Y-%m-%d")
            todo = []
            for a in sorted(_articles(), key=lambda x: x.get("published_at") or x.get("created") or "", reverse=True):
                lk = a.get("links") or {}
                if not a.get("vid") or (lk.get("apple") and lk.get("spotify")):
                    continue
                if lk.get("checked") and lk["checked"] >= time.strftime("%Y-%m-%d", time.localtime(time.time() - 3 * 86400)):
                    continue                      # looked recently; new episodes appear on podcast feeds late, retry after 3 days
                todo.append({"slug": a["slug"], "vid": a["vid"], "channel": a.get("channel", ""), "src_title": a.get("src_title", ""),
                             "published": a.get("published") or ""})
                if len(todo) >= lim:
                    break
            handler._json({"ok": True, "todo": todo})
        return True
    if path == "/api/vidsum/relay/queue":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            handler._json({"ok": True, "queue": relay_queue(int((qs.get("limit") or ["15"])[0])),
                           "need_dates": [a["vid"] for a in _articles() if a.get("vid") and not a.get("published_at") and a.get("kind") != "rss"][:25]})
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
            elif path == "/api/vidsum/relay/status":
                relay_status_set(req)
                handler._json({"ok": True})
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
    if path == "/api/vidsum/links/set":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            slug = str(req.get("slug") or "")
            try:
                with open(os.path.join(ART_DIR, os.path.basename(slug) + ".json"), encoding="utf-8") as f:
                    a = json.load(f)
            except Exception:
                handler._json({"ok": False, "error": "no such article"}, 404)
                return True
            lk = {k: str(v)[:400] for k, v in (req.get("links") or {}).items() if k in ("apple", "spotify", "checked") and v}
            for k in ("apple", "spotify"):                     # never overwrite a link we already have with nothing
                if not lk.get(k) and (a.get("links") or {}).get(k):
                    lk[k] = a["links"][k]
            ok_host = {"apple": "https://podcasts.apple.com/", "spotify": "https://open.spotify.com/"}
            lk = {k: v for k, v in lk.items() if k == "checked" or v.startswith(ok_host[k])}
            a["links"] = lk
            _write_article(a)
            handler._json({"ok": True, "links": lk})
        return True
    if path == "/api/vidsum/admin/users/reset-own":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "not found"}, 404)
            return True
        uid = str(req.get("user_id") or "")
        own = {c["id"] for c in _load_ch()["channels"] if c.get("owner_id") == uid}
        p = get_vprefs(uid)
        fixed = [i for i in p["hiddenBase"] if i in own]
        set_vprefs(uid, {"hiddenBase": [i for i in p["hiddenBase"] if i not in own]})
        handler._json({"ok": True, "switched_on": len(fixed)})
        return True
    if path == "/api/vidsum/article/topic":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
            return True
        slug, prim = str(req.get("slug") or ""), req.get("topic")
        a = next((x for x in _articles() if x.get("slug") == slug), None)
        if not a or prim not in TOPICS:
            handler._json({"ok": False, "error": "unknown article or topic"}, 400)
            return True
        sec = req.get("secondary") if req.get("secondary") in TOPICS and req.get("secondary") != prim else None
        a["topic"], a["topics"], a["topics_v"] = prim, [prim] + ([sec] if sec else []), 4
        _write_article(a)
        handler._json({"ok": True, "topics": a["topics"]})
        return True
    if path == "/api/vidsum/topics/backfill":
        user = current_user(handler)
        if not (user and user.get("admin")):
            handler._json({"error": "forbidden"}, 403)
        else:
            redo = bool(req.get("redo"))
            n = backfill_topics(int(req.get("limit") or 12), redo, req.get("only") or None)
            handler._json({"ok": True, "done": n, "remaining": sum(1 for a in _articles() if a.get("blocks") and (a.get("topics_v") != 4 if redo else not a.get("topics")))})
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
    if path == "/api/vidsum/lang":                       # remember the language for the signed-in user (the cookie is set by the page)
        l = req.get("lang")
        user = current_user(handler)
        if l in ("he", "en") and user and user.get("id") != "admin-token":
            set_vprefs(user["id"], {"lang": l})
        handler._json({"ok": l in ("he", "en"), "lang": l})
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
                if req.get("catalog_id"):                   # picked from the scanner catalog: name, feed, language and topic are already known
                    import podscanner
                    p = podscanner.catalog_pod(str(req["catalog_id"]))
                    if not p:
                        raise ValueError("this podcast is not in the catalog")
                    twin = podscanner.existing_source_name(p["name"])
                    if twin:
                        raise ValueError(f"already in the sources table as \"{twin}\"")
                    req = {"url": p["feed"], "name": p["name"], "language": p["language"] if p["language"] in LANGS else "other",
                           "vertical": p["topic"] if p["topic"] in TOPICS else "תרבות"}
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
                        if (req.get("url") or "").strip() and not _is_youtube_ref(req["url"]):
                            info = vidsum_feeds.resolve_feed(req["url"].strip(), req.get("name") or c.get("name"))
                            if info["id"] != c["id"] and any(x["id"] == info["id"] for x in d["channels"]):
                                raise ValueError("this source is already in the table")
                            c.update(id=info["id"], kind="rss", feed_url=info["feed_url"], image=info["image"], url=req["url"].strip()[:300],
                                     added=time.strftime("%Y-%m-%d %H:%M:%S"), take_latest=True)
                            c.pop("seen", None)
                        elif (req.get("url") or "").strip():
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
                            c.pop("vertical_auto", None)
                        if (req.get("name") or "").strip():
                            c["name"] = req["name"].strip()[:120]
                        if "no_headline" in req and user.get("admin"):
                            c["no_headline"] = bool(req["no_headline"])
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
            elif path == "/api/vidsum/channels/take_latest":
                ids = {str(x) for x in (req.get("ids") or [])}
                with LOCK:
                    d = _load_ch()
                    n = 0
                    for c in d["channels"]:
                        if c["id"] in ids and c.get("kind") != "rss":
                            c["take_latest"] = True
                            c["seen"] = []                      # the next scan sees the whole feed again; only the newest is taken
                            n += 1
                    _save_ch(d)
                handler._json({"ok": True, "armed": n})
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
    if path == "/api/vidsum/submit":
        user = current_user(handler)
        if not user:
            handler._json({"ok": False, "error": "sign in with Google first"}, 401)
            return True
        is_admin = bool(user.get("admin"))
        owner = "admin" if user.get("id") == "admin-token" else user["id"]
        url = str(req.get("url") or "").strip()[:300]
        code, payload = submit(url, is_admin, "luna", None, owner)
        if payload.get("ok") and payload.get("existing"):
            payload["slug"] = payload.get("slug")
        handler._json(payload, code)
        return True
    if path == "/api/vidsum/summarize":
        user = current_user(handler)
        is_admin = bool(user and user.get("admin"))
        code, payload = submit(str(req.get("url") or ""), is_admin, req.get("engine", "luna") if is_admin else "luna")
        handler._json(payload, code)
        return True
    return False
