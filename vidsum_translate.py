"""English edition of Pawed: every article gets an "en" block (title, standfirst, lead, key points, blocks): translated from the Hebrew,
or, when the episode itself was not in Hebrew, written in English from the original transcript (never Hebrew -> English).

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
_UPGRADED = set()                 # translated articles already checked for the original-English upgrade (this process)
_REDO = set()
_LOCK = threading.Lock()


def _payload(a):
    return {"title": a.get("title") or "", "standfirst": a.get("standfirst") or "", "lead": a.get("lead") or "",
            "key_points": list(a.get("key_points") or []),
            "blocks": [{"type": b.get("type"), "text": b.get("text") or "", "speaker": b.get("speaker") or "", "items": list(b.get("items") or [])}
                       for b in a.get("blocks") or []]}


def _prompt(src, to="English"):
    frm = "English" if to == "Hebrew" else "Hebrew"
    site = "an Israeli news portal, in the style of a Hebrew news site feature" if to == "Hebrew" else "an English-language news site"
    style = ("Use news-style Hebrew attribution (\u05dc\u05d3\u05d1\u05e8\u05d9\u05d5, \u05dc\u05d8\u05e2\u05e0\u05ea\u05d5). " if to == "Hebrew"
             else "Transliterate Hebrew names the common way. ")
    return (f"Translate this {frm} news article (a written summary of a podcast or video episode) into natural, fluent {to} for {site}. "
            "Keep the meaning, names and numbers exact. Keep quotes as quotes. Do not add or drop information. " + style +
            "\nReturn ONLY one valid JSON object with exactly the same shape and the same number of blocks, key points and list items as the input, "
            "translating every string value (leave empty strings empty and keep every block's \"type\" unchanged). "
            "Never use the ASCII double-quote character inside a string value (use single quotes instead), so the JSON stays valid. "
            "Do not use long dashes, use a spaced hyphen.\n\nINPUT:\n" + json.dumps(src, ensure_ascii=False))


def _translated(src, to, label):
    """-> the translated payload (same shape as _payload), asked twice at most; raises on a shape mismatch."""
    for _ in range(2):
        res, _tok, _stop = va._luna(_prompt(src, to), max_tokens=24000)
        if _valid(src, res):
            nd = va.vidsum_render.nodash
            return {"title": nd(res["title"]).strip(), "standfirst": nd(res.get("standfirst") or "").strip(), "lead": nd(res.get("lead") or "").strip(),
                    "key_points": [nd(str(k)) for k in res["key_points"]],
                    "blocks": [{"type": x["type"], "text": nd(o.get("text") or ""), "speaker": o.get("speaker") or "",
                                "items": [nd(str(i)) for i in (o.get("items") or [])]} for x, o in zip(src["blocks"], res["blocks"])]}
        va.log(f"vidsum translate {label}: shape mismatch, asking again")
    raise RuntimeError("translation shape mismatch")


def to_hebrew(art):
    """An article written in English -> its Hebrew version (title, standfirst, lead, key_points, blocks with the same timestamps)."""
    out = _translated(_payload(art), "Hebrew", art.get("slug") or art.get("vid") or "article")
    blocks = []
    for orig, t in zip(art["blocks"], out["blocks"]):
        nb = {"type": orig["type"], "text": t["text"], "ts": orig.get("ts", "")}
        if orig["type"] == "quote":
            nb["speaker"] = t["speaker"] or orig.get("speaker", "")
        if orig["type"] == "list":
            nb = {"type": "list", "items": t["items"]}
        blocks.append(nb)
    return {"title": out["title"], "standfirst": out["standfirst"], "lead": out["lead"] or out["standfirst"], "key_points": out["key_points"], "blocks": blocks}


def _english_original(a):
    """An article whose episode was NOT in Hebrew: write its English version from the original transcript, never from the Hebrew summary.
    -> the "en" dict, or None when there is no transcript on disk / the episode is Hebrew."""
    import os
    try:
        with open(os.path.join(va.TR_DIR, (a.get("vid") or "") + ".json"), encoding="utf-8") as f:
            tr = json.load(f)
    except Exception:
        return None
    text = tr.get("transcript") or ""
    if not text or va._hebrew_share(text[:30000]) >= 0.3:
        return None
    dur, title, channel = tr.get("duration"), tr.get("title") or a.get("src_title") or "", tr.get("channel") or a.get("channel") or ""
    data = None
    for retry in (False, True):
        prompt = va._text_prompt_en(title, channel, dur, text, retry)
        if tr.get("description"):
            prompt += "\n\nVIDEO DESCRIPTION (use for names and context):\n" + tr["description"][:2500]
        data, _tok, _fin, _used = va._write_text(a.get("vid") or "", prompt)
        if va._ts_ok(data, dur):
            break
    fin = va._finalize(data, dur, {})
    return {"title": fin["title"], "standfirst": fin["standfirst"], "lead": fin["lead"], "key_points": fin["key_points"], "blocks": fin["blocks"],
            "original": True, "at": time.strftime("%Y-%m-%d %H:%M:%S"), "model": va.LUNA_MODEL}


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


def translate(slug, redo=False):
    """Translate one article and store it. -> True if stored. redo: an existing Hebrew->English translation of an episode that was not in
    Hebrew is replaced by an English version written from the original transcript (left alone when there is none)."""
    with _LOCK:
        if slug in _BUSY:
            return False
        _BUSY.add(slug)
    try:
        a = _load(slug)
        if not a or (a.get("en") and not redo):
            return bool(a)
        with va.tok_ctx("translate", a.get("vid") or slug, None):
            en = _english_original(a)                               # an English episode: its English version comes from the transcript
            if en is None and redo:
                return True
            if en is None:
                out = _translated(_payload(a), "English", slug)
                en = dict(out, at=time.strftime("%Y-%m-%d %H:%M:%S"), model=va.LUNA_MODEL)
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
    arts = va._articles()                                     # newest release first
    for a in arts:
        s = a.get("slug")
        if s and not a.get("en") and s not in _BUSY and time.time() - _FAILED.get(s, 0) > 3600:
            return s
    for a in arts:                                            # translations made before the "original English" rule: upgrade the non-Hebrew episodes once
        s = a.get("slug")
        if s and a.get("en") and not a["en"].get("original") and s not in _UPGRADED and s not in _BUSY:
            _UPGRADED.add(s)
            _REDO.add(s)
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
                translate(s, redo=s in _REDO)
                _REDO.discard(s)
                time.sleep(3)
                continue
        except Exception as e:
            va.log(f"vidsum translate loop error: {str(e)[:200]}")
        time.sleep(60)


def start():
    for _ in range(2):                                        # two at a time (LunaRoute takes up to 3 articles at once)
        threading.Thread(target=loop, daemon=True).start()
