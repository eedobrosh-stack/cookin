"""English edition of Pawed: every article gets an "en" block (title, standfirst, lead, key points, blocks) translated from the Hebrew.

New articles are picked up by the background loop (newest first), the old archive is backfilled the same way, and an English page request for
an article without a translation moves it to the front of the line. The translation is stored in the article's own JSON ("en" key), the
Hebrew text is never touched.
"""
import json
import threading
import time

import vidsum_articles as va

_WANT = []                       # slugs asked for by a page view, translated first
_FAILED = {}                     # slug -> time of the last failure (retried after an hour)
_BUSY = set()
_LOCK = threading.Lock()


def _payload(a):
    return {"title": a.get("title") or "", "standfirst": a.get("standfirst") or "", "lead": a.get("lead") or "",
            "key_points": list(a.get("key_points") or []),
            "blocks": [{"type": b.get("type"), "text": b.get("text") or "", "speaker": b.get("speaker") or "", "items": list(b.get("items") or [])}
                       for b in a.get("blocks") or []]}


def _prompt(src):
    return ("Translate this Hebrew news article (a written summary of a podcast or video episode) into natural, fluent English for an English-language "
            "news site. Keep the meaning, names and numbers exact. Transliterate Hebrew names the common way. Keep quotes as quotes. "
            "Do not add or drop information.\n"
            "Return ONLY one valid JSON object with exactly the same shape and the same number of blocks, key points and list items as the input, "
            "translating every string value (leave empty strings empty and keep every block's \"type\" unchanged). "
            "Never use the ASCII double-quote character inside a string value (use single quotes instead), so the JSON stays valid. "
            "Do not use long dashes, use a spaced hyphen.\n\nINPUT:\n" + json.dumps(src, ensure_ascii=False))


def _valid(src, out):
    if not isinstance(out, dict) or not (out.get("title") or "").strip():
        return False
    if len(out.get("key_points") or []) != len(src["key_points"]) or len(out.get("blocks") or []) != len(src["blocks"]):
        return False
    for s, o in zip(src["blocks"], out["blocks"]):
        if not isinstance(o, dict) or len(o.get("items") or []) != len(s["items"]):
            return False
        if s["text"].strip() and not (o.get("text") or "").strip():
            return False
    return True


def translate(slug):
    """Translate one article and store it. -> True if stored."""
    with _LOCK:
        if slug in _BUSY:
            return False
        _BUSY.add(slug)
    try:
        a = _load(slug)
        if not a or a.get("en"):
            return bool(a)
        src = _payload(a)
        out = None
        with va.tok_ctx("translate", a.get("vid") or slug, None):
            for _ in range(2):
                res, _tok, _stop = va._luna(_prompt(src), max_tokens=24000)
                if _valid(src, res):
                    out = res
                    break
                va.log(f"vidsum translate {slug}: shape mismatch, asking again")
        if not out:
            raise RuntimeError("translation shape mismatch")
        en = {"title": va.vidsum_render.nodash(out["title"]).strip(), "standfirst": va.vidsum_render.nodash(out.get("standfirst") or "").strip(),
              "lead": va.vidsum_render.nodash(out.get("lead") or "").strip(),
              "key_points": [va.vidsum_render.nodash(str(k)) for k in out["key_points"]],
              "blocks": [{"type": s["type"], "text": va.vidsum_render.nodash(o.get("text") or ""), "speaker": o.get("speaker") or "",
                          "items": [va.vidsum_render.nodash(str(i)) for i in (o.get("items") or [])]} for s, o in zip(src["blocks"], out["blocks"])],
              "at": time.strftime("%Y-%m-%d %H:%M:%S"), "model": va.LUNA_MODEL}
        with va.LOCK:                                       # re-read: other jobs may have rewritten the article meanwhile; only add "en"
            cur = _load(slug)
            if not cur:
                return False
            cur["en"] = en
            va._write_article(cur)
        va.log(f"vidsum translate {slug} DONE")
        return True
    except Exception as e:
        _FAILED[slug] = time.time()
        va.log(f"vidsum translate {slug} failed: {va._scrub(str(e))[:200]}")
        return False
    finally:
        with _LOCK:
            _BUSY.discard(slug)


def _load(slug):
    try:
        import os
        with open(os.path.join(va.ART_DIR, slug + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def want(slug):
    """An English page was requested for an article that has no translation yet: do it next."""
    with _LOCK:
        if slug not in _WANT:
            _WANT.append(slug)


def _next():
    with _LOCK:
        while _WANT:
            s = _WANT.pop(0)
            if s not in _BUSY:
                return s
    for a in va._articles():                                  # newest release first
        s = a.get("slug")
        if s and not a.get("en") and s not in _BUSY and time.time() - _FAILED.get(s, 0) > 3600:
            return s
    return None


def pending():
    return sum(1 for a in va._articles() if not a.get("en"))


def loop():
    time.sleep(240)
    while True:
        try:
            s = _next()
            if s:
                translate(s)
                time.sleep(3)
                continue
        except Exception as e:
            va.log(f"vidsum translate loop error: {str(e)[:200]}")
        time.sleep(60)


def start():
    for _ in range(2):                                        # two at a time (LunaRoute takes up to 3 articles at once)
        threading.Thread(target=loop, daemon=True).start()
