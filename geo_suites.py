"""Geo suites: a preset roster of podcasts per country, picked by the visitor's geo (or ?geo=brazil).

A suite = the top 5 quality podcasts per Pawed section (local-language, charted in that country) + the US suite as the pivot.
Israel's suite is the legacy base roster (channels without a "geos" tag). Suites are proposed from the PodScanner catalog,
reviewed on /vidsum/geo (admin) and only then activated (the channels are created with geos=[slug]).
"""
import json, os, re, threading, time

import multiuser

DATA_PATH = os.path.join(multiuser.DATA_DIR, "geo_suites.json")
LOCK = threading.RLock()
CTX = threading.local()

# slug -> (ISO country, English name, Hebrew name, audio language of the suite, UI language)
GEOS = {
    "il": ("IL", "Israel", "ישראל", "he", "he"),
    "us": ("US", "United States", "ארצות הברית", "en", "en"),
    "gb": ("GB", "United Kingdom", "בריטניה", "en", "en"),
    "ca": ("CA", "Canada", "קנדה", "en", "en"),
    "au": ("AU", "Australia", "אוסטרליה", "en", "en"),
    "de": ("DE", "Germany", "גרמניה", "de", "de"),
    "fr": ("FR", "France", "צרפת", "fr", "fr"),
    "it": ("IT", "Italy", "איטליה", "it", "it"),
    "es": ("ES", "Spain", "ספרד", "es", "es"),
    "mx": ("MX", "Mexico", "מקסיקו", "es", "es"),
    "br": ("BR", "Brazil", "ברזיל", "pt", "pt"),
    "nl": ("NL", "Netherlands", "הולנד", "nl", "nl"),
}
ALIASES = {"uk": "gb", "britain": "gb", "england": "gb", "unitedkingdom": "gb", "usa": "us", "unitedstates": "us", "america": "us",
           "germany": "de", "deutschland": "de", "france": "fr", "italy": "it", "spain": "es", "mexico": "mx", "brazil": "br", "brasil": "br",
           "canada": "ca", "australia": "au", "netherlands": "nl", "holland": "nl", "israel": "il"}
for _s, _v in GEOS.items():
    ALIASES[_s] = _s
    ALIASES[_v[1].lower().replace(" ", "")] = _s
CC2SLUG = {v[0]: s for s, v in GEOS.items()}
PER_TOPIC = 5


def norm(v):
    return ALIASES.get(re.sub(r"[^a-z]", "", (v or "").lower()), "")


# ------------------------------------------------------------------ visitor geo
def resolve(handler, qs=None):
    """-> (slugs, explicit). The content regions the visitor reads: ?geo= (one, for testing), the pawed_geos cookie (several),
    the legacy pawed_geo cookie, else the detected country plus the United States. Unknown country: Israel plus the US."""
    q = ((qs or {}).get("geo") or [""])[0]
    if not q:
        m = re.search(r"[?&]geo=([A-Za-z_-]{2,20})", getattr(handler, "path", "") or "")
        q = m.group(1) if m else ""
    s = norm(q)
    if s:
        return [s], True
    ck = handler.headers.get("Cookie") or ""
    m = re.search(r"(?:^|;\s*)pawed_geos=([a-z,]{2,60})", ck)
    sel = list(dict.fromkeys(g for g in (norm(x) for x in (m.group(1).split(",") if m else [])) if g))
    if sel:
        return sel, True
    m = re.search(r"(?:^|;\s*)pawed_geo=([a-z]{2,20})\b", ck)
    s = norm(m.group(1)) if m else ""
    if s:
        return [s], True
    cc = (handler.headers.get("CF-IPCountry") or "").strip().upper()
    home = CC2SLUG.get(cc, "us") if len(cc) == 2 and cc.isalpha() and cc not in ("XX", "T1") else "il"
    return list(dict.fromkeys([home, "us"])), False


def set_ctx(handler, qs=None):
    CTX.geos, CTX.explicit = resolve(handler, qs)
    CTX.geo = CTX.geos[0]


def set_geos(geos, explicit=True):
    CTX.geos, CTX.explicit = list(geos), explicit
    CTX.geo = CTX.geos[0]


def ctx():
    return getattr(CTX, "geo", None), getattr(CTX, "explicit", False)


def geos():
    return list(getattr(CTX, "geos", None) or [getattr(CTX, "geo", None) or "il"])


def active(slug, channels):
    return any(slug in (c.get("geos") or ()) for c in channels if c.get("owner_id") is None)


def effective(channels, geo=None):
    """The suite the visitor actually gets: their own when it is live, else the US one when live, else the legacy roster."""
    geo = geo or ctx()[0] or "il"
    if geo == "il":
        return "il"
    if active(geo, channels):
        return geo
    if active("us", channels):
        return "us"
    return "il"


def effective_set(channels, sel=None):
    """The live suites behind the selected regions. A region without a live suite adds nothing; only when none of the picks is live
    does the visitor get the single-geo fallback (US suite, else the Israel roster)."""
    sel = sel or geos()
    live = [g for g in dict.fromkeys(sel) if g == "il" or active(g, channels)]
    return live or [effective(channels, sel[0])]


def channel_ok(c, channels, sel=None):
    """Is this base (Pawed roster) channel in any of the visitor's selected suites?"""
    eff = effective_set(channels, sel)
    g = c.get("geos") or []
    if "il" in eff and (not g or "il" in g):
        return True
    return bool(set(eff) - {"il"}) and bool(set(eff) & set(g))


# ------------------------------------------------------------------ proposals
def _load():
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"suites": {}}


def _save(d):
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, DATA_PATH)


def _candidates(slug, relaxed=False):
    """Catalog podcasts charted in the geo's country, in the suite language, best first per section -> {topic: [rows]}."""
    import podscanner as ps, vidsum_articles as va
    cc, lang = GEOS[slug][0].lower(), GEOS[slug][3]
    q = ps.quality_for(5 if relaxed else 8)
    with ps.LOCK:
        raw = ps._load()["pods"]
    block = set(ps.DEFAULT_SETTINGS["block_genres"])
    seen, by_topic = set(), {}
    for p in raw.values():
        if p.get("missing") or not p.get("feed") or not p.get("name"):
            continue
        rank = (p.get("geo") or {}).get(cc)
        if cc not in (p.get("geo") or {}):
            continue
        row = ps._row(p)
        row["topic"] = ps._TOPIC_FIX.get(row["topic"], row["topic"])
        row["language"] = ps.canon_lang(row["language"])
        if row["language"] != lang or row["topic"] not in va.TOPICS or (set(row["genres"]) & block):
            continue
        if not ps.catalog_quality(row, q):
            continue
        k = ps._nname(row["name"])
        if k in seen:
            continue
        seen.add(k)
        local = 101 - (rank or 50)
        row["rank"] = rank
        row["pick_score"] = round(0.6 * local + 0.4 * row["score"], 1)
        by_topic.setdefault(row["topic"], []).append(row)
    for rows in by_topic.values():
        rows.sort(key=lambda r: -r["pick_score"])
    return by_topic


def _slim(r, relaxed=False):
    return {"id": r["id"], "name": r["name"], "feed": r["feed"], "link": r.get("link", ""), "language": r["language"], "topic": r["topic"],
            "rank": r["rank"], "score": r["score"], "pick_score": r["pick_score"], "episodes": r["episodes"], "days_since": r["days_since"],
            "image": r["image"], "hosts": r["hosts"][:2], "relaxed": relaxed}


def propose(slug):
    """Build (or rebuild) the proposal for one geo. Keeps nothing from a previous proposal."""
    if slug not in GEOS or slug == "il":
        raise ValueError("no proposal for this geo")
    strict, loose = _candidates(slug), None
    pods = {}
    us_ids = set()
    if slug != "us":
        us_ids = {p["id"] for ps_ in (_load()["suites"].get("us") or {}).get("pods", {}).values() for p in ps_}
    import vidsum_articles as va
    for t in va.TOPICS:
        rows = [r for r in strict.get(t, []) if r["id"] not in us_ids][:PER_TOPIC]
        picked = [_slim(r) for r in rows]
        if len(picked) < PER_TOPIC:                                 # thin chart: relax the quality dial one notch to fill, flagged
            loose = loose or _candidates(slug, relaxed=True)
            have = {p["id"] for p in picked} | us_ids
            for r in loose.get(t, []):
                if len(picked) >= PER_TOPIC:
                    break
                if r["id"] not in have:
                    picked.append(_slim(r, relaxed=True))
        pods[t] = picked
    with LOCK:
        d = _load()
        old = d["suites"].get(slug, {})
        d["suites"][slug] = {"pods": pods, "status": "proposed", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                             "activated": old.get("activated") if old.get("status") == "active" else None}
        if old.get("status") == "active":
            d["suites"][slug]["status"] = "active"
        _save(d)
    return d["suites"][slug]


def propose_all():
    out = {}
    order = ["us"] + [s for s in GEOS if s not in ("us", "il")]                # US first: the others exclude its picks
    for s in order:
        try:
            out[s] = propose(s)
        except Exception as e:
            out[s] = {"error": str(e)[:200]}
    return out


def review():
    d = _load()
    res = []
    for s in GEOS:
        if s == "il":
            continue
        su = d["suites"].get(s) or {}
        n = sum(len(v) for v in (su.get("pods") or {}).values())
        res.append({"geo": s, "name": GEOS[s][1], "language": GEOS[s][3], "status": su.get("status") or "none", "generated": su.get("generated"),
                    "pods": su.get("pods") or {}, "count": n})
    return res


def alternatives(slug, topic, limit=8):
    cur = {p["id"] for p in ((_load()["suites"].get(slug) or {}).get("pods") or {}).get(topic, [])}
    rows = [r for r in _candidates(slug, relaxed=True).get(topic, []) if r["id"] not in cur][:limit]
    return [_slim(r) for r in rows]


def pick(slug, topic, remove=None, add=None):
    with LOCK:
        d = _load()
        su = d["suites"].get(slug)
        if not su:
            raise ValueError("no proposal for this geo")
        lst = su["pods"].setdefault(topic, [])
        if remove:
            lst[:] = [p for p in lst if p["id"] != remove]
        if add:
            row = next((r for r in _candidates(slug, relaxed=True).get(topic, []) if r["id"] == add), None)
            if not row:
                raise ValueError("podcast is not a candidate for this geo and section")
            if not any(p["id"] == add for p in lst):
                lst.append(_slim(row, relaxed=True))
        _save(d)
    return su


def activate(slug):
    """Create the roster channels for an approved suite (an existing channel with the same feed or name just gets the geo tag)."""
    import podscanner as ps, vidsum_articles as va
    with LOCK:
        d = _load()
        su = d["suites"].get(slug)
    if not su:
        raise ValueError("no proposal for this geo")
    admin = {"id": "geo-suites", "admin": True, "name": "Pawed"}
    made = tagged = failed = 0
    for topic, pods in su["pods"].items():
        for p in pods:
            ch = va._load_ch()["channels"]
            ex = next((c for c in ch if c.get("owner_id") is None and (c.get("feed_url") == p["feed"] or ps._nname(c.get("name")) == ps._nname(p["name"]))), None)
            if not ex:
                try:
                    cid = va.add_source({"url": p["feed"], "name": p["name"], "language": "en" if p["language"] == "en" else "other",
                                         "lang_full": p["language"], "vertical": topic}, admin)
                except Exception as e:
                    va.log(f"geo-suite {slug} add {p['name']} failed: {str(e)[:120]}")
                    failed += 1
                    continue
                made += 1
            else:
                cid = ex["id"]
                tagged += 1
            with va.LOCK:
                dd = va._load_ch()
                for c in dd["channels"]:
                    if c["id"] == cid:
                        g = list(c.get("geos") or [])
                        if not g and ex and c.get("language") == "he":
                            g = ["il"]                                   # a Hebrew legacy roster channel keeps its Israel membership; other languages are not Israel
                        if slug not in g:
                            g.append(slug)
                        c["geos"] = g
                va._save_ch(dd)
    with LOCK:
        d = _load()
        d["suites"][slug]["status"] = "active"
        d["suites"][slug]["activated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        _save(d)
    return {"created": made, "tagged": tagged, "failed": failed}


ISRAEL_FOCUS = ("Call Me Back", "Unholy: Two Jews")


def retag(dry=True):
    """Israel's suite is the Hebrew roster. Base channels in another language that still count as Israel (no geos, or an `il` tag
    added by an earlier activation) move out: English ones become US content, `il` is dropped from the rest. -> counts + the changes."""
    import vidsum_articles as va
    changes = []
    with va.LOCK:
        d = va._load_ch()
        for c in d["channels"]:
            if c.get("owner_id") is not None or c.get("language") == "he" or c["id"].startswith("pending-"):
                continue
            g = list(c.get("geos") or [])
            new = None
            if not g and c.get("language") == "en":
                new = ["us"]
            elif "il" in g and len(g) > 1:
                new = [x for x in g if x != "il"]
            elif g == ["il"]:
                new = ["us"] if c.get("language") == "en" else None
            if new == ["us"] and any(k in (c.get("name") or "") for k in ISRAEL_FOCUS):
                new = ["il", "us"]                                       # American-made, Israel-focused shows stay in both
            if new is not None and new != g:
                changes.append({"name": c.get("name"), "language": c.get("language"), "from": g, "to": new})
                if not dry:
                    c["geos"] = new
        if not dry and changes:
            va._save_ch(d)
    return {"dry": dry, "count": len(changes), "changes": changes}
