"""Golden moments: the segments of an episode a person would clip and share (a punchline, a blunt claim, a sharp exchange).

Experiment 2026-11-27: 33 model picks over 5 Hebrew episodes, rated by the owner: 20 "I would clip it", 9 meh, 1 no. Debate exchanges and punchlines
passed most often, "sharp turn" and "insight" least, and the model's own score did not predict the rating, so ranking here uses the kind.

Admin-only for now: the section shows on an article page only for an admin, and gems are generated on demand (admin endpoint) unless
VIDSUM_GEMS_AUTO=1, which also lets a background loop do recent articles (capped per day).
"""
import json, os, re, threading, time

import vidsum_articles as va

GEMS_AUTO = os.environ.get("VIDSUM_GEMS_AUTO", "0") == "1"
GEMS_DAILY_CAP = int(os.environ.get("VIDSUM_GEMS_DAILY_CAP", "40"))
CHUNK_SEC = 20 * 60                      # long episodes are read in 20 minute windows (LunaRoute returned an empty reply on 30 minute ones) so the gems spread over the whole conversation
KEEP = 10
KIND_BONUS = {"debate_exchange": 0.5, "punchline": 0.5, "blunt_claim": 0.3, "story": 0.0, "emotional": 0.0, "sharp_turn": -1.0, "insight": -1.5}
_BUSY = set()
_LAST = {}                               # slug -> outcome of the last run (admin endpoint shows it)
_DAY = {"day": "", "n": 0}
_LOCK = threading.Lock()


def _ts(s):
    p = [int(x) for x in re.findall(r"\d+", str(s))]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1] if len(p) == 2 else (p[0] if p else None)


def _chunks(transcript):
    """-> [(start_sec, text)]: the transcript cut into windows at line boundaries; each line starts with its [m:ss] timestamp."""
    lines = re.findall(r"(?m)^(\[[\d:]+\].*)$", transcript) or transcript.splitlines()
    out, cur, t0 = [], [], None
    for ln in lines:
        m = re.match(r"\[([\d:]+)\]", ln)
        t = _ts(m.group(1)) if m else None
        if t is not None and t0 is None:
            t0 = t
        if t is not None and t0 is not None and t - t0 >= CHUNK_SEC and cur:
            out.append((t0, "\n".join(cur)))
            cur, t0 = [], t
        cur.append(ln)
    if cur:
        tail = "\n".join(cur)
        if out and len(tail) < 3000:                          # a sliver at the end belongs to the window before it
            out[-1] = (out[-1][0], out[-1][1] + "\n" + tail)
        else:
            out.append((t0 or 0, tail))
    return out


def _prompt(title, channel, lang_name, text, n, t0, last):
    return (
        f"You find the golden moments of a podcast episode: the moments a person would clip and post on social media.\n"
        f"Show: {channel}\nEpisode: {title}\nLanguage of the transcript: {lang_name}.\n"
        "Real listeners pick SHORT, sharp moments (5 to 45 seconds): a punchline, a devastating line inside an argument, a blunt claim, "
        "a sharp exchange between speakers, a sudden reversal. Prefer moments that stand on their own.\n"
        f"The transcript below is one window of the episode (it starts at {t0 // 60}:{t0 % 60:02d}{', and it is the end of the episode' if last else ''}). "
        "It is speech recognition with word errors: infer the intended words, but quote as written. Each line starts with its timestamp.\n"
        f"Return JSON only: {{\"gems\": [ ... ]}} with up to {n} gems in this window (fewer if there are not that many real ones; never pad). Each gem:\n"
        "- core_start, core_end: the tight moment, in SECONDS from the start of the episode (integers); 5 to 45 seconds; core_end is the timestamp of the line after the last line.\n"
        "- context_start, context_end: a wider window in seconds (up to 120 seconds) that adds the setup a viewer needs.\n"
        f"- title: punchy headline of 4 to 9 words in {lang_name}; title_en: the same in English.\n"
        "- kind: one of punchline | debate_exchange | blunt_claim | story | emotional | sharp_turn | insight\n"
        "- speaker_role: host | guest | caller | unknown\n"
        "- score: 1 to 10\n- why: one English sentence\n"
        "- excerpt: the core, verbatim, as written in the transcript\n"
        "- risk: null, or one short English line if it is an accusation about a named person, sensitive, or easy to misread out of context.\n"
        "Include moments from heated or argumentative stretches. Never use the ASCII double quote inside a string value.\n\nTRANSCRIPT:\n" + text)


def _clean(g, dur):
    try:
        cs, ce = _ts(g.get("core_start")), _ts(g.get("core_end"))
        xs, xe = _ts(g.get("context_start")), _ts(g.get("context_end"))
        if cs is None or ce is None or ce <= cs:
            return None
        if ce - cs < 10:                                       # a one or two second 'gem' is a transcript artifact, not a clip
            return None
        xs = cs if xs is None else min(xs, cs)
        xe = ce if xe is None else max(xe, ce)
        if dur and cs > dur + 60:
            return None
        ce = min(ce, cs + 90)                                  # a core is a clip, not a chapter
        kind = str(g.get("kind") or "story")
        s = float(g.get("score") or 5)
        rk = s + KIND_BONUS.get(kind, 0.0)
        return {"cs": cs, "ce": ce, "xs": xs, "xe": min(xe, xs + 150), "t": str(g.get("title") or "")[:140], "te": str(g.get("title_en") or "")[:140],
                "k": kind, "r": str(g.get("speaker_role") or "unknown"), "s": s, "rk": round(rk, 2), "why": str(g.get("why") or "")[:240],
                "ex": str(g.get("excerpt") or "")[:500], "risk": (str(g["risk"])[:200] if g.get("risk") else None)}
    except (TypeError, ValueError):
        return None


def _pick(gems):
    """Highest rank first, no two gems overlapping."""
    out = []
    for g in sorted(gems, key=lambda g: -g["rk"]):
        if all(g["ce"] <= o["cs"] or g["cs"] >= o["ce"] for o in out):
            out.append(g)
        if len(out) >= KEEP:
            break
    return sorted(out, key=lambda g: g["cs"])


def _load_tr(vid):
    try:
        with open(os.path.join(va.TR_DIR, vid + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _full_article(slug):
    with open(os.path.join(va.ART_DIR, slug + ".json"), encoding="utf-8") as f:
        return json.load(f)


def extract(slug):
    """Generate and store the gems of one article. -> (ok, message)"""
    ok, msg = _extract(slug)
    _LAST[slug] = {"ok": ok, "msg": msg, "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    return ok, msg


def _extract(slug):
    with _LOCK:
        if slug in _BUSY:
            return False, "already running"
        _BUSY.add(slug)
    try:
        a = _full_article(slug)
        tr = _load_tr(a.get("vid") or "")
        if not tr or not (tr.get("transcript") or "").strip():
            return False, "no stored transcript"
        langs = va.LANG_NAMES
        al = va.audio_lang(a, None) or "he"
        lang_name = langs.get(al, "Hebrew" if al == "he" else "English")
        dur = int(tr.get("duration") or 0)
        chunks = _chunks(tr["transcript"])
        per = 5 if len(chunks) > 1 else 8
        allg, errs = [], []
        for i, (t0, text) in enumerate(chunks):
            try:
                res, _tok, _stop = va._luna(_prompt(a.get("title") or "", a.get("channel") or "", lang_name, text, per, t0, i == len(chunks) - 1), max_tokens=24000)
            except Exception as e:                              # one bad window does not lose the others
                errs.append(f"window {i}: {va._scrub(str(e))[:120]}")
                continue
            for g in (res.get("gems") or []) if isinstance(res, dict) else []:
                c = _clean(g, dur)
                if c:
                    allg.append(c)
        if not allg:
            return False, "no gems: " + "; ".join(errs)[:300]
        gems = _pick(allg)
        with va.LOCK:
            cur = _full_article(slug)
            cur["gems"] = gems
            cur["gems_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            va._write_article(cur)
        return True, f"{len(gems)} gems from {len(allg)} candidates in {len(chunks)} window(s)" + (f"; {len(errs)} window(s) failed" if errs else "")
    except Exception as e:
        va.log(f"vidsum gems failed for {slug}: {va._scrub(str(e))[:200]}")
        return False, str(e)[:200]
    finally:
        with _LOCK:
            _BUSY.discard(slug)


def _fmt(s):
    h, m, c = s // 3600, s % 3600 // 60, s % 60
    return f"{h}:{m:02d}:{c:02d}" if h else f"{m}:{c:02d}"


_CSS = ("<style>.gems{margin:28px 0;padding:16px 18px;border:2px dashed #6d3fc9;border-radius:10px;background:rgba(109,63,201,.06)}"
        ".gems h3{margin:0 0 2px}.gems .gl{font-size:13px;opacity:.7;margin:0 0 10px}.gems .g{padding:12px 0;border-top:1px solid rgba(128,128,128,.25)}"
        ".gems .gt{font-weight:700;font-size:17px}.gems .gm{font-size:13px;opacity:.75;margin:4px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center}"
        ".gems .gm span{border:1px solid rgba(128,128,128,.4);border-radius:999px;padding:0 8px}.gems .gx{margin:6px 0;font-size:15px;opacity:.92}"
        ".gems .gr{font-size:13px;color:#c2410c}.gems a.go{font-weight:700}</style>")


def section_html(a, lang="he"):
    """The admin-only Golden moments block (empty when the article has none)."""
    import html as H
    gems = a.get("gems") or []
    if not gems:
        return ""
    e = H.escape
    nd = va.vidsum_render.nodash
    he = lang == "he"
    yt = a.get("kind") != "rss" and re.fullmatch(r"[\w-]{11}", a.get("vid") or "")
    rows = []
    for g in gems:
        title = g["t"] if he and g.get("t") else (g.get("te") or g.get("t"))
        link = (f'<a class="go" href="https://www.youtube.com/watch?v={e(a["vid"])}&amp;t={g["cs"]}s" target="_blank" rel="noopener">&#9654; {e(_fmt(g["cs"]))}</a>'
                if yt else f'<span>at {e(_fmt(g["cs"]))} in the episode</span>')
        rows.append(f'<div class="g"><div class="gt">{e(nd(title))}</div><div class="gm"><span>{e(_fmt(g["cs"]))} to {e(_fmt(g["ce"]))}</span>'
                    f'<span>{e(g["k"].replace("_", " "))}</span>{link}</div><div class="gx" dir="auto">{e(nd(g["ex"]))}</div>'
                    + (f'<div class="gr">{e(nd(g["risk"]))}</div>' if g.get("risk") else "") + "</div>")
    return (_CSS + '<section class="gems"><h3>Golden moments</h3><p class="gl">Admin preview. Picked by a model, not checked by a person.</p>'
            + "".join(rows) + "</section>")


def pending_recent(limit=10):
    out = []
    since = time.strftime("%Y-%m-%d", time.localtime(time.time() - 3 * 86400))
    for a in va._article_index():
        if (a.get("created") or "") >= since and not a.get("gems") and a.get("blocks") and a.get("vid") and os.path.exists(os.path.join(va.TR_DIR, a["vid"] + ".json")):
            out.append(a["slug"])
            if len(out) >= limit:
                break
    return out


def _loop():
    time.sleep(600)
    while True:
        try:
            d = time.strftime("%Y-%m-%d")
            if _DAY["day"] != d:
                _DAY.update(day=d, n=0)
            if _DAY["n"] < GEMS_DAILY_CAP:
                todo = pending_recent(1)
                if todo:
                    _DAY["n"] += 1
                    extract(todo[0])
                    time.sleep(5)
                    continue
        except Exception as e:
            va.log(f"vidsum gems loop error: {str(e)[:200]}")
        time.sleep(300)


def start():
    if GEMS_AUTO:
        threading.Thread(target=_loop, daemon=True).start()
