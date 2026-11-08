"""Pawed Index (אינדקס): a searchable A-Z map of everything the articles mention.

Per article (stored in the article JSON under "ent", computed once, newest first, by a background loop):
  kw      keywords: the article's own words minus stop-words (Hebrew + English + common European), no model needed
  people  [{en, he, role}] persons named in the episode: host / guest / mentioned (LunaRoute extraction)
  orgs    [{en, he}] company and brand names (LunaRoute extraction)
The index itself is built from those fields plus the podcast / episode names and the catalog's hosts, cached until the article files change, and
filtered per viewer (private sources stay private) when it is served.
"""
import json
import re
import threading
import time
import unicodedata

import vidsum_articles as va

ENT_V = 1
_NIQQUD = re.compile(r"[֑-ׇ]")
_TOK = re.compile(r"[^\W\d_]{3,}", re.U)

STOP = set("""
את של על עם זה זאת הוא היא הם הן אני אנחנו אנו אתה את אתם אתן לא כי אם או גם כל מה מי איך למה אבל רק עוד יש אין היה היתה היו להיות יהיה שלא כך לכן כמו בין אחרי לפני תוך דרך מול אל אצל עד כבר אז פה שם כאן הזה הזאת האלה אלה אלו ואת אותו אותה אותם אותן שלו שלה שלהם שלהן לו לה להם להן בו בה בהם ממנו ממנה יותר פחות מאוד די כן ככל כפי לדברי לדבריו לדבריה לטענתו לטענתה לפי וכן אולם אך האם מספר שנה שנים אחד אחת שני שתי שלוש עוד עצמו עצמה אמר אמרה אומר אומרת מסביר מסבירה טוען טוענת לדעתו לדעתה כלומר בעצם למשל כמה הרבה קצת בכל מכל לכל וגם ועוד אבל אפילו כאשר כשהוא כשהיא שהוא שהיא שהם מתוך אודות בנוגע ביחס לגבי עבור בשביל בזכות למרות בגלל אצלו אצלה אלא מדובר דובר מדברים מדבר מדברת הפרק הפודקאסט הסיכום פרק פודקאסט אורח אורחת מנחה מנחים מארח מארחת ציין ציינה הדגיש הדגישה הוסיף הוסיפה לדבריהם טענו טוענים מסביר הסביר הסבירה
the and for are but not you all can had her was one our out has have his how its may new now old see two way who did get him let she too use that this with from they will would there their what about which when were been more some into than then them these those your just like over also only very such here most other after before because while where being each other make made said says say say according
und der die das ist nicht ein eine einen auch mit von für auf den dem des sich als aber wie wir sie ich oder bei zum zur noch nur wird sind war hat dass
le la les des une est pas pour dans que qui sur avec par plus mais ont sont cette ces aux
el los las una por con para del que como más pero sus sus este esta esto son fue
 não uma para com por mais dos das mas como foi são
il lo gli una per con che non sono più del della dei alla
het een van dat dit niet zijn voor met als maar ook door naar
""".split())


def _clean(s):
    s = _NIQQUD.sub("", s or "")
    return s.replace("״", "").replace("׳", "").replace("'", "").replace("’", "").replace('"', " ")


def tokens(text):
    return [w for w in _TOK.findall(_clean(text).lower()) if w not in STOP and not w.startswith("http")]


def _body_text(a):
    parts = []
    for b in a.get("blocks") or []:
        parts.append(b.get("text") or "")
        parts.extend(b.get("items") or [])
    return "\n".join(parts)


def keywords_of(a, top=14):
    """Top words of one article, titles and key points weighted up; both the Hebrew text and the English edition when it exists."""
    cnt = {}
    def add(text, w):
        for t in tokens(text):
            cnt[t] = cnt.get(t, 0) + w
    add(a.get("title"), 4)
    add(a.get("standfirst"), 2)
    for k in a.get("key_points") or []:
        add(k, 2)
    add(_body_text(a), 1)
    en = a.get("en") or {}
    if en:
        add(en.get("title"), 4)
        add(en.get("standfirst"), 2)
        for k in en.get("key_points") or []:
            add(k, 2)
        add(_body_text(en), 1)
    ranked = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, c in ranked[:top] if c >= 3]


def _prompt(a):
    txt = (_body_text(a))[:3500]
    src = {"podcast": a.get("channel") or "", "episode_title": a.get("src_title") or "", "title": a.get("title") or "", "standfirst": a.get("standfirst") or "",
           "key_points": a.get("key_points") or [], "text": txt}
    return ("From this article (a written summary of a podcast or video episode, usually in Hebrew) list the PERSONS and the COMPANIES named in it.\n"
            "- people: real named individuals only (never roles like 'the minister'). en = the full name in its usual English spelling (Elon Musk), "
            "he = the same name in Hebrew as the article writes it (אילון מאסק), empty string if the article is not Hebrew. "
            "role = \"host\" if this person hosts or interviews on the show, \"guest\" if interviewed or a main speaker, else \"mentioned\".\n"
            "- orgs: companies, brands and startups only (Tesla, Google, Wix). Not countries, cities, parties, armies, ministries or media outlets of the podcast itself. "
            "en = usual English name, he = Hebrew as written or empty.\n"
            "At most 20 people and 20 orgs, the most important first. Never invent; skip anything uncertain. Output ONLY one valid JSON object, no markdown, "
            "never use the ASCII double-quote character inside a string value. Shape: "
            '{"people":[{"en":"","he":"","role":"host|guest|mentioned"}],"orgs":[{"en":"","he":""}]}\n\nARTICLE:\n' + json.dumps(src, ensure_ascii=False))


def _norm_list(res):
    def s(x):
        return re.sub(r"\s+", " ", str(x or "")).strip()[:80]
    people, orgs = [], []
    for p in (res.get("people") or [])[:25]:
        if isinstance(p, dict) and (s(p.get("en")) or s(p.get("he"))):
            role = p.get("role") if p.get("role") in ("host", "guest", "mentioned") else "mentioned"
            people.append({"en": s(p.get("en")), "he": s(p.get("he")), "role": role})
    for o in (res.get("orgs") or [])[:25]:
        if isinstance(o, dict) and (s(o.get("en")) or s(o.get("he"))):
            orgs.append({"en": s(o.get("en")), "he": s(o.get("he"))})
    return people, orgs


def process_kw(slug):
    """Keywords only (no model): cheap, runs for the whole archive first so the index fills in minutes."""
    import os
    with open(os.path.join(va.ART_DIR, slug + ".json"), encoding="utf-8") as f:
        a = json.load(f)
    prev = a.get("ent") or {}
    a["ent"] = dict(prev, v=prev.get("v") or ENT_V, kw=keywords_of(a), people=prev.get("people") or [], orgs=prev.get("orgs") or [], llm=bool(prev.get("llm")),
                    at=time.strftime("%Y-%m-%d %H:%M:%S"))
    va._write_article(a)


def process(slug):
    """Compute and store 'ent' for one article. Keywords always; people/orgs through LunaRoute (kept as [] + 'llm': False if the call fails, retried later)."""
    import os
    path = os.path.join(va.ART_DIR, slug + ".json")
    with open(path, encoding="utf-8") as f:
        a = json.load(f)
    prev = a.get("ent") or {}
    ent = {"v": ENT_V, "kw": keywords_of(a), "people": prev.get("people") or [], "orgs": prev.get("orgs") or [], "llm": bool(prev.get("llm")),
           "at": time.strftime("%Y-%m-%d %H:%M:%S")}               # a failed model call never wipes what an earlier run found
    err = ""
    if a.get("blocks") or a.get("key_points"):
        try:
            res, _tok, _stop = va._luna(_prompt(a), max_tokens=3000)
            ent["people"], ent["orgs"] = _norm_list(res)
            ent["llm"] = True
        except Exception as e:
            err = str(e)
            va.log(f"index entities {slug}: {err[:160]}")
    a["ent"] = ent
    va._write_article(a)
    return ent, err


_FAILED = {}
_BUSY = set()
_LOCK = threading.Lock()
RETRY_S = 3600


_BACKOFF = {"until": 0.0}


def pending(kw_only=False):
    """Slugs still to do (newest release first). kw_only: those without keywords yet. Otherwise: those without model-extracted people/companies, skipping failures of the last hour."""
    now = time.time()
    out = []
    for a in va._article_index():
        e = a.get("ent")
        if kw_only:
            if not e or "kw" not in e:
                out.append(a["slug"])
            continue
        if e and e.get("v") == ENT_V and e.get("llm"):
            continue
        if now - _FAILED.get(a["slug"], 0) < RETRY_S:
            continue
        out.append(a["slug"])
    return out


def loop():
    time.sleep(90)
    while True:
        try:
            kw = pending(kw_only=True)
            if kw:                                           # phase 1: keywords for everything, no model, a few per second
                for s in kw[:40]:
                    try:
                        process_kw(s)
                    except Exception as e:
                        va.log(f"index keywords {s}: {str(e)[:120]}")
                    time.sleep(0.2)
                continue
            if time.time() < _BACKOFF["until"]:
                time.sleep(30)
                continue
            todo = pending()[:1]                              # phase 2: people + companies, one at a time (LunaRoute has a concurrent-request limit shared with the article writer)
            if not todo:
                time.sleep(300)
                continue
            slug = todo[0]
            try:
                ent, err = process(slug)
                if not ent["llm"]:
                    _FAILED[slug] = time.time()
                if "429" in err or "CONCURRENT" in err:
                    _BACKOFF["until"] = time.time() + 180   # LunaRoute is busy: leave it alone for 3 minutes
            except Exception as e:
                _FAILED[slug] = time.time()
                va.log(f"index process {slug}: {str(e)[:160]}")
            time.sleep(6)
        except Exception as e:
            va.log(f"index loop error: {str(e)[:160]}")
            time.sleep(120)


def start():
    threading.Thread(target=loop, daemon=True).start()


# ------------------------------------------------------------------ the index ---
_C = {"sig": None, "data": None}

TAGS = {
    "en": {"host": "Podcast Host", "guest": "Guest", "mentioned": "Persona mentioned", "company": "Company mentioned", "keyword": "Keyword",
           "podcast": "Podcast", "episode": "Episode"},
    "he": {"host": "מנחה הפודקאסט", "guest": "אורח", "mentioned": "אישיות שהוזכרה", "company": "חברה שהוזכרה", "keyword": "מילת מפתח",
           "podcast": "פודקאסט", "episode": "פרק"},
}


def _key(name):
    s = unicodedata.normalize("NFKC", name or "").lower()
    s = re.sub(r"\b(dr|prof|mr|mrs|ms|sir)\.?\s", "", s)
    return re.sub(r"[^\w֐-׿ ]", "", s).strip()


def _hosts_by_podcast():
    try:
        import podscanner
        return {r["_n"]: [h for h in (r.get("hosts") or []) if isinstance(h, str)] for r in podscanner._catalog() if r.get("hosts")}, podscanner._nname
    except Exception:
        return {}, (lambda n: re.sub(r"[^\w]", "", n or "").lower())


def build():
    """entries: id -> {kinds:set, en, he, slugs:set}. Cached on the article index signature (any new or edited article rebuilds)."""
    items = va._article_index()
    sig = (len(items), max((a.get("created") or "" for a in items), default=""), sum(1 for a in items if (a.get("ent") or {}).get("llm")))
    if _C["sig"] == sig and _C["data"] is not None:
        return _C["data"]
    E = {}
    def ent(eid, kind, en, he=""):
        e = E.get(eid)
        if not e:
            e = E[eid] = {"id": eid, "kinds": set(), "en": en, "he": {}, "slugs": set()}
        e["kinds"].add(kind)
        if he:
            e["he"][he] = e["he"].get(he, 0) + 1
        return e
    hosts, nname = _hosts_by_podcast()
    kwdf = {}
    for a in items:
        for w in (a.get("ent") or {}).get("kw") or []:
            kwdf[w] = kwdf.get(w, 0) + 1
    def canon(w):                                   # Hebrew one-letter prefixes (the, and, in, to, from, that, as): ובינה / הבינה -> בינה when the bare word is common
        if len(w) > 4 and w[0] in "והבלמשכ" and kwdf.get(w[1:], 0) >= 3:
            return w[1:]
        return w
    n = max(1, len(items))
    for a in items:
        slug = a["slug"]
        e = a.get("ent") or {}
        for p in e.get("people") or []:
            k = _key(p.get("en") or p.get("he"))
            if k:
                ent("p:" + k, p["role"], p.get("en") or p.get("he"), p.get("he") or "")["slugs"].add(slug)
        for o in e.get("orgs") or []:
            k = _key(o.get("en") or o.get("he"))
            if k:
                ent("c:" + k, "company", o.get("en") or o.get("he"), o.get("he") or "")["slugs"].add(slug)
        for w in {canon(x) for x in e.get("kw") or []}:
            if 3 <= kwdf.get(w, 0) <= max(8, n * 0.35):
                ent("k:" + w, "keyword", w)["slugs"].add(slug)
        ch = (a.get("channel") or "").strip()
        if ch:
            ent("s:" + _key(ch), "podcast", ch)["slugs"].add(slug)
            for h in hosts.get(nname(ch), []):
                ent("p:" + _key(h), "host", h)["slugs"].add(slug)
        t = (a.get("title") or "").strip()
        ten = ((a.get("en") or {}).get("title") or "").strip()
        if t:
            ent("e:" + slug, "episode", ten or t, t)["slugs"].add(slug)
    # a bare surname / first name is the same person as the single full name that ends or starts with it ("Levinson" -> "Haim Levinson")
    people = [k for k in E if k.startswith("p:")]
    for k in people:
        w = k[2:]
        if " " in w or k not in E:
            continue
        full = [o for o in people if o != k and o in E and " " in o[2:] and (o[2:].split()[-1] == w or o[2:].split()[0] == w)]
        if len(full) == 1:
            t = E[full[0]]
            t["kinds"] |= E[k]["kinds"]
            t["slugs"] |= E[k]["slugs"]
            for h, c in E[k]["he"].items():
                t["he"][h] = t["he"].get(h, 0) + c
            del E[k]
    names = set()
    for k, e in E.items():
        if k[0] in "pc":
            names.add(e["en"].lower())
            names |= {h.lower() for h in e["he"]}
    for k in [k for k in E if k[0] == "k" and E[k]["en"].lower() in names]:
        del E[k]                                      # a keyword that is just a person's or company's name is listed once, as that person or company
    _C["sig"], _C["data"] = sig, E
    return E


def entries_for(visible, lang):
    """Light list for the page: [{id, l: label, a: other-language name for search, t: [tag names], n: count of visible articles}] sorted A-Z."""
    he = lang == "he"
    T = TAGS["he" if he else "en"]
    rank = ["host", "guest", "mentioned", "company", "keyword", "podcast", "episode"]
    out = []
    for e in build().values():
        n = len(e["slugs"] & visible)
        if not n:
            continue
        hebrew = max(e["he"], key=e["he"].get) if e["he"] else ""
        label, alt = (hebrew or e["en"], e["en"]) if he else (e["en"], hebrew)
        if e["id"].startswith("e:"):
            label, alt = (hebrew or e["en"], e["en"]) if he else (e["en"] or hebrew, hebrew)
        tags = [T[k] for k in rank if k in e["kinds"]]
        out.append({"id": e["id"], "l": label, "a": alt if alt != label else "", "t": tags, "n": n})
    out.sort(key=lambda x: (x["l"].lower()))
    return out


def articles_of(eid, visible):
    e = build().get(eid)
    if not e:
        return None, []
    return e, [s for s in e["slugs"] if s in visible]


def host_of(channel):
    hosts, nname = _hosts_by_podcast()
    return ", ".join(hosts.get(nname(channel), [])[:3])


def hosts_of(channel):
    """[{name, id}] for the article's podcast: the catalog's hosts (each links to its own index entry), else the podcast itself."""
    hosts, nname = _hosts_by_podcast()
    hs = hosts.get(nname(channel), [])[:3]
    if hs:
        return [{"name": h, "id": "p:" + _key(h)} for h in hs]
    return [{"name": channel, "id": "s:" + _key(channel)}] if channel else []
