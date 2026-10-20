"""PodScanner: admin-only podcast discovery table for Pawed (pawed.io/podscanner).

Pipeline (background thread, resumable, state in DATA_DIR/podscanner.json):
  1 charts   Apple top-podcasts RSS per country x genre  -> candidate ids + chart geo
  2 lookup   iTunes lookup (150 ids per call)            -> name, feed, episode count, last release, genres
  3 enrich   RSS feed (first 300 KB)                     -> language, hosts (author), last episode, cadence
  4 classify LunaRoute (batches)                         -> Pawed topic + hosts, only for pods that pass the rule pre-vet
  5 vet      rules in settings                           -> auto verdict in/out + reasons; manual override wins
Client-side filler: POST /api/podscanner/ingest (admin token) takes names / Apple urls / feed urls found elsewhere
(Mac iTunes search, Google via Chrome MCP) and runs them through steps 2-5.
"""
import datetime, email.utils, hashlib, json, os, re, statistics, threading, time
import urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import multiuser
import vidsum_articles as va

DATA_PATH = os.path.join(multiuser.DATA_DIR, "podscanner.json")
PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "podscanner.html")
LOCK = threading.RLock()
UA = {"User-Agent": "Mozilla/5.0 (pawed-podscanner)", "Accept-Language": "en"}

# country code -> (name, default language). ~25 markets
COUNTRIES = {
    "il": ("Israel", "he"), "us": ("United States", "en"), "gb": ("United Kingdom", "en"), "ca": ("Canada", "en"),
    "au": ("Australia", "en"), "ie": ("Ireland", "en"), "nz": ("New Zealand", "en"), "za": ("South Africa", "en"),
    "in": ("India", "en"), "sg": ("Singapore", "en"), "de": ("Germany", "de"), "fr": ("France", "fr"),
    "es": ("Spain", "es"), "mx": ("Mexico", "es"), "ar": ("Argentina", "es"), "br": ("Brazil", "pt"),
    "it": ("Italy", "it"), "nl": ("Netherlands", "nl"), "se": ("Sweden", "sv"), "no": ("Norway", "no"),
    "pl": ("Poland", "pl"), "ru": ("Russia", "ru"), "tr": ("Turkey", "tr"), "jp": ("Japan", "ja"), "kr": ("South Korea", "ko"),
    "ae": ("United Arab Emirates", "ar"),
}
GENRES = {1301: "Arts", 1303: "Comedy", 1304: "Education", 1305: "Kids & Family", 1307: "Health & Fitness", 1309: "TV & Film",
          1310: "Music", 1311: "News", 1314: "Religion & Spirituality", 1315: "Science", 1316: "Sports", 1318: "Technology",
          1321: "Business", 1324: "Society & Culture", 1488: "True Crime", 1489: "News", 1502: "Leisure", 1511: "Government",
          1512: "History"}
# Apple genre -> Pawed section, used until/unless the model classifies the pod
GENRE_TOPIC = {"News": "פוליטיקה", "Government": "פוליטיקה", "Business": "כלכלה", "Technology": "טכנולוגיה", "Science": "טכנולוגיה",
               "Sports": "ספורט", "Health & Fitness": "בריאות", "TV & Film": "תרבות", "Music": "תרבות", "Arts": "תרבות",
               "Comedy": "תרבות", "History": "תרבות", "Society & Culture": "תרבות", "True Crime": "תרבות", "Leisure": "תרבות",
               "Education": "תרבות", "Religion & Spirituality": "תרבות", "Kids & Family": "תרבות"}

DEFAULT_SETTINGS = {
    "max_days_since": 45,        # last episode no older than this
    "min_episodes": 20,
    "max_gap_days": 21,          # typical gap between episodes
    "languages": ["he", "en"],
    "topics": ["פוליטיקה", "טכנולוגיה", "כלכלה", "ספורט", "תרבות", "לייפסטייל", "בריאות"],
    "block_genres": ["Kids & Family", "Religion & Spirituality", "Music"],
}

STATUS = {"running": False, "stage": "", "done": 0, "total": 0, "msg": "", "started": None, "finished": None, "error": None}


def log(msg):
    va.log("podscanner " + msg)


# ------------------------------------------------------------------ storage
def _load():
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    d.setdefault("pods", {})
    d.setdefault("settings", dict(DEFAULT_SETTINGS))
    d.setdefault("runs", [])
    st = d["settings"]
    if "רכילות" in st.get("topics", []):                 # category renamed 2026-10-20
        st["topics"] = ["לייפסטייל" if t == "רכילות" else t for t in st["topics"]]
    return d


def _save(d):
    d["runs"] = d["runs"][-30:]
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, DATA_PATH)


def _http(url, timeout=25, limit=None):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(limit) if limit else r.read()
        enc = r.headers.get_content_charset() or "utf-8"
    return raw.decode(enc, "replace")


def _json_get(url, timeout=25):
    last = None
    for i in range(3):
        try:
            return json.loads(_http(url, timeout))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (403, 429, 503):
                time.sleep(4 * (i + 1))
                continue
            raise
        except Exception as e:                 # transient network error
            last = e
            time.sleep(2)
    raise last


def _status(**kw):
    STATUS.update(kw)


# ------------------------------------------------------------------ step 1: charts
def _chart(cc, genre, limit):
    try:
        d = _json_get(f"https://itunes.apple.com/{cc}/rss/toppodcasts/limit={limit}/genre={genre}/json")
    except Exception as e:
        log(f"chart {cc}/{genre} failed: {str(e)[:100]}")
        return []
    out = []
    for rank, e in enumerate((d.get("feed") or {}).get("entry") or [], 1):
        try:
            pid = int(e["id"]["attributes"]["im:id"])
        except Exception:
            continue
        out.append((pid, rank, (e.get("im:name") or {}).get("label", "")))
    return out


def stage_charts(d, countries, genres, limit):
    jobs = [(cc, g) for cc in countries for g in genres]
    _status(stage="charts", done=0, total=len(jobs))
    seen_new = 0
    with ThreadPoolExecutor(6) as ex:
        for n, ((cc, g), rows) in enumerate(zip(jobs, ex.map(lambda j: _chart(j[0], j[1], limit), jobs)), 1):
            for pid, rank, name in rows:
                key = "a%d" % pid
                p = d["pods"].get(key)
                if p is None:
                    p = d["pods"][key] = {"id": key, "apple_id": pid, "name": name, "geo": {}, "source": "apple-charts",
                                          "added": time.strftime("%Y-%m-%d")}
                    seen_new += 1
                best = p["geo"].get(cc)
                if best is None or rank < best:
                    p["geo"][cc] = rank
            _status(done=n)
    log(f"charts: {len(jobs)} charts, {seen_new} new pods, {len(d['pods'])} total")
    return seen_new


# ------------------------------------------------------------------ step 2: iTunes lookup
def _apply_lookup(p, r):
    p["name"] = r.get("collectionName") or r.get("trackName") or p.get("name") or ""
    p["author"] = r.get("artistName") or ""
    p["feed"] = r.get("feedUrl") or p.get("feed") or ""
    p["link"] = (r.get("collectionViewUrl") or r.get("trackViewUrl") or "").split("?")[0]
    p["image"] = r.get("artworkUrl100") or ""
    p["episodes"] = r.get("trackCount") or p.get("episodes")
    p["genres"] = [g for g in (r.get("genres") or []) if g not in ("Podcasts",)]
    p["apple_country"] = (r.get("country") or "").lower()
    rd = r.get("releaseDate") or ""
    if rd:
        p["last_ep_apple"] = rd[:10]
    p["looked_up"] = time.strftime("%Y-%m-%d")


def stage_lookup(d, force=False):
    todo = [p for p in d["pods"].values() if p.get("apple_id") and (force or not p.get("looked_up"))]
    _status(stage="lookup", done=0, total=len(todo))
    for i in range(0, len(todo), 150):
        chunk = todo[i:i + 150]
        ids = ",".join(str(p["apple_id"]) for p in chunk)
        try:
            res = _json_get(f"https://itunes.apple.com/lookup?id={ids}&entity=podcast&limit=200").get("results", [])
        except Exception as e:
            log(f"lookup chunk failed: {str(e)[:100]}")
            continue
        by = {r.get("collectionId"): r for r in res if r.get("collectionId")}
        for p in chunk:
            r = by.get(p["apple_id"])
            if r:
                _apply_lookup(p, r)
            else:
                p["looked_up"] = time.strftime("%Y-%m-%d")
                p["missing"] = True
        _status(done=min(i + 150, len(todo)))
        time.sleep(0.4)


# ------------------------------------------------------------------ step 3: RSS enrichment
def _parse_date(s):
    try:
        t = email.utils.parsedate_to_datetime((s or "").strip())
        return t.astimezone(datetime.timezone.utc).date()
    except Exception:
        return None


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower()


def parse_rss(xml_text):
    """-> dict(language, author, link, dates[list newest first], item_count_seen)."""
    xml_text = re.sub(r"^\s*<\?xml[^>]*\?>", "", xml_text.lstrip("﻿"))
    # the feed is truncated at a size limit: cut at the last complete item so the parser accepts it
    if "</rss>" not in xml_text:
        k = xml_text.rfind("</item>")
        xml_text = (xml_text[:k + 7] if k > 0 else xml_text) + "</channel></rss>"
    root = ET.fromstring(xml_text)
    ch = root.find("channel")
    if ch is None:
        raise ValueError("no channel")
    out = {"language": "", "author": "", "link": "", "dates": [], "desc": ""}
    for el in ch:
        t = _local(el.tag)
        txt = (el.text or "").strip()
        if t == "language" and not out["language"]:
            out["language"] = txt
        elif t == "author" and not out["author"]:
            out["author"] = txt
        elif t in ("description", "summary") and not out["desc"]:
            out["desc"] = re.sub(r"<[^>]+>", " ", txt)[:300]
        elif t == "link" and not out["link"] and txt.startswith("http"):
            out["link"] = txt
        elif t == "item":
            for sub in el:
                if _local(sub.tag) == "pubdate":
                    dt = _parse_date(sub.text)
                    if dt:
                        out["dates"].append(dt)
    out["dates"].sort(reverse=True)
    return out


def cadence_of(dates):
    """dates newest first -> (label, median gap in days)."""
    if len(dates) < 3:
        return ("", None)
    ds = dates[:15]
    gaps = [(ds[i] - ds[i + 1]).days for i in range(len(ds) - 1)]
    g = statistics.median(gaps)
    if g <= 1.5:
        lab = "daily"
    elif g <= 3.5:
        lab = "2-3 / week"
    elif g <= 9:
        lab = "weekly"
    elif g <= 17:
        lab = "biweekly"
    elif g <= 45:
        lab = "monthly"
    else:
        lab = "rare"
    # a pod that bursts then goes quiet is irregular, whatever the median says
    if max(gaps) > max(30, g * 6):
        lab += " (irregular)"
    return (lab, g)


def _norm_lang(l, default=""):
    l = (l or "").strip().lower().replace("_", "-")
    if not l:
        return default
    base = l.split("-")[0]
    return {"iw": "he"}.get(base, base)


def _enrich_one(p):
    feed = p.get("feed")
    if not feed:
        return
    try:
        info = parse_rss(_http(feed, timeout=25, limit=300_000))
    except Exception as e:
        p["rss_error"] = str(e)[:80]
        p["enriched"] = time.strftime("%Y-%m-%d")
        return
    p.pop("rss_error", None)
    dates = info["dates"]
    if dates:
        p["last_ep"] = dates[0].isoformat()
        p["cadence"], p["gap_days"] = cadence_of(dates)
    p["language"] = _norm_lang(info["language"], p.get("language") or "")
    p["rss_author"] = info["author"]
    p["site"] = info["link"]
    p["desc"] = info["desc"]
    p["enriched"] = time.strftime("%Y-%m-%d")


def stage_enrich(d, force=False, max_age_days=3):
    cut = (datetime.date.today() - datetime.timedelta(days=max_age_days)).isoformat()
    todo = [p for p in d["pods"].values() if p.get("feed") and (force or (p.get("enriched") or "") < cut)]
    _status(stage="enrich", done=0, total=len(todo))
    done = 0
    with ThreadPoolExecutor(8) as ex:
        for _ in ex.map(_enrich_one, todo):
            done += 1
            if done % 25 == 0:
                _status(done=done)
            if done % 500 == 0:
                with LOCK:
                    _save(d)
    _status(done=len(todo))


# ------------------------------------------------------------------ step 5: rules
def days_since(p):
    s = p.get("last_ep") or p.get("last_ep_apple")
    if not s:
        return None
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(s)).days
    except ValueError:
        return None


def vet(p, st):
    """-> (auto verdict 'in'|'out', [reasons for out])"""
    why = []
    ds = days_since(p)
    if ds is None:
        why.append("no episode date")
    elif ds > st["max_days_since"]:
        why.append(f"inactive {ds}d")
    if (p.get("episodes") or 0) < st["min_episodes"]:
        why.append(f"{p.get('episodes') or 0} episodes")
    if p.get("gap_days") is not None and p["gap_days"] > st["max_gap_days"]:
        why.append(f"gap {round(p['gap_days'])}d")
    if p.get("language") and p["language"] not in st["languages"]:
        why.append(f"language {p['language']}")
    if p.get("topic") and p["topic"] not in st["topics"]:
        why.append(f"topic {p['topic']}")
    if any(g in st["block_genres"] for g in p.get("genres", [])[:2]):
        why.append("blocked genre")
    return ("out" if why else "in", why)


def revet_all(d):
    st = d["settings"]
    for p in d["pods"].values():
        p["auto"], p["why"] = vet(p, st)


def _prevet_for_classify(p, st):
    """cheap gate before spending model calls: active, enough episodes, wanted language"""
    ds = days_since(p)
    return (ds is not None and ds <= st["max_days_since"] and (p.get("episodes") or 0) >= st["min_episodes"]
            and (not p.get("language") or p["language"] in st["languages"]))


# ------------------------------------------------------------------ step 4: LunaRoute classification
def _classify_batch(batch):
    items = [{"id": p["id"], "name": p["name"], "author": p.get("rss_author") or p.get("author"), "genres": p.get("genres", [])[:2],
              "language": p.get("language"), "description": (p.get("desc") or "")[:260]} for p in batch]
    prompt = ("Classify podcasts for a Hebrew news portal. For each item return: topic = exactly one of "
              + json.dumps(va.TOPICS + ["אחר"], ensure_ascii=False)
              + " (judge the show's main subject; use \"אחר\" when none fits, e.g. kids, religion, music); hosts = the real person "
              "names who host the show if you are confident (from the name/author text), else []. Never invent hosts. "
              'Reply with only JSON: {"<id>": {"topic": "...", "hosts": ["..."]}, ...}\n\n' + json.dumps(items, ensure_ascii=False))
    d, _, _ = va._luna(prompt, max_tokens=4000)
    return d


def stage_classify(d, cap=600):
    st = d["settings"]
    todo = [p for p in d["pods"].values() if not p.get("classified") and _prevet_for_classify(p, st)][:cap]
    _status(stage="classify", done=0, total=len(todo))
    for i in range(0, len(todo), 12):
        batch = todo[i:i + 12]
        try:
            with va.tok_ctx("ps-classify"):
                res = _classify_batch(batch)
        except Exception as e:
            log(f"classify batch failed: {str(e)[:160]}")
            continue
        for p in batch:
            r = res.get(p["id"]) if isinstance(res, dict) else None
            if isinstance(r, dict):
                p["topic"] = r.get("topic") if r.get("topic") in va.TOPICS + ["אחר"] else p.get("topic")
                hosts = [h.strip() for h in (r.get("hosts") or []) if isinstance(h, str) and h.strip()]
                p["hosts"] = hosts[:4]
                p["classified"] = time.strftime("%Y-%m-%d")
        _status(done=min(i + 12, len(todo)))
        with LOCK:
            _save(d)


def run_judge(cap=150, min_score=0):
    """LunaRoute fit grade 1-10 for Pawed, best-scored pods currently vetted 'in' first."""
    if STATUS["running"]:
        return False
    _status(running=True, stage="judge", done=0, total=0, msg="", started=time.strftime("%Y-%m-%d %H:%M:%S"), finished=None, error=None)

    def work():
        try:
            with LOCK:
                d = _load()
            todo = [p for p in d["pods"].values() if (p.get("manual") or p.get("auto")) == "in" and not p.get("fit") and score_of(p) >= min_score]
            todo.sort(key=lambda p: -score_of(p))
            todo = todo[:cap]
            _status(total=len(todo))
            for i in range(0, len(todo), 10):
                batch = todo[i:i + 10]
                items = [{"id": p["id"], "name": p["name"], "hosts": p.get("hosts"), "topic": p.get("topic"), "language": p.get("language"),
                          "genres": p.get("genres", [])[:2], "cadence": p.get("cadence"), "episodes": p.get("episodes"),
                          "description": (p.get("desc") or "")[:300]} for p in batch]
                prompt = ("Pawed is a Hebrew news portal that turns podcast episodes into long, sourced articles (politics, tech, economy, sport, "
                          "culture, health). Grade each podcast 1-10 for how well its episodes would make good Pawed articles: substantive spoken "
                          "content with real information, opinion or interviews scores high; music, meditation, sound-only, kids, pure comedy bits, "
                          "promo or one-note gimmick shows score low; a well known professional show with a clear host scores higher than an obscure one. "
                          'Reply with only JSON: {"<id>": {"fit": 1-10, "why": "max 12 words in English"}, ...}\n\n' + json.dumps(items, ensure_ascii=False))
                try:
                    with va.tok_ctx("ps-judge"):
                        res, _, _ = va._luna(prompt, max_tokens=3000)
                except Exception as e:
                    log(f"judge batch failed: {str(e)[:160]}")
                    continue
                for p in batch:
                    r = res.get(p["id"]) if isinstance(res, dict) else None
                    if isinstance(r, dict) and isinstance(r.get("fit"), (int, float)):
                        p["fit"] = max(1, min(10, int(r["fit"])))
                        p["fit_why"] = str(r.get("why") or "")[:120]
                _status(done=min(i + 10, len(todo)))
                with LOCK:
                    _save(d)
            _status(msg=f"{len(todo)} pods graded")
        except Exception as e:
            log("judge failed: " + str(e)[:200])
            _status(error=str(e)[:200])
        finally:
            _status(running=False, stage="done", finished=time.strftime("%Y-%m-%d %H:%M:%S"))

    threading.Thread(target=work, daemon=True).start()
    return True


def fill_defaults(d):
    """topic from the Apple genre (and hosts from the feed author) wherever the model hasn't spoken"""
    for p in d["pods"].values():
        if p.get("topic") in _TOPIC_FIX:
            p["topic"] = _TOPIC_FIX[p["topic"]]
        if not p.get("topic"):
            for g in p.get("genres", []):
                if g in GENRE_TOPIC:
                    p["topic"] = GENRE_TOPIC[g]
                    break
            else:
                p["topic"] = "אחר"
        if not p.get("hosts"):
            a = (p.get("rss_author") or p.get("author") or "").strip()
            p["hosts"] = [a] if a else []
            p["hosts_guess"] = True
        else:
            p.pop("hosts_guess", None)
        if not p.get("language"):
            cs = list(p.get("geo", {}))
            p["language"] = COUNTRIES.get(cs[0], ("", ""))[1] if cs else ""


# ------------------------------------------------------------------ run
def run_scan(countries=None, genres=None, limit=100, classify_cap=600, force_enrich=False, skip_charts=False):
    if STATUS["running"]:
        return False
    countries = [c for c in (countries or list(COUNTRIES)) if c in COUNTRIES]
    genres = [g for g in (genres or list(GENRES)) if int(g) in GENRES]
    _status(running=True, stage="starting", done=0, total=0, msg="", started=time.strftime("%Y-%m-%d %H:%M:%S"), finished=None, error=None)

    def work():
        try:
            with LOCK:
                d = _load()
            new = 0 if skip_charts else stage_charts(d, countries, [int(g) for g in genres], limit)
            stage_lookup(d)
            with LOCK:
                _save(d)
            stage_enrich(d, force=force_enrich)
            with LOCK:
                _save(d)
            stage_classify(d, classify_cap)
            fill_defaults(d)
            revet_all(d)
            n_in = sum(1 for p in d["pods"].values() if (p.get("manual") or p.get("auto")) == "in")
            d["runs"].append({"at": time.strftime("%Y-%m-%d %H:%M:%S"), "countries": len(countries), "genres": len(genres),
                              "new": new, "total": len(d["pods"]), "in": n_in})
            with LOCK:
                _save(d)
            _status(msg=f"{new} new pods, {len(d['pods'])} total, {n_in} vetted in")
        except Exception as e:
            log("scan failed: " + str(e)[:200])
            _status(error=str(e)[:200])
        finally:
            _status(running=False, stage="done", finished=time.strftime("%Y-%m-%d %H:%M:%S"))

    threading.Thread(target=work, daemon=True).start()
    return True


# ------------------------------------------------------------------ client-side ingest
def ingest(items, source="client"):
    """items: [{name?, apple_url?, apple_id?, feed_url?}] -> resolves through iTunes, adds as pods, enriches inline."""
    added = 0
    with LOCK:
        d = _load()
    for it in items[:300]:
        pid = it.get("apple_id")
        m = re.search(r"/id(\d{6,})", it.get("apple_url") or "")
        if not pid and m:
            pid = int(m.group(1))
        res = None
        try:
            if pid:
                res = (_json_get(f"https://itunes.apple.com/lookup?id={int(pid)}&entity=podcast").get("results") or [None])[0]
            elif it.get("name"):
                q = urllib.parse.quote(it["name"])
                res = (_json_get(f"https://itunes.apple.com/search?term={q}&media=podcast&limit=1").get("results") or [None])[0]
        except Exception as e:
            log(f"ingest lookup failed for {it}: {str(e)[:80]}")
        if res and res.get("collectionId"):
            key = "a%d" % res["collectionId"]
            p = d["pods"].get(key)
            if p is None:
                p = d["pods"][key] = {"id": key, "apple_id": res["collectionId"], "geo": {}, "source": source,
                                      "added": time.strftime("%Y-%m-%d")}
                added += 1
            _apply_lookup(p, res)
            c = (res.get("country") or "").lower()
            if c and c not in p["geo"]:
                p["geo"][c.lower()] = 0
            _enrich_one(p)
        elif it.get("feed_url"):
            key = "f" + hashlib.md5(it["feed_url"].encode()).hexdigest()[:12]
            if key not in d["pods"]:
                d["pods"][key] = {"id": key, "name": it.get("name") or it["feed_url"], "feed": it["feed_url"], "geo": {}, "source": source,
                                  "added": time.strftime("%Y-%m-%d"), "link": it.get("site") or ""}
                added += 1
            _enrich_one(d["pods"][key])
    fill_defaults(d)
    revet_all(d)
    with LOCK:
        _save(d)
    return added


# ------------------------------------------------------------------ public catalog (feeds the sources page for every signed-in user)
QUALITY = {"min_episodes": 51, "max_days": 45, "min_score": 50}      # "high quality": >50 episodes, last episode <=45 days, chart score >=50
_CAT = {"mtime": 0.0, "pods": []}
_TOPIC_FIX = {"רכילות": "לייפסטייל"}


def _catalog():
    """lightweight pod list for search/browse; cached until the scanner file changes"""
    try:
        m = os.path.getmtime(DATA_PATH)
    except OSError:
        return []
    if m != _CAT["mtime"]:
        with LOCK:
            d = _load()
        seen_n = {}
        for p in d["pods"].values():
            if p.get("missing") or not p.get("feed") or not p.get("name"):
                continue
            row = _row(p)
            row["topic"] = _TOPIC_FIX.get(row["topic"], row["topic"])
            row["_n"] = _nname(p["name"])
            # the same show can be charted under several Apple ids (re-listed feeds): keep one, the best scored / most recently active
            key = row["_n"]
            old_r = seen_n.get(key)
            if old_r is not None and (old_r["score"], -(old_r["days_since"] or 9999)) >= (row["score"], -(row["days_since"] or 9999)):
                continue
            seen_n[key] = row
        pods = list(seen_n.values())
        _CAT["mtime"], _CAT["pods"] = m, pods
    return _CAT["pods"]


def _pub(r):
    return {"id": r["id"], "name": r["name"], "hosts": r["hosts"][:2], "language": r["language"], "topic": r["topic"], "episodes": r["episodes"],
            "days_since": r["days_since"], "cadence": r["cadence"], "geo": r["geo"][:2], "image": r["image"], "score": r["score"]}


def catalog_suggest(q, limit=8):
    k = _nname(q)
    if len(k) < 2:
        return []
    hits = [r for r in _catalog() if k in r["_n"]]
    hits.sort(key=lambda r: (r["days_since"] if r["days_since"] is not None else 9999, not r["_n"].startswith(k), -r["score"]))   # latest episode first
    return [_pub(r) for r in hits[:limit]]


def catalog_quality(r):
    return ((r["episodes"] or 0) >= QUALITY["min_episodes"] and r["days_since"] is not None and r["days_since"] <= QUALITY["max_days"]
            and r["score"] >= QUALITY["min_score"])


def catalog_browse(language="", country="", topic="", limit=30):
    out = [r for r in _catalog() if catalog_quality(r) and (not language or r["language"] == language) and (not country or country in r["geo_codes"])
           and (not topic or r["topic"] == topic)]
    out.sort(key=lambda r: -r["score"])
    return [_pub(r) for r in out[:limit]], len(out)


def catalog_options():
    """languages / countries that actually have quality pods, for the pickers"""
    langs, ctry = {}, {}
    for r in _catalog():
        if catalog_quality(r):
            langs[r["language"]] = langs.get(r["language"], 0) + 1
            for c in r["geo_codes"]:
                if c in COUNTRIES:
                    ctry[c] = ctry.get(c, 0) + 1
    return ({k: v for k, v in sorted(langs.items(), key=lambda kv: -kv[1]) if k},
            [{"code": c, "name": COUNTRIES.get(c, (c.upper(), ""))[0], "n": n} for c, n in sorted(ctry.items(), key=lambda kv: -kv[1])])


def catalog_pod(pid):
    with LOCK:
        d = _load()
    p = d["pods"].get(pid)
    if not p or not p.get("feed"):
        return None
    r = _row(p)
    r["topic"] = _TOPIC_FIX.get(r["topic"], r["topic"])
    return r


def existing_source_name(name):
    return _existing_source(name)


# ------------------------------------------------------------------ view + HTTP
def score_of(p):
    """0-100 popularity/consistency score from chart rank, breadth, depth and regularity"""
    ranks = [r if r else 50 for r in p.get("geo", {}).values()]
    best = (101 - min(ranks)) if ranks else 0
    breadth = min(len(ranks), 6) / 6 * 100
    eps = min((p.get("episodes") or 0), 500) / 500 * 100
    g = p.get("gap_days")
    reg = 0 if g is None else max(0, 100 - g * 6)
    return round(0.5 * best + 0.2 * breadth + 0.1 * eps + 0.2 * reg)


def _row(p):
    cs = sorted(p.get("geo", {}).items(), key=lambda kv: (kv[1] or 999, kv[0]))
    return {"id": p["id"], "name": p.get("name", ""), "hosts": p.get("hosts", []), "hosts_guess": p.get("hosts_guess", False),
            "geo": [COUNTRIES.get(c, (c.upper(), ""))[0] for c, _ in cs][:6], "geo_codes": [c for c, _ in cs][:6],
            "language": p.get("language", ""), "topic": p.get("topic", ""), "genres": p.get("genres", [])[:2],
            "episodes": p.get("episodes"), "cadence": p.get("cadence", ""), "gap_days": p.get("gap_days"),
            "last_ep": p.get("last_ep") or p.get("last_ep_apple") or "", "days_since": days_since(p),
            "link": p.get("link", ""), "feed": p.get("feed", ""), "site": p.get("site", ""), "image": p.get("image", ""),
            "promoted": p.get("promoted", ""), "score": score_of(p), "fit": p.get("fit"), "fit_why": p.get("fit_why", ""), "auto": p.get("auto", "out"), "why": p.get("why", []), "manual": p.get("manual"), "source": p.get("source", "")}


def _nname(n):
    return re.sub(r"[^\w]", "", n or "").lower()


def _existing_source(name):
    """name of a source already in the Pawed table whose name matches (either contains the other), else None"""
    k = _nname(name)
    if len(k) < 3:
        return None
    for c in va._load_ch()["channels"]:
        o = _nname(c.get("name"))
        if o and (o in k or k in o):
            return c.get("name")
    return None


def _admin(handler):
    u = multiuser.current_user(handler)
    return u if u and u.get("admin") else None


def handle_get(handler, path, qs):
    if path in ("/podscanner", "/podscanner/"):
        u = multiuser.current_user(handler)
        if not u or not u.get("admin"):
            if not u:                                   # signed out: send to Google sign-in, admins only get through
                handler.send_response(302)
                handler.send_header("Location", "/auth/login?next=" + urllib.parse.quote("/podscanner"))
                handler.send_header("Content-Length", "0")
                handler.end_headers()
                return True
            handler._json({"error": "not found"}, 404)
            return True
        va._serve(handler, PAGE)
        return True
    if path == "/api/podscanner/pods":
        if not _admin(handler):
            handler._json({"error": "not found"}, 404)
            return True
        with LOCK:
            d = _load()
        rows = [_row(p) for p in d["pods"].values() if not p.get("missing")]
        handler._json({"ok": True, "pods": rows, "settings": d["settings"], "status": STATUS, "runs": d["runs"][-5:],
                       "countries": {k: v[0] for k, v in COUNTRIES.items()}, "topics": va.TOPICS + ["אחר"]})
        return True
    if path == "/api/podscanner/status":
        if not _admin(handler):
            handler._json({"error": "not found"}, 404)
            return True
        handler._json({"ok": True, "status": STATUS})
        return True
    return False


def handle_post(handler, path, req):
    if not _admin(handler):
        handler._json({"error": "not found"}, 404)
        return True
    if path == "/api/podscanner/scan":
        ok = run_scan(req.get("countries"), req.get("genres"), int(req.get("limit") or 100), int(req.get("classify_cap") or 600),
                      bool(req.get("force_enrich")), bool(req.get("skip_charts")))
        handler._json({"ok": ok, "error": None if ok else "a scan is already running", "status": STATUS})
        return True
    if path == "/api/podscanner/judge":
        ok = run_judge(int(req.get("cap") or 150), int(req.get("min_score") or 0))
        handler._json({"ok": ok, "error": None if ok else "a scan is already running", "status": STATUS})
        return True
    if path == "/api/podscanner/verdict":
        with LOCK:
            d = _load()
            for pid in (req.get("ids") or [req.get("id")]):
                p = d["pods"].get(pid)
                if p:
                    if req.get("verdict") in ("in", "out"):
                        p["manual"] = req["verdict"]
                    else:
                        p.pop("manual", None)
            _save(d)
        handler._json({"ok": True})
        return True
    if path == "/api/podscanner/settings":
        with LOCK:
            d = _load()
            st = d["settings"]
            for k in ("max_days_since", "min_episodes", "max_gap_days"):
                if k in req:
                    st[k] = max(0, int(req[k]))
            for k in ("languages", "topics", "block_genres"):
                if isinstance(req.get(k), list):
                    st[k] = [str(x) for x in req[k]][:40]
            revet_all(d)
            _save(d)
        handler._json({"ok": True, "settings": st})
        return True
    if path == "/api/podscanner/promote":
        user = _admin(handler)
        out = []
        for pid in (req.get("ids") or [])[:25]:
            with LOCK:
                p = _load()["pods"].get(pid)
            if not p or not p.get("feed"):
                out.append({"id": pid, "ok": False, "error": "no feed"})
                continue
            twin = _existing_source(p.get("name") or "")
            if twin:                                  # already followed (often as a YouTube channel, so the feed id differs)
                with LOCK:
                    d = _load()
                    d["pods"][pid]["promoted"] = time.strftime("%Y-%m-%d")
                    d["pods"][pid]["manual"] = "in"
                    _save(d)
                out.append({"id": pid, "ok": True, "already": True, "error": None, "twin": twin})
                continue
            try:
                va.add_source({"url": p["feed"], "name": p.get("name"), "language": p.get("language") if p.get("language") in va.LANGS else "he",
                               "vertical": p.get("topic") if p.get("topic") in va.TOPICS else "תרבות"}, user)
                err = None
            except ValueError as e:
                err = str(e)
            except Exception as e:
                err = "failed: " + str(e)[:120]
            ok = err is None or "already in the table" in err
            if ok:
                with LOCK:
                    d = _load()
                    if pid in d["pods"]:
                        d["pods"][pid]["promoted"] = time.strftime("%Y-%m-%d")
                        d["pods"][pid]["manual"] = "in"
                        _save(d)
            out.append({"id": pid, "ok": ok, "error": err if not ok else None, "already": bool(err and ok)})
        handler._json({"ok": True, "results": out})
        return True
    if path == "/api/podscanner/ingest":
        items = req.get("items") if isinstance(req.get("items"), list) else []
        n = ingest(items, str(req.get("source") or "client")[:20])
        handler._json({"ok": True, "added": n})
        return True
    return False
