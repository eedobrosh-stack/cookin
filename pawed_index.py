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


GENERIC = set("""
about above across actually almost along already always another anything around away back become before being believe best better between beyond big billion bit both bring call came cant case change come could course day days different does doing done down during each either end enough even ever every everyone everything example fact far feel few find first five four get getting give given going gone good got great group guy guys hand happen happened hard having help here high however hundred idea important including instead into itself job just keep kind know known last late least left less let level life like likely little live long look lot lots made make makes making man many matter maybe mean means might million moment money more most much must near need needs never new next nobody nothing number often old once ones only open others over own part people per percent perhaps person place play point possible probably problem put question quite rather real really reason right run same saying second see seem seems set several share short show since small some someone something sometimes soon start started still story such sure take taking talk talking tell than thing things think thinks though thought thousand three through time times today together told took top toward trillion try trying turn two under until upon use used using very view wait want wanted wants way ways week weeks well went what whether while whole whose why will within without work working world would year years yes yet young bet bets betting coalition cognitive comedians commitments committee community company compute computer congress consciousness conscription constitution content control conversation companies core
שנה שנים פרק מדובר למעשה כלל חלק דבר דברים אנשים אדם עניין מצב צורה סוג אופן תחום נושא שאלה תשובה בעיה סיפור זמן יום ימים שבוע חודש חודשים מאז עדיין בקרוב כיום היום אתמול מחר הרבה מעט גדול גדולה קטן קטנה חדש חדשה ראשון ראשונה אחרון אחרונה טוב טובה רע אפשר צריך צריכה יכול יכולה רוצה רוצים חושב חושבת מאמין מאמינה אומרים נראה נראית קורה קרה התברר מסתבר עשוי עשויה הנראה אכן בהחלט ממש פשוט בדיוק לגמרי כמעט אולי בטח תמיד פעם פעמים שוב כלומר למשל הנה זהו כזה כזאת כאלה איזה איזו מישהו משהו כלום שניים שלושה מיליון מיליארד אלף אחוז אחוזים דולר דולרים שקל שקלים כסף עולם מדינה חברה חברות ארגון
""".split())


# product/tech topics people discuss that are lowercase in text; never filtered as generic
KEEP_KW = set("codex claude gemini chatgpt copilot cursor sora grok llama mistral deepseek perplexity midjourney openai anthropic nvidia bitcoin ethereum blockchain crypto stablecoin starlink tesla waymo".split())


def _clean(s):
    s = _NIQQUD.sub("", s or "")
    return s.replace("״", "").replace("׳", "").replace("'", "").replace("’", "").replace('"', " ")


def tokens(text):
    return [w for w in _TOK.findall(_clean(text).lower()) if w not in STOP and w not in GENERIC and not w.startswith("http")]


def _body_text(a):
    parts = []
    for b in a.get("blocks") or []:
        parts.append(b.get("text") or "")
        parts.extend(b.get("items") or [])
    return "\n".join(parts)


def keywords_of(a, top=14):
    """Top words of one article, titles and key points weighted up; both the Hebrew text and the English edition when it exists.
    Returns (keywords, proper) where proper = those keywords that are capitalised in most of their Latin occurrences (names, brands, places)."""
    cnt, parts = {}, []
    def add(text, w):
        parts.append(text or "")
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
    kw = [w for w, c in ranked[:top] if c >= 3]
    tot, cap = {}, {}
    for m in re.finditer(r"[A-Za-z][A-Za-z]{2,}", _clean(" ".join(parts))):
        w = m.group().lower()
        tot[w] = tot.get(w, 0) + 1
        if m.group()[0].isupper():
            cap[w] = cap.get(w, 0) + 1
    return kw, [w for w in kw if tot.get(w) and cap.get(w, 0) / tot[w] >= 0.6]


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
    kw, kwp = keywords_of(a)
    a["ent"] = dict(prev, v=prev.get("v") or ENT_V, kw=kw, kwp=kwp, kwv=2, people=prev.get("people") or [], orgs=prev.get("orgs") or [], llm=bool(prev.get("llm")),
                    at=time.strftime("%Y-%m-%d %H:%M:%S"))
    va._write_article(a)


def process(slug):
    """Compute and store 'ent' for one article. Keywords always; people/orgs through LunaRoute (kept as [] + 'llm': False if the call fails, retried later)."""
    import os
    path = os.path.join(va.ART_DIR, slug + ".json")
    with open(path, encoding="utf-8") as f:
        a = json.load(f)
    prev = a.get("ent") or {}
    kw, kwp = keywords_of(a)
    ent = {"v": ENT_V, "kw": kw, "kwp": kwp, "kwv": 2, "people": prev.get("people") or [], "orgs": prev.get("orgs") or [], "llm": bool(prev.get("llm")),
           "at": time.strftime("%Y-%m-%d %H:%M:%S")}               # a failed model call never wipes what an earlier run found
    err = ""
    if a.get("blocks") or a.get("key_points"):
        try:
            res, _tok, _stop = va._luna(_prompt(a), max_tokens=12000)       # the reasoning model spends part of the budget thinking: 3000 left an empty reply on real articles
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
RETRY_S = 1200


_BACKOFF = {"until": 0.0}
_KW_LOCK = threading.Lock()


def pending(kw_only=False):
    """Slugs still to do (newest release first). kw_only: those without keywords yet. Otherwise: those without model-extracted people/companies, skipping failures of the last hour."""
    now = time.time()
    out = []
    for a in va._article_index():
        e = a.get("ent")
        if kw_only:
            if not e or "kw" not in e or (e.get("kwv") or 1) < 2:
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
            if kw:                                           # phase 1: keywords for everything, no model, a few per second (one worker at a time)
                if _KW_LOCK.acquire(blocking=False):
                    try:
                        for s in kw[:40]:
                            try:
                                process_kw(s)
                            except Exception as e:
                                va.log(f"index keywords {s}: {str(e)[:120]}")
                            time.sleep(0.2)
                    finally:
                        _KW_LOCK.release()
                else:
                    time.sleep(10)
                continue
            if time.time() < _BACKOFF["until"]:
                time.sleep(30)
                continue
            with _LOCK:
                todo = [x for x in pending() if x not in _BUSY][:1]
                if todo:
                    _BUSY.add(todo[0])
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
            finally:
                with _LOCK:
                    _BUSY.discard(slug)
            time.sleep(6)
        except Exception as e:
            va.log(f"index loop error: {str(e)[:160]}")
            time.sleep(120)


def start():
    threading.Thread(target=loop, daemon=True).start()
    threading.Thread(target=loop, daemon=True).start()           # a second worker: each model call takes 30-90 s


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
    # One name = one entry: a keyword that is a person's surname (or the whole name of a one-word company) joins that person / company, so
    # "נתניהו" the keyword (24 articles) and Benjamin Netanyahu the persona (2) become one entry holding all 26.
    tokidx = {}
    for k, e in E.items():
        if k[0] not in "pc":
            continue
        for nm in [e["en"]] + list(e["he"]):
            ws = [norm(w) for w in _words(nm)]
            ws = [w for w in ws if w]
            if not ws:
                continue
            keys = {ws[-1]} if k[0] == "p" else ({ws[0]} if len(ws) == 1 else set())
            for t in keys:
                if len(t) >= 3:
                    tokidx.setdefault(t, set()).add(k)
    capdf = {}
    for a in items:
        for w in (a.get("ent") or {}).get("kwp") or []:
            capdf[w] = capdf.get(w, 0) + 1
    for k in [k for k in E if k[0] == "k"]:
        cands = tokidx.get(norm(E[k]["en"]))
        if not cands:
            continue
        t = E[max(cands, key=lambda c: len(E[c]["slugs"]))]
        t["kinds"].add("keyword")
        t["slugs"] |= E[k]["slugs"]
        del E[k]
    # what is left of the keywords must be material: names / brands (capitalised in the text) always; ordinary English words only when long, rare and not generic; Hebrew words not generic and not everywhere
    for k in [k for k in E if k[0] == "k"]:
        w, df = E[k]["en"], len(E[k]["slugs"])
        latin = bool(re.match(r"[a-z]", w))
        if w in GENERIC:
            keep = False
        elif w in KEEP_KW:
            keep = True
        elif latin:
            keep = capdf.get(w, 0) >= 0.6 * df and df <= 40  # lowercase English words are never material; only names/brands
        else:
            keep = len(w) >= 4 and df <= 15  # Hebrew has no capitals: only rare, story-specific words
        if not keep:
            del E[k]
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


# ------------------------------------------------------------------ search ---
_HEB_SIMILAR = str.maketrans({"ט": "ת", "ק": "כ", "ע": "א", "ו": "", "י": ""})      # spellings that sound alike (אנטרופיק / אנתרופיק); matres lectionis dropped


def norm(s):
    """Match form of a word: lower case, no niqqud / quotes / hyphens, Latin 'ph' -> 'f', 'th' -> 't', Hebrew look-alike letters merged."""
    t = _NIQQUD.sub("", unicodedata.normalize("NFKC", s or "").lower())
    t = re.sub(r"[\u05f3\u05f4'\u2019\"\-_]", "", t)
    t = t.replace("ph", "f").replace("th", "t").replace("ck", "k")
    return t.translate(_HEB_SIMILAR)


_WORD = re.compile(r"[^\W_]+(?:['\u2019\u05f3\u05f4][^\W_]+)*", re.U)      # keeps ג׳מיני / don't in one piece


def _words(s):
    return _WORD.findall(s or "")


def _search_index():
    """normalised searchable text per entry + a vocabulary of normalised words (people, companies, keywords, podcasts) for spelling correction."""
    E = build()
    if _C.get("sx_sig") is _C["data"] and _C.get("sx"):
        return _C["sx"]
    texts, vocab = {}, {}
    for k, e in E.items():
        names = [e["en"]] + list(e["he"])
        t = " ".join(norm(n) for n in names)
        texts[k] = t
        if k[0] != "e":
            for n in names:
                for w in _words(n):
                    nw = norm(w)
                    if len(nw) >= 3:
                        vocab.setdefault(nw, w)
    _C["sx"], _C["sx_sig"] = (texts, vocab), _C["data"]
    return _C["sx"]


def _match(q_tokens, texts, visible):
    E = build()
    out = []
    for k, t in texts.items():
        if all(tok in t for tok in q_tokens) and (E[k]["slugs"] & visible):
            out.append(k)
    return out


def search(q, visible):
    """-> (entry ids, slugs, corrected) for a typed query: every entry whose names contain all the words (the union of their articles); when nothing
    matches, each word is replaced by its closest known word (Antropic -> Anthropic) and the search repeats. corrected = the query actually used, '' if unchanged."""
    import difflib
    texts, vocab = _search_index()
    toks = [norm(w) for w in _words(q) if len(norm(w)) >= 2]
    if not toks:
        return [], set(), ""
    ids = _match(toks, texts, visible)
    corrected = ""
    if not ids:
        fixed, changed = [], False
        for tk in toks:
            if any(tk in t for t in texts.values()):
                fixed.append(tk)
                continue
            near = difflib.get_close_matches(tk, list(vocab), n=1, cutoff=0.78) if len(tk) >= 4 else []
            if near:
                fixed.append(near[0])
                changed = True
            else:
                fixed.append(tk)
        if changed:
            ids = _match(fixed, texts, visible)
            if ids:
                corrected = " ".join(vocab.get(w, w) for w in fixed)
    E = build()
    slugs = set()
    for k in ids:
        slugs |= E[k]["slugs"] & visible
    return ids, slugs, corrected


# ------------------------------------------------------------------ snippets ---
def terms_for(eid=None, query=""):
    """Normalised search terms to look for in an article's text: the words of every name of the entry (en + Hebrew), or of the typed query."""
    names = []
    if eid:
        e = build().get(eid)
        if e:
            names = [e["en"]] + list(e["he"])
    else:
        names = [query]
    out = []
    for nm in names:
        for w in _words(nm):
            nw = norm(w)
            if len(nw) >= 3 and nw not in out and w.lower() not in STOP and w.lower() not in GENERIC:
                out.append(nw)
    return out


def _sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?\u2026\u05f4])\s+|\n+", text or "") if x and x.strip()]


def _best(texts, terms):
    """(sentence, matched words) of the sentence mentioning most of the terms, scanning texts in order; ties go to the earlier one."""
    best, bw, bs = None, [], 0
    for text in texts:
        sents = _sentences(text)
        for i, sent in enumerate(sents):
            hit = []
            for m in _WORD.finditer(sent):
                nw = norm(m.group())
                if any(t in nw for t in terms) and m.group() not in hit:
                    hit.append(m.group())
            sc = len({norm(h) for h in hit})
            if sc > bs:
                nxt = sents[i + 1] if i + 1 < len(sents) else ""
                best, bw, bs = (sent + (" " + nxt if len(sent) < 110 and nxt else "")), hit, sc
        if bs and bs >= len(terms):
            break
    return best, bw


def snippet(slug, terms, prefer_he=True, width=260):
    """A line or two from the article where the searched words are mentioned: {t: text, hl: [words]} or None."""
    import os
    if not terms:
        return None
    try:
        with open(os.path.join(va.ART_DIR, slug + ".json"), encoding="utf-8") as f:
            a = json.load(f)
    except Exception:
        return None
    def texts(x):
        out = list(x.get("key_points") or []) + [x.get("standfirst") or ""]
        out += [(b.get("text") or "") for b in x.get("blocks") or []]
        return out
    eds = [a, a.get("en") or {}]
    if not prefer_he:
        eds.reverse()
    for ed in eds:
        sent, hit = _best(texts(ed), terms)
        if sent:
            if len(sent) > width:                       # window around the first hit
                i = max(0, sent.find(hit[0]) - width // 3) if hit and hit[0] in sent else 0
                sent = ("\u2026 " if i else "") + sent[i:i + width].rsplit(" ", 1)[0] + " \u2026"
            return {"t": sent, "hl": hit[:6]}
    return None
