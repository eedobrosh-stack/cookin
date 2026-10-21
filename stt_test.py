"""Admin experiment: can Gemini transcribe a podcast episode as well as the Mac's Whisper did?

Takes a podcast episode that already has a Whisper transcript (from the Mac relay), sends the same audio to Gemini (Files API),
and compares the two: time, tokens, how much they agree, and whether Gemini's timestamps drift. Nothing is published or changed.
Started with GET /api/vidsum/admin/stt-compare?run=1[&vid=...], read with GET /api/vidsum/admin/stt-compare.
"""
import difflib, json, os, re, tempfile, threading, time, urllib.error, urllib.request

import multiuser
import vidsum_articles as va

STATE = {"status": "idle"}
_LOCK = threading.Lock()
MAX_AUDIO_MB = 120
BASE = "https://generativelanguage.googleapis.com"


def _words(s):
    s = re.sub(r"[֑-ׇ]", "", s or "")
    return re.findall(r"[\w']+", s.lower())


def _blocks(text):
    out = []
    for line in (text or "").splitlines():
        m = re.match(r"\s*\[(?:(\d+):)?(\d+):(\d+)\]\s*(.*)", line)
        if m:
            h, mi, se, t = m.groups()
            out.append((int(h or 0) * 3600 + int(mi) * 60 + int(se), t))
    return out


def _window(blocks, lo, hi):
    return " ".join(t for s, t in blocks if lo <= s < hi)


def _jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / max(1, len(a | b))


def pick_episode():
    """newest podcast episode with a Whisper transcript, 20-45 minutes long (short enough for one Gemini answer)"""
    best = None
    for vid, j in va._load_jobs().items():
        if j.get("kind") != "rss" or j.get("status") != "done" or not j.get("audio"):
            continue
        if not os.path.exists(os.path.join(va.TR_DIR, vid + ".json")):
            continue
        d = j.get("duration") or 0
        if 20 * 60 <= d <= 45 * 60 and (best is None or (j.get("updated") or "") > (best[1].get("updated") or "")):
            best = (vid, j)
    return best


def _download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pawed)"})
    size = 0
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        mime = r.headers.get_content_type() or "audio/mpeg"
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_AUDIO_MB * (1 << 20):
                raise RuntimeError(f"audio larger than {MAX_AUDIO_MB} MB")
            f.write(chunk)
    return size, (mime if mime.startswith("audio/") else "audio/mpeg")


def _upload(path, mime, key):
    size = os.path.getsize(path)
    start = urllib.request.Request(f"{BASE}/upload/v1beta/files?key={key}", data=json.dumps({"file": {"display_name": "pawed-stt-test"}}).encode(),
                                   headers={"X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                                            "X-Goog-Upload-Header-Content-Length": str(size), "X-Goog-Upload-Header-Content-Type": mime,
                                            "Content-Type": "application/json"})
    with urllib.request.urlopen(start, timeout=60) as r:
        up_url = r.headers["x-goog-upload-url"]
    with open(path, "rb") as f:
        data = f.read()
    fin = urllib.request.Request(up_url, data=data, headers={"X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize",
                                                              "Content-Length": str(size)})
    with urllib.request.urlopen(fin, timeout=300) as r:
        info = json.loads(r.read().decode())["file"]
    for _ in range(60):                                          # the file has to become ACTIVE before it can be used
        if info.get("state") == "ACTIVE":
            return info
        time.sleep(2)
        with urllib.request.urlopen(f"{BASE}/v1beta/{info['name']}?key={key}", timeout=30) as r:
            info = json.loads(r.read().decode())
    raise RuntimeError("Gemini file never became ACTIVE")


PROMPT = ("Transcribe this Hebrew podcast episode word for word, in Hebrew, with no summary and nothing left out. Start a new line every ~30 seconds "
          "with the elapsed time in the form [m:ss] (or [h:mm:ss] after an hour), then the speech of that stretch. Do not add speaker names or comments.")


def _with_retry(fn, *args, tries=3, pause=20):
    """Gemini answers 500/503 now and then: try again before giving up"""
    last = None
    for i in range(tries):
        try:
            return fn(*args)
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (429, 500, 502, 503, 504) or i == tries - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            if i == tries - 1:
                raise
        time.sleep(pause * (i + 1))
    raise last


def _generate(file_info, key, prompt=None):
    body = {"contents": [{"role": "user", "parts": [{"file_data": {"mime_type": file_info.get("mimeType", "audio/mpeg"), "file_uri": file_info["uri"]}},
                                                      {"text": prompt or PROMPT}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 65536}}
    req = urllib.request.Request(f"{BASE}/v1beta/models/{multiuser.GEMINI_MODEL}:generateContent?key={key}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        res = json.loads(r.read().decode())
    cand = res["candidates"][0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    um = res.get("usageMetadata") or {}
    return text, um, cand.get("finishReason")


def compare(whisper_text, gemini_text, duration):
    wb, gb = _blocks(whisper_text), _blocks(gemini_text)
    out = {"whisper_blocks": len(wb), "gemini_blocks": len(gb), "whisper_words": len(_words(whisper_text)), "gemini_words": len(_words(gemini_text))}
    if not wb or not gb:
        out["error"] = "one transcript has no timestamped blocks"
        return out
    # agreement: Gemini block vs the Whisper text at the same time (+-)
    agree = []
    for s, t in gb:
        gw = _words(t)
        ww = _words(_window(wb, s - 20, s + 50))
        if gw and ww:
            agree.append(difflib.SequenceMatcher(None, gw, ww, autojunk=False).ratio() if len(gw) < 150 else _jaccard(gw, ww))
    out["agreement_avg"] = round(sum(agree) / max(1, len(agree)), 3)
    # timestamp drift at 9 points through the episode: which shift of the Whisper timeline fits Gemini's block best
    drift = []
    idxs = sorted({int(i * (len(gb) - 1) / 8) for i in range(9)})
    for i in idxs:
        s, t = gb[i]
        gw = _words(t)
        scores = {off: _jaccard(gw, _words(_window(wb, s + off, s + off + 32))) for off in range(-120, 121, 5)}
        top = max(scores.values())
        tied = sorted(off for off, sc in scores.items() if sc >= top - 1e-9)          # a plateau of equally good shifts: take its middle
        drift.append({"at": s, "gemini_late_s": -(tied[len(tied) // 2] + 16)})        # +16 centres the 32 s window; positive = Gemini's clock runs ahead of Whisper's
    out["drift"] = drift
    offs = [abs(d["gemini_late_s"]) for d in drift]
    out["drift_max_s"] = max(offs)
    out["drift_median_s"] = sorted(offs)[len(offs) // 2]
    # side-by-side samples (start, middle, end)
    out["samples"] = []
    for i in (1, len(gb) // 2, len(gb) - 2):
        if 0 <= i < len(gb):
            s, t = gb[i]
            out["samples"].append({"t": s, "gemini": t[:220], "whisper": _window(wb, s - 3, s + 32)[:220]})
    return out


def _run(vid, job):
    t0 = time.time()
    key = (multiuser.secret("GEMINI_API_KEY") or "").strip()
    res = {"status": "running", "vid": vid, "title": job.get("title"), "duration_s": job.get("duration"), "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    with _LOCK:
        STATE.clear(); STATE.update(res)
    try:
        if not key:
            raise RuntimeError("GEMINI_API_KEY missing")
        with open(os.path.join(va.TR_DIR, vid + ".json"), encoding="utf-8") as f:
            whisper = json.load(f)["transcript"]
        tmp = tempfile.mkdtemp(prefix="stt_")
        path = os.path.join(tmp, "a.mp3")
        t = time.time(); size, mime = _download(job["audio"], path); res["download_s"] = round(time.time() - t, 1); res["audio_mb"] = round(size / 1e6, 1)
        t = time.time(); info = _with_retry(_upload, path, mime, key); res["upload_s"] = round(time.time() - t, 1)
        t = time.time()
        with va.tok_ctx("stt-test", vid):
            text, um, fin = _with_retry(_generate, info, key)
        res["generate_s"] = round(time.time() - t, 1)
        va._tok_log(multiuser.GEMINI_MODEL, um.get("promptTokenCount", 0), um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0))
        res.update(tokens_in=um.get("promptTokenCount"), tokens_out=um.get("candidatesTokenCount"), tokens_thoughts=um.get("thoughtsTokenCount"),
                   finish=fin, gemini_chars=len(text), whisper_chars=len(whisper), gemini_head=text[:300])
        res["compare"] = compare(whisper, text, job.get("duration"))
        res["status"] = "done"
        try:
            os.remove(path)
            os.rmdir(tmp)
        except OSError:
            pass
    except Exception as e:
        res["status"] = "failed"
        res["error"] = va._scrub(str(e))[:400]
    res["total_s"] = round(time.time() - t0, 1)
    with _LOCK:
        STATE.clear(); STATE.update(res)


def audit():
    """Podcast episodes whose stored (Whisper) transcript is mostly NOT in the language the job says: wrong-language transcription."""
    rows = []
    arts = {a.get("vid"): a for a in va._articles()}
    for vid, j in va._load_jobs().items():
        if j.get("kind") != "rss":
            continue
        p = os.path.join(va.TR_DIR, vid + ".json")
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                tr = json.load(f).get("transcript") or ""
        except (OSError, ValueError):
            continue
        letters = [c for c in tr if c.isalpha()]
        if not letters:
            continue
        he = sum(1 for c in letters if "\u0590" <= c <= "\u05ff") / len(letters)
        rows.append({"vid": vid, "title": (j.get("title") or "")[:60], "channel": (j.get("channel") or "")[:30], "job_language": j.get("language"),
                     "source": j.get("source"), "hebrew_ratio": round(he, 2), "status": j.get("status"), "has_article": vid in arts,
                     "duration": j.get("duration"), "method": (arts.get(vid) or {}).get("method")})
    rows.sort(key=lambda r: r["hebrew_ratio"])
    return rows


def handle_get(handler, qs):
    user = va.current_user(handler)
    if not (user and user.get("admin")):
        handler._json({"error": "not found"}, 404)
        return True
    rq = (qs.get("requeue") or [""])[0]
    if rq:                                                         # rebuild a podcast job (audio link, title, source...) from its feed and queue it again
        import vidsum_feeds
        for ch in va._load_ch()["channels"]:
            if ch.get("kind") != "rss":
                continue
            try:
                items = vidsum_feeds.parse_feed(vidsum_feeds.fetch(ch["feed_url"]))["items"]
            except Exception:
                continue
            it = next((i for i in items if vidsum_feeds.episode_id(i) == rq), None)
            if it:
                ok = va._submit_rss(ch, it)
                handler._json({"ok": bool(ok), "requeued": rq, "source": ch["name"], "title": it["title"][:80], "language": ch.get("language")})
                return True
        handler._json({"ok": False, "error": "episode not found in any podcast feed"})
        return True
    redo = (qs.get("redo") or [""])[0]
    if redo:                                                       # throw away an article built from a bad transcript and let the pipeline redo it
        job = va._load_jobs().get(redo)
        if not job or job.get("kind") != "rss":
            handler._json({"ok": False, "error": "unknown podcast job"})
            return True
        deleted = 0
        for a in va._articles():                                  # remove the article but KEEP the job (it holds the audio link, title, source)
            if a.get("vid") == redo:
                try:
                    os.remove(os.path.join(va.ART_DIR, a["slug"] + ".json"))
                    deleted += 1
                except OSError:
                    pass
        try:
            os.remove(os.path.join(va.TR_DIR, redo + ".json"))
        except OSError:
            pass
        va._set_job(redo, status="needs_transcript", language=(qs.get("language") or ["he"])[0], error="", gstt_next=0, srv_claim=0, attempts=0,
                    submitted=time.strftime("%Y-%m-%d %H:%M:%S"))
        handler._json({"ok": True, "redo": redo, "article_deleted": deleted})
        return True
    if (qs.get("audit") or [""])[0]:
        handler._json({"ok": True, "rows": audit()})
        return True
    if (qs.get("run") or [""])[0]:
        if STATE.get("status") == "running":
            handler._json({"ok": False, "error": "already running", **STATE})
            return True
        vid = (qs.get("vid") or [""])[0]
        job = va._load_jobs().get(vid) if vid else None
        if not job:
            pick = pick_episode()
            if not pick:
                handler._json({"ok": False, "error": "no podcast episode with a Whisper transcript and 20-45 min duration found"})
                return True
            vid, job = pick
        threading.Thread(target=_run, args=(vid, job), daemon=True).start()
        handler._json({"ok": True, "started": vid, "title": job.get("title")})
        return True
    handler._json({"ok": True, **STATE})
    return True
