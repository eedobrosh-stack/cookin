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


def moment_html(a, n, lang="he"):
    """Public page for one golden moment: headline, verbatim quote, the YouTube player started at the moment (embed, not hosted), the summary, and the way on to the article. -> html or None"""
    import html as H
    import urllib.parse
    gems = a.get("gems") or []
    if not (0 <= n < len(gems)):
        return None
    g = gems[n]
    e = H.escape
    nd = va.vidsum_render.nodash
    yt = a.get("kind") != "rss" and re.fullmatch(r"[\w-]{11}", a.get("vid") or "")
    he = lang == "he"
    title = nd(g["t"] if he and g.get("t") else (g.get("te") or g.get("t")))
    show = a.get("channel") or ""
    ep = nd(a.get("title") or "")
    art = "/vidsum/article/" + urllib.parse.quote(a["slug"])
    cs, ce = g["cs"], g["ce"]
    if yt:
        player = (f'<div class="pl"><iframe src="https://www.youtube-nocookie.com/embed/{e(a["vid"])}?start={cs}&amp;end={ce + 8}&amp;rel=0" '
                  f'title="{e(title)}" allow="accelerometer; encrypted-media; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>'
                  f'<p class="lk"><a href="https://www.youtube.com/watch?v={e(a["vid"])}&amp;t={cs}s" target="_blank" rel="noopener">&#9654; {e(_fmt(cs))} on YouTube</a></p>')
    else:
        player = f'<p class="lk">At {e(_fmt(cs))} in the episode.</p>'
    sub = a.get("subtitle") or ""
    desc = nd(g.get("ex") or title)[:200]
    url = f"https://pawed.io/moment/{urllib.parse.quote(a['slug'])}/{n}"
    css = ("<style>:root{--ink:#1c1b19;--muted:#6b665d;--bg:#faf8f3;--card:#fff;--line:#e4dfd3;--ac:#6d3fc9}"
           "@media(prefers-color-scheme:dark){:root{--ink:#ece9e1;--muted:#a39d92;--bg:#171614;--card:#1f1e1b;--line:#35332e;--ac:#a98bf0}}"
           "*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 system-ui,-apple-system,sans-serif}"
           ".w{max-width:680px;margin:0 auto;padding:20px 16px 48px}.k{font-size:13px;color:var(--muted);margin:0 0 14px}.k a{color:var(--ac);font-weight:700;text-decoration:none}"
           "h1{font-size:28px;line-height:1.25;margin:0 0 6px}.src{color:var(--muted);font-size:15px;margin:0 0 16px}"
           "blockquote{margin:0 0 18px;padding:14px 18px;background:var(--card);border-inline-start:4px solid var(--ac);border-radius:8px;font-size:19px}"
           ".pl{position:relative;padding-top:56.25%;border-radius:10px;overflow:hidden;background:#000}.pl iframe{position:absolute;inset:0;width:100%;height:100%;border:0}"
           ".lk{font-size:14px;margin:8px 0 22px}.lk a{color:var(--ac)}"
           ".sum{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:0 0 18px}.sum b{display:block;margin-bottom:4px}"
           ".more{display:inline-block;background:var(--ac);color:#fff;font-weight:700;padding:11px 20px;border-radius:999px;text-decoration:none}"
           ".sh{margin:18px 0 0}.sh button{font:inherit;font-size:15px;background:none;color:var(--ac);border:1px solid var(--ac);border-radius:999px;padding:8px 18px;cursor:pointer}"
           ".ft{margin-top:28px;font-size:13px;color:var(--muted)}</style>")
    head = (f'<!doctype html><html lang="{"he" if he else "en"}" dir="{"rtl" if he else "ltr"}"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
            f'<title>{e(title)} | Pawed</title><meta name="description" content="{e(desc)}">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:type" content="article"><meta property="og:url" content="{e(url)}"><meta property="og:image" content="{e(url)}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{e(url)}.png">'
            f'{css}</head><body><div class="w">')
    body = (f'<p class="k"><a href="/">Pawed</a> &middot; {e(show)}</p><h1>{e(title)}</h1><p class="src">{e(show)} &middot; {e(ep)}</p>'
            f'<blockquote dir="auto">{e(nd(g.get("ex") or ""))}</blockquote>{player}'
            + (f'<div class="sum"><b>{"על מה הפרק" if he else "About the episode"}</b>{e(nd(sub))}</div>' if sub else "")
            + f'<a class="more" href="{e(art)}">{"הסיכום המלא של הפרק" if he else "Read the full episode summary"} &rarr;</a>'
            f'<p class="sh"><button type="button" id="cp" data-u="{e(url)}">{"העתקת קישור" if he else "Copy link"}</button></p>'
            f'<p class="ft">{"המקטע נבחר אוטומטית ולא נבדק. הציטוט מתומלל אוטומטית ועלול להכיל שגיאות. הקול והווידאו שייכים ליוצרי הפודקאסט." if he else "This moment was picked automatically and not checked. The quote is machine transcribed and may contain errors. The audio and video belong to the podcast creators."}</p>'
            '</div><script>document.getElementById("cp").onclick=function(){var b=this,u=b.dataset.u;'
            'if(navigator.share){navigator.share({url:u}).catch(function(){});return}'
            'try{navigator.clipboard.writeText(u).then(function(){b.textContent="\\u2713"})}catch(e){prompt("",u)}}</script></body></html>')
    return head + body


_MIRROR = str.maketrans("()[]{}<>", ")(][}{><")


def _visual(s, base_dir="R"):
    """Logical text -> the order PIL must draw left to right. Right-to-left paragraphs only: Hebrew runs are reversed, Latin and number runs
    stay as they are, and the runs are laid out right to left. No library, so it behaves the same on every host."""
    if base_dir != "R":
        return s
    def cls(c):
        if "\u0590" <= c <= "\u05ff":
            return "R"
        return "L" if c.isalnum() else "N"
    cl = [cls(c) for c in s]
    for i, c in enumerate(cl):                              # neutrals take the direction around them when both sides agree, else the paragraph's (R);
        if c == "N":                                        # a separator inside a number (3,000 / 1.5 / 48-) stays with the number
            j = i - 1
            while j >= 0 and cl[j] == "N":
                j -= 1
            k = i + 1
            while k < len(cl) and cl[k] == "N":
                k += 1
            a, b = (cl[j] if j >= 0 else "R"), (cl[k] if k < len(cl) else "R")
            digits = j >= 0 and k < len(cl) and s[j].isdigit() and s[k].isdigit() and s[i] in ",.:/"
            cl[i] = "L" if (a == b == "L" and (digits or s[i] == " " and False)) else ("L" if a == b == "L" and s[i] != " " else ("R" if a != b or a == "R" else "L"))
    runs, cur, d = [], "", None
    for ch, c in zip(s, cl):
        if c != d and cur:
            runs.append((d, cur))
            cur = ""
        d = c
        cur += ch
    if cur:
        runs.append((d, cur))
    return "".join((r[::-1].translate(_MIRROR) if dd == "R" else r) for dd, r in reversed(runs))


_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts", "Heebo.ttf")


def _font(size, weight=b"Bold"):
    from PIL import ImageFont
    f = ImageFont.truetype(_FONT, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def card_png(a, n, lang="he"):
    """1200x630 share image for one moment (headline, quote, show). -> PNG bytes or None"""
    import io
    from PIL import Image, ImageDraw
    gems = a.get("gems") or []
    if not (0 <= n < len(gems)):
        return None
    g = gems[n]
    he = lang == "he"
    nd = va.vidsum_render.nodash
    title = nd(g["t"] if he and g.get("t") else (g.get("te") or g.get("t")))
    quote = nd(g.get("ex") or "")
    show = nd(a.get("channel") or "")
    from PIL import features
    raqm = features.check("raqm")                           # Pillow wheels on Linux ship libraqm, which does the bidi itself; without it we reorder ourselves
    get_display = (lambda s, **k: s) if raqm else _visual
    kw = {"direction": "rtl", "language": "he"} if (raqm and he) else {}

    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "#faf8f3")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 18, H], fill="#6d3fc9")
    pad, right = 70, W - 70
    maxw = W - 2 * pad

    def wrap(text, font, limit, lines_max):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font) <= limit:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if len(lines) > lines_max:
            lines = lines[:lines_max]
            lines[-1] = lines[-1].rstrip(" ,.;:") + "..."
        return lines

    def put(lines, font, y, fill, gap, inset=0):
        for ln in lines:
            vis = get_display(ln, base_dir="R" if he else "L")
            if he:
                d.text((right - inset, y), vis, font=font, fill=fill, anchor="ra", **kw)
            else:
                d.text((pad + inset, y), vis, font=font, fill=fill)
            y += gap
        return y

    d.text((right if he else pad, 46), "Pawed", font=_font(34, b"ExtraBold"), fill="#6d3fc9", anchor="ra" if he else "la")
    tf, qf = _font(64, b"ExtraBold"), _font(34, b"Regular")
    y = put(wrap(title, tf, maxw, 3), tf, 118, "#1c1b19", 78)
    y += 24
    qlines = wrap(quote, qf, maxw - 40, 5)
    d.rectangle([(right - 6) if he else pad, y, right if he else pad + 6, y + 44 * len(qlines)], fill="#6d3fc9")
    put(qlines, qf, y + 2, "#3d3a35", 44, inset=28)
    foot = _font(28, b"Medium")
    d.text((right if he else pad, H - 52), get_display(show, base_dir="R" if he else "L") + "  |  pawed.io", font=foot, fill="#6b665d",
           anchor="rs" if he else "ls", **kw)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return out.getvalue()
