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


def _prompt(src, to="English", frm=None):
    frm = frm or ("English" if to == "Hebrew" else "Hebrew")
    site = ("an Israeli news portal, in the style of a Hebrew news site feature" if to == "Hebrew" else
            "an English-language news site" if to == "English" else f"a {to}-language news site")
    style = ("Use news-style Hebrew attribution (\u05dc\u05d3\u05d1\u05e8\u05d9\u05d5, \u05dc\u05d8\u05e2\u05e0\u05ea\u05d5). " if to == "Hebrew"
             else "Transliterate Hebrew names the common way. " if to == "English"
             else f"Use the natural {to} journalistic attribution style (said, according to) and keep proper names in their usual spelling. ")
    return (f"Translate this {frm} news article (a written summary of a podcast or video episode) into natural, fluent {to} for {site}. "
            "Keep the meaning, names and numbers exact. Keep quotes as quotes. Do not add or drop information. " + style +
            "\nReturn ONLY one valid JSON object with exactly the same shape and the same number of blocks, key points and list items as the input, "
            "translating every string value (leave empty strings empty and keep every block's \"type\" unchanged). "
            "Never use the ASCII double-quote character inside a string value (use single quotes instead), so the JSON stays valid. "
            "Do not use long dashes, use a spaced hyphen.\n\nINPUT:\n" + json.dumps(src, ensure_ascii=False))


def _translated(src, to, label, frm=None):
    """-> the translated payload (same shape as _payload), asked twice at most; raises on a shape mismatch."""
    for _ in range(2):
        res, _tok, _stop = va._luna(_prompt(src, to, frm), max_tokens=24000)
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
    arts = va._article_index()                                # newest release first (slim copies)
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
    return sum(1 for a in va._article_index() if not a.get("en"))


# ------------------------------------------------------------------ language editions (de/fr/it/es/pt/nl), demand driven
import os

import geo_suites
import pawed_i18n
import vidsum_render

TR_SINCE = time.strftime("%Y-%m-%d", time.localtime(time.time() - 3 * 86400))   # full language editions are written ahead of time for articles of the last 3 days; older ones get headlines (trh) and a full edition when opened
TR_SINCE_MIN = "2026-11-01"
LANG_NAME = {"de": "German", "fr": "French", "it": "Italian", "es": "Spanish", "pt": "Brazilian Portuguese", "nl": "Dutch"}
LANG_DAILY_CAP = 900                         # editions written per day (LunaRoute is free, this only bounds a runaway queue)
_WANT_L = []                                 # (slug, lang) asked for by a page view
_FAILED_L = {}                               # (slug, lang) -> time of the last failure (retried after an hour)
_DONE_TODAY = {"day": "", "n": 0}


def _bump():
    d = time.strftime("%Y-%m-%d")
    if _DONE_TODAY["day"] != d:
        _DONE_TODAY.update(day=d, n=0)
    _DONE_TODAY["n"] += 1


def _cap_left():
    d = time.strftime("%Y-%m-%d")
    return _DONE_TODAY["day"] != d or _DONE_TODAY["n"] < LANG_DAILY_CAP


def wanted_langs(ch, chs):
    """UI languages a source's new articles are written in ahead of time: the language of the suite it belongs to (a German show gets a German
    edition) and the preferred language of the user who owns it. A US-suite show gets none: it already exists in English and Hebrew, and
    any other language is written the first time a reader opens an article in it (want_lang)."""
    out = set(pawed_i18n.ORDER)                           # every language: all articles are written in all languages
    for g in ch.get("geos") or []:
        if g in geo_suites.GEOS and g not in ("us", "il"):
            out.add(geo_suites.GEOS[g][4])
    if ch.get("owner_id"):
        try:
            l = va.get_vprefs(ch["owner_id"]).get("lang")
            if l:
                out.add(l)
        except Exception:
            pass
    return out & set(pawed_i18n.ORDER)


def _since():
    return max(TR_SINCE_MIN, time.strftime("%Y-%m-%d", time.localtime(time.time() - 3 * 86400)))


def _eligible(a):
    return bool(a.get("slug")) and (a.get("created") or "") >= _since()


def want_lang(slug, lang):
    """A page was requested in `lang` for an article without that edition: do it next (recent articles only)."""
    if lang not in pawed_i18n.ORDER:
        return
    with _LOCK:
        if (slug, lang) not in _WANT_L and len(_WANT_L) < 300:
            _WANT_L.append((slug, lang))


def _native(a, lang):
    """The episode itself is in `lang`: write the edition straight from the original transcript. -> edition dict or None."""
    try:
        with open(os.path.join(va.TR_DIR, (a.get("vid") or "") + ".json"), encoding="utf-8") as f:
            tr = json.load(f)
    except Exception:
        return None
    text = tr.get("transcript") or ""
    if not text:
        return None
    name = LANG_NAME[lang]
    dur, title, channel = tr.get("duration"), tr.get("title") or a.get("src_title") or "", tr.get("channel") or a.get("channel") or ""
    data = None
    for retry in (False, True):
        prompt = va._text_prompt_en(title, channel, dur, text, retry).replace("(names in their original English spelling)", "(names in their usual spelling)")
        prompt = prompt.replace("English", name).replace("he said", "he said (in " + name + ")").replace("according to her", "according to her (in " + name + ")")
        if tr.get("description"):
            prompt += "\n\nVIDEO DESCRIPTION (use for names and context):\n" + tr["description"][:2500]
        data, _tok, _fin, _used = va._write_text(a.get("vid") or "", prompt)
        if va._ts_ok(data, dur):
            break
    fin = va._finalize(data, dur, {})
    return {"title": fin["title"], "standfirst": fin["standfirst"], "lead": fin["lead"], "key_points": fin["key_points"], "blocks": fin["blocks"],
            "original": True, "native": True}


def _from_english(a, lang):
    """Translate the article's English edition (or its Hebrew text when there is none) into `lang`, keeping timestamps, types and speakers."""
    src_art, has_en = vidsum_render._overlay_en(a)
    out = _translated(_payload(src_art), LANG_NAME[lang], f"{a.get('slug')}/{lang}", frm="English" if has_en else "Hebrew")
    blocks = []
    for orig, t in zip(src_art["blocks"], out["blocks"]):
        nb = dict(orig)
        nb["text"] = t["text"]
        if orig.get("speaker") is not None and t["speaker"]:
            nb["speaker"] = t["speaker"]
        if orig.get("items"):
            nb["items"] = t["items"]
        blocks.append(nb)
    return {"title": out["title"], "standfirst": out["standfirst"], "lead": out["lead"] or out["standfirst"], "key_points": out["key_points"],
            "blocks": blocks, "original": True}


def translate_lang(slug, lang):
    key = f"{slug}/{lang}"
    with _LOCK:
        if key in _BUSY:
            return False
        _BUSY.add(key)
    try:
        a = _load(slug)
        if not a or (a.get("tr") or {}).get(lang):
            return bool(a)
        with va.tok_ctx("translate", a.get("vid") or slug, None):
            ch = next((c for c in va._load_ch()["channels"] if c["id"] == a.get("source_id")), None)
            ed = _native(a, lang) if va.audio_lang(a, ch) == lang else None
            if ed is None:
                ed = _from_english(a, lang)
        ed.update(at=time.strftime("%Y-%m-%d %H:%M:%S"), model=va.LUNA_MODEL)
        with va.LOCK:
            cur = _load(slug)
            if not cur:
                return False
            cur.setdefault("tr", {})[lang] = ed
            va._write_article(cur)
        _bump()
        va.log(f"vidsum translate {slug} -> {lang} DONE")
        return True
    except Exception as e:
        _FAILED_L[(slug, lang)] = time.time()
        va.log(f"vidsum translate {slug} -> {lang} failed: {va._scrub(str(e))[:200]}")
        return False
    finally:
        with _LOCK:
            _BUSY.discard(key)


def _next_lang():
    if not _cap_left():
        return None
    with _LOCK:
        while _WANT_L:
            s, l = _WANT_L.pop(0)
            if f"{s}/{l}" not in _BUSY:
                return s, l
    chs = va._load_ch()["channels"]
    chmap = {c["id"]: c for c in chs}
    wl = {}
    for a in va._article_index():                             # newest first; the English edition must exist (it is the source)
        if not _eligible(a) or not a.get("en"):
            continue
        sid = a.get("source_id")
        if sid not in wl:
            wl[sid] = wanted_langs(chmap.get(sid) or {}, chs)
        for l in sorted(wl[sid]):
            if not (a.get("tr") or {}).get(l) and f"{a['slug']}/{l}" not in _BUSY and time.time() - _FAILED_L.get((a["slug"], l), 0) > 3600:
                return a["slug"], l
    return None


def pending_langs():
    chs = va._load_ch()["channels"]
    chmap = {c["id"]: c for c in chs}
    n = 0
    for a in va._article_index():
        if _eligible(a) and a.get("en"):
            n += sum(1 for l in wanted_langs(chmap.get(a.get("source_id")) or {}, chs) if not (a.get("tr") or {}).get(l))
    return n


_FAILED_H = {}
H_BATCH = 10


def _head_src(a):
    en = a.get("en") or {}
    return (en.get("title") or a.get("title") or "", en.get("lead") or en.get("standfirst") or a.get("lead") or a.get("standfirst") or "")


def headline_pending():
    out = []
    for a in va._article_index():                          # newest first
        if not a.get("slug") or not (a.get("title") or "").strip():
            continue
        have = set(a.get("trh") or {}) | set((a.get("tr") or {}))
        if set(pawed_i18n.ORDER) - have and time.time() - _FAILED_H.get(a["slug"], 0) > 3600:
            out.append(a)
    return out


def headline_batch():
    """Titles and leads in every language for H_BATCH articles in ONE model call (cheap): lists, search and the Index are then fully localized,
    the body of an article is written only when it is opened (or by the eager window above). -> number of articles done."""
    todo = headline_pending()[:H_BATCH]
    if not todo:
        return 0
    items = {str(i): dict(zip(("title", "lead"), _head_src(a))) for i, a in enumerate(todo)}
    langs = ", ".join(f"{k} ({LANG_NAME[k]})" for k in pawed_i18n.ORDER)
    prompt = ("Translate the title and lead of each news item below into these languages: " + langs + ". Natural, fluent news-site wording; "
              "keep names and numbers exact; never use the ASCII double-quote character inside a string value.\n"
              "Return ONLY one JSON object: {\"<item id>\": {\"de\": {\"title\": \"...\", \"lead\": \"...\"}, \"fr\": {...}, ...}, ...} covering every item id and every language.\n\n"
              + json.dumps(items, ensure_ascii=False))
    try:
        res, _tok, _stop = va._luna(prompt, max_tokens=24000)
    except Exception as e:
        for a in todo:
            _FAILED_H[a["slug"]] = time.time()
        va.log(f"vidsum headlines batch failed: {va._scrub(str(e))[:200]}")
        return 0
    done = 0
    nd = va.vidsum_render.nodash
    for i, a in enumerate(todo):
        got = (res or {}).get(str(i)) if isinstance(res, dict) else None
        add = {}
        if isinstance(got, dict):
            for l in pawed_i18n.ORDER:
                e = got.get(l)
                if isinstance(e, dict) and str(e.get("title") or "").strip():
                    add[l] = {"title": nd(str(e["title"])).strip(), "lead": nd(str(e.get("lead") or "")).strip()}
        if not add:
            _FAILED_H[a["slug"]] = time.time()
            continue
        with va.LOCK:
            cur = _load(a["slug"])
            if cur:
                cur.setdefault("trh", {}).update({l: v for l, v in add.items() if l not in cur["trh"]})
                va._write_article(cur)
                done += 1
    va.log(f"vidsum headlines: {done}/{len(todo)} articles")
    return done


def loop():
    time.sleep(240)
    while True:
        try:
            if headline_batch():                              # cheap: titles + leads in every language, 10 articles per call
                time.sleep(3)
                continue
            sl = _next_lang()                                 # language editions first: they are the demand-driven, newest-first work
            if sl:
                translate_lang(*sl)
                time.sleep(3)
                continue
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
