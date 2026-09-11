"""Cookin candidates scanner — finds new recipe shorts on YouTube that fit the
family's taste (in the spirit of the "basics" catalog, but widening the variety),
scores them with Gemini and lets the admin vet them in at /cands (hidden page,
no navigation from the site). Approving a candidate creates a PUBLIC dish owned
by the admin and runs the regular extraction pipeline (multiuser.process_dish);
any failure lands in the manual queue exactly like a member's dish.

Data: table `cands` in the same SQLite DB (multiuser.db()).
Schedule: one scan per day (COOKIN_CANDS_HOUR_UTC, default 4 = 07:00 Israel),
plus "Scan now" on the page / POST /api/admin/cands/scan.
"""
import datetime, glob, json, math, os, random, re, subprocess, sys, threading, time, traceback
import urllib.request, urllib.parse, urllib.error

import multiuser
from multiuser import db, secret, log, now_iso, current_user, start_processing, admin_emails, GEMINI_MODEL

SITE = multiuser.SITE
MAX_DUR = int(os.environ.get("COOKIN_CANDS_MAX_SEC", "240"))      # reels/shorts only
MIN_VIEWS = int(os.environ.get("COOKIN_CANDS_MIN_VIEWS", "300"))
PER_QUERY = int(os.environ.get("COOKIN_CANDS_PER_QUERY", "15"))
QUERIES_PER_SCAN = int(os.environ.get("COOKIN_CANDS_QUERIES", "10"))
KEEP_SCORE = float(os.environ.get("COOKIN_CANDS_KEEP", "7"))       # below this → stored as 'low', hidden
PER_DISH = int(os.environ.get("COOKIN_CANDS_PER_DISH", "2"))       # max videos of the same dish per scan
PER_QUERY_KEEP = int(os.environ.get("COOKIN_CANDS_PER_QUERY_KEEP", "5"))  # max candidates per search query per scan
SCAN_HOUR_UTC = int(os.environ.get("COOKIN_CANDS_HOUR_UTC", "4"))
SCAN_ENABLED = os.environ.get("COOKIN_CANDS_SCAN", "on").lower() not in ("off", "0", "false")

SCHEMA = """
CREATE TABLE IF NOT EXISTS cands(
  id TEXT PRIMARY KEY, url TEXT, title TEXT, channel TEXT, duration INTEGER, views INTEGER,
  thumb TEXT, query TEXT, lang TEXT, cuisine TEXT, category TEXT, score REAL, fit REAL, novelty REAL,
  reason TEXT, status TEXT DEFAULT 'new', dish_id TEXT, found_at TEXT, decided_at TEXT, dish TEXT);
CREATE INDEX IF NOT EXISTS cands_status ON cands(status, score);
CREATE TABLE IF NOT EXISTS cands_meta(k TEXT PRIMARY KEY, v TEXT);
"""

# Query pool — deliberately wider than the catalog (which is heavy on pasta, chicken,
# Thai/coconut curries, Italian, Mediterranean fish, slow braises). Any language.
QUERY_POOL = [
    # East / Southeast Asia
    "korean braised chicken jjimdak recipe", "korean bulgogi home recipe", "korean kimchi jjigae recipe",
    "japanese oyakodon recipe", "japanese chicken karaage recipe", "japanese nikujaga recipe",
    "vietnamese caramel pork thit kho recipe", "vietnamese lemongrass chicken recipe", "bun cha recipe",
    "chinese mapo tofu recipe", "chinese cumin lamb stir fry", "cantonese steamed fish ginger scallion",
    "sichuan dry fried green beans", "chinese tomato egg stir fry", "chinese braised pork belly recipe",
    "thai larb recipe", "thai massaman curry recipe", "thai tom kha soup recipe", "pad see ew recipe",
    "filipino chicken adobo recipe", "malaysian rendang recipe", "indonesian nasi goreng recipe",
    # South Asia
    "chicken biryani easy recipe", "dal tadka recipe", "chana masala recipe", "keema matar recipe",
    "palak paneer recipe", "goan fish curry recipe", "chicken korma recipe", "aloo gobi recipe",
    # Middle East / Levant / Israel / Persia / Turkey
    "מתכון קל לארוחת ערב", "מתכון סיר אחד", "תבשיל ערבי מתכון", "מתכון מקלובה", "מתכון פריקה",
    "מתכון שקשוקה מיוחדת", "מתכון קציצות ברוטב", "מתכון סלט ערבי", "מתכון דג לשישי",
    "turkish menemen recipe", "turkish kofte recipe", "turkish lentil soup mercimek", "iskender kebab recipe",
    "persian ghormeh sabzi recipe", "persian tahchin recipe", "fesenjan recipe", "persian kuku sabzi",
    "lebanese fatteh recipe", "lebanese mujadara recipe", "syrian kibbeh recipe", "iraqi tbit chicken rice",
    "moroccan chicken tagine olives lemon", "moroccan harira soup recipe", "tunisian shakshuka recipe",
    "yemeni chicken mandi recipe", "georgian chakhokhbili recipe", "georgian lobio recipe",
    # Europe
    "spanish paella recipe easy", "spanish garlic shrimp gambas al ajillo", "spanish tortilla recipe",
    "greek moussaka recipe", "greek lemon chicken soup avgolemono", "greek gemista stuffed vegetables",
    "italian risotto recipe home", "italian ossobuco recipe", "italian eggplant parmigiana", "gnocchi recipe from scratch",
    "italian minestrone recipe", "ricetta veloce cena", "ricetta pollo alla cacciatora", "pasta e fagioli ricetta",
    "french coq au vin recipe", "french ratatouille recipe", "french onion soup recipe", "recette facile poulet",
    "hungarian goulash recipe", "polish pierogi recipe", "russian borscht recipe", "german schnitzel recipe",
    "portuguese piri piri chicken", "portuguese bacalhau recipe", "receta pollo al chilindron",
    # Americas
    "mexican chicken tinga recipe", "mexican pozole recipe", "birria tacos recipe", "carnitas recipe",
    "mexican enchiladas verdes recipe", "receta pollo con mole", "peruvian lomo saltado recipe",
    "peruvian aji de gallina recipe", "brazilian moqueca recipe", "brazilian feijoada recipe",
    "argentinian empanadas recipe", "cuban ropa vieja recipe", "jamaican jerk chicken recipe",
    "louisiana gumbo recipe", "shrimp and grits recipe", "cajun jambalaya recipe",
    # Africa
    "ethiopian doro wat recipe", "west african jollof rice recipe", "south african bobotie recipe",
    "nigerian egusi soup recipe", "senegalese chicken yassa recipe",
    # ingredient / technique-led (widen: lamb, seafood, legumes, rice, dumplings, vegetables)
    "lamb shoulder slow roast recipe", "lamb chops recipe pan", "mussels white wine garlic recipe",
    "squid stir fry recipe", "whole roasted cauliflower recipe", "stuffed peppers recipe",
    "eggplant recipe easy dinner", "lentil stew recipe", "white bean stew recipe", "chickpea stew recipe",
    "dumplings recipe homemade", "fried rice recipe restaurant style", "sheet pan dinner recipe",
    "one pot rice chicken recipe", "meatballs recipe sauce", "stuffed cabbage rolls recipe",
    "pumpkin soup recipe", "roasted vegetables salad recipe", "grain bowl recipe", "fish tacos recipe",
    "shrimp curry recipe", "crispy tofu recipe", "zucchini recipe dinner", "leek recipe dinner",
    "baked fish recipe mediterranean", "chicken thighs recipe dinner", "ground beef recipe dinner",
]

# YouTube "sp" filters: under 4 minutes (relevance), then under 4 minutes uploaded this year
SP_FILTERS = ["EgIYAQ%253D%253D", "EgQIBRgB"]  # short+relevance, short+this-year

BLOCK_RX = re.compile(
    r"\b(dessert|cake|cookie|brownie|cupcake|cheesecake|pancake|waffle|muffin|donut|doughnut|pie crust|"
    r"chocolate|ice ?cream|mousse|pudding|candy|fudge|frosting|macaron|tiramisu|baklava|"
    r"cocktail|smoothie|milkshake|mukbang|asmr eating|what i eat|weight loss|diet plan|calorie|protein shake|"
    r"dog food|cat food|review|ranking|taste test|vs\.?|challenge|prank|reaction)\b|"
    r"עוגה|עוגיות|קינוח|שוקולד|גלידה|פנקייק|בראוניז|מאפינס|מוס\b|שייק|דיאטה", re.I)

_state = {"running": False, "last": None, "last_result": None}
_lock = threading.Lock()


def init():
    with db() as c:
        c.executescript(SCHEMA)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(cands)")}
        if "dish" not in cols:
            c.execute("ALTER TABLE cands ADD COLUMN dish TEXT")


def _meta(k, v=None):
    with db() as c:
        if v is None:
            r = c.execute("SELECT v FROM cands_meta WHERE k=?", (k,)).fetchone()
            return r["v"] if r else None
        c.execute("INSERT INTO cands_meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v))


# ----------------------------------------------------------------- catalog ---
_CAT = None


def catalog():
    """[(name, category)] parsed from site/data*.js (Hebrew files only)."""
    global _CAT
    if _CAT is not None:
        return _CAT
    out = []
    rx = re.compile(r'\bname\s*:\s*"([^"]+)"[^{}]*?\bcategory\s*:\s*"([^"]+)"|\bcategory\s*:\s*"([^"]+)"[^{}]*?\bname\s*:\s*"([^"]+)"')
    for f in sorted(glob.glob(os.path.join(SITE, "data*.js"))):
        if f.endswith("-en.js"):
            continue
        try:
            src = open(f, encoding="utf-8").read()
        except OSError:
            continue
        for m in rx.finditer(src):
            name, cat = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
            out.append((name, cat))
    _CAT = out
    return out


def _known_video_ids():
    """YouTube ids already in the site (static catalog links + member dishes)."""
    ids = set()
    srcs = []
    for f in glob.glob(os.path.join(SITE, "data*.js")):
        try:
            srcs.append(open(f, encoding="utf-8").read())
        except OSError:
            pass
    with db() as c:
        srcs += [r["source_url"] or "" for r in c.execute("SELECT source_url FROM dishes")]
    for s in srcs:
        for m in re.finditer(r"(?:youtu\.be/|youtube\.com/(?:shorts/|watch\?v=|embed/))([A-Za-z0-9_-]{11})", s):
            ids.add(m.group(1))
    return ids


# ------------------------------------------------------------------ search ---
def _yt_search(query, sp, n):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query) + "&sp=" + sp
    cmd = [sys.executable, "-m", "yt_dlp", "--flat-playlist", "-j", "--no-warnings", "--playlist-end", str(n), url]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        log(f"cands: search timeout {query!r}")
        return []
    out = []
    for line in p.stdout.splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        vid = d.get("id")
        if not vid or len(vid) != 11 or d.get("live_status") in ("is_live", "is_upcoming"):
            continue
        thumbs = d.get("thumbnails") or []
        out.append({
            "id": vid, "url": f"https://www.youtube.com/watch?v={vid}",
            "title": (d.get("title") or "")[:200], "channel": (d.get("channel") or d.get("uploader") or "")[:100],
            "duration": int(d.get("duration") or 0), "views": int(d.get("view_count") or 0),
            "thumb": (thumbs[-1].get("url") if thumbs else f"https://i.ytimg.com/vi/{vid}/hq720.jpg"),
            "query": query,
        })
    if p.returncode != 0 and not out:
        log(f"cands: search failed {query!r}: {(p.stderr or '')[-300:]}")
    return out


def _pick_queries(n):
    """Rotate through the pool: today's slice, seeded by date, so consecutive days differ."""
    rnd = random.Random(datetime.date.today().toordinal())
    pool = QUERY_POOL[:]
    rnd.shuffle(pool)
    # avoid the queries used in the last two scans
    recent = set(json.loads(_meta("recent_queries") or "[]"))
    picked = [q for q in pool if q not in recent][:n]
    if len(picked) < n:
        picked += [q for q in pool if q not in picked][:n - len(picked)]
    _meta("recent_queries", json.dumps((list(recent) + picked)[-2 * n:]))
    return picked


# ----------------------------------------------------------------- scoring ---
SCORE_SCHEMA = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "id": {"type": "STRING"}, "is_recipe": {"type": "BOOLEAN"},
    "fit": {"type": "NUMBER"}, "novelty": {"type": "NUMBER"}, "dish": {"type": "STRING"},
    "cuisine": {"type": "STRING"}, "category": {"type": "STRING"}, "lang": {"type": "STRING"},
    "reason": {"type": "STRING"}}, "required": ["id", "is_recipe", "fit", "novelty", "dish", "reason"]}}


def _score_prompt(items):
    cat = catalog()
    counts = {}
    for _, c in cat:
        counts[c] = counts.get(c, 0) + 1
    names = "\n".join(f"- {n} [{c}]" for n, c in cat)
    lst = "\n".join(f'{i["id"]} | {i["title"]} | channel: {i["channel"]} | {i["duration"]}s | {i["views"]} views'
                    for i in items)
    return f"""You curate "Cookin", a Hebrew family recipe book built from short cooking videos (reels/shorts).
The family already has these {len(cat)} dishes (category counts: {json.dumps(counts, ensure_ascii=False)}):
{names}

Their taste, inferred from the catalog: savory home cooking for weeknights and Shabbat; lots of pasta
(lemon/butter/chili-crisp/creamy), chicken (Thai & coconut curries, braises, one-pot), beef braises and
"set-and-forget" pots, Mediterranean fish, Chinese/Thai/Korean home-style stir fries, Israeli & Levantine
dishes, 5-ingredient quick dinners, simple salads and vegetable sides. Real food a home cook can make,
no desserts/baking, no diet or fitness content, no restaurant reviews, mukbang or ASMR without a recipe.

Now the goal is to WIDEN the variety, not to repeat: new cuisines (Mexican, Indian, Korean, Japanese,
Vietnamese, Turkish, Persian, Greek, Spanish, Georgian, Moroccan, Lebanese, Filipino, Peruvian, West African...),
new proteins and formats (lamb, mussels/squid/shrimp, legumes, rice dishes, dumplings, stuffed vegetables,
soups, salads as a meal), new techniques. A candidate that is basically another aglio e olio, red curry
chicken, alfredo, lemon pasta, Mongolian beef or chimichurri should get LOW novelty.

Score each YouTube candidate below from title + channel only. Be CALIBRATED and use the whole range:
a typical decent recipe video is fit 6 / novelty 5; reserve 9-10 for the few that are truly exceptional.
Differentiate between candidates: the same dish from a well-known, trusted channel (RecipeTin Eats,
Jamie Oliver, Kenji, The Mediterranean Dish, Maangchi, Chef John, established native cooks...) beats a
generic one; a clear title with a real dish name beats clickbait.
- is_recipe: true only if this looks like an actual cooking recipe video (not a review/vlog/eating video).
- fit 0-10: would this family love to cook and eat it (delicious, home-cookable, savory, in their spirit,
  weeknight-feasible or a worthy Shabbat pot). Penalize: gimmicks, giant-batch/outdoor cooking, very
  hard or exotic-ingredient recipes, low-effort content.
- novelty 0-10: how much it adds to the catalog (10 = new cuisine/technique/ingredient; 0 = near duplicate
  of an existing dish). Judge against the catalog only, not against other candidates.
- dish: canonical dish name in lowercase English (e.g. "mujadara", "ratatouille", "chicken carnitas") so
  videos of the same dish can be grouped.
- cuisine: short label in Hebrew (e.g. "קוריאני", "מקסיקני"). category: the best of {", ".join(multiuser.CATS_HE)}.
- lang: probable language of the video (ISO code like en/he/it/es/ko).
- reason: ONE short Hebrew sentence for the admin (why yes / why not), max 120 chars.

Candidates (id | title | channel | duration | views):
{lst}

Return a JSON array with one object per candidate id."""


def _gemini_json(prompt, schema, timeout=180):
    key = secret("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json",
                                 "response_schema": schema, "maxOutputTokens": 32768}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                res = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            last = e.read().decode()[:400]
            if e.code in (429, 500, 503) and attempt < 2:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"gemini {e.code}: {last}")
    text = res["candidates"][0]["content"]["parts"][0]["text"]
    tokens = int((res.get("usageMetadata") or {}).get("totalTokenCount") or 0)
    try:
        return json.loads(text), tokens
    except json.JSONDecodeError:
        # truncated output: salvage the complete objects of the array
        cut = text.rfind("},")
        if cut > 0:
            try:
                return json.loads(text[:cut + 1] + "]"), tokens
            except json.JSONDecodeError:
                pass
        raise


def _heuristic(items):
    """Fallback when Gemini is unavailable: keep everything that passes the filters, mid score."""
    return {i["id"]: {"is_recipe": True, "fit": 6, "novelty": 6, "cuisine": "", "category": "",
                      "lang": "", "reason": "לא נוקד (Gemini לא זמין) — לבדוק ידנית"} for i in items}


def score(items):
    out, tokens = {}, 0
    for i in range(0, len(items), 20):
        chunk = items[i:i + 20]
        try:
            arr, t = _gemini_json(_score_prompt(chunk), SCORE_SCHEMA)
            tokens += t
            for row in arr if isinstance(arr, list) else []:  # noqa
                if isinstance(row, dict) and row.get("id"):
                    out[str(row["id"])] = row
        except Exception as e:
            log(f"cands: scoring failed ({e}); heuristic for {len(chunk)}")
            out.update(_heuristic(chunk))
    return out, tokens


# -------------------------------------------------------------------- scan ---
def scan(n_queries=None):
    """One full scan: search → filter → dedupe → score → insert. Returns a summary dict."""
    t0 = time.time()
    queries = _pick_queries(n_queries or QUERIES_PER_SCAN)
    raw, seen = [], set()
    for q in queries:
        for sp in SP_FILTERS:
            for it in _yt_search(q, sp, PER_QUERY):
                if it["id"] not in seen:
                    seen.add(it["id"]); raw.append(it)
    known = _known_video_ids()
    with db() as c:
        have = {r["id"] for r in c.execute("SELECT id FROM cands")}
    cands = [i for i in raw if i["id"] not in known and i["id"] not in have
             and 15 <= i["duration"] <= MAX_DUR and i["views"] >= MIN_VIEWS
             and not BLOCK_RX.search(i["title"] + " " + i["channel"])]
    scores, tokens = score(cands) if cands else ({}, 0)
    kept = low = 0
    now = now_iso()
    # final score: taste fit + variety + a popularity signal (300 views → 0, 10k → 4, 100k → 7, 1M+ → 10)
    for i in cands:
        s = scores.get(i["id"]) or {"is_recipe": True, "fit": 5, "novelty": 5, "reason": "", "dish": ""}
        i["s"] = s
        fit, nov = float(s.get("fit") or 0), float(s.get("novelty") or 0)
        pop = min(10.0, max(0.0, (math.log10(i["views"] + 1) - 2.5) * 2.86))
        i["final"] = round(0.5 * fit + 0.3 * nov + 0.2 * pop, 1) if s.get("is_recipe", True) else 0.0
        i["dish"] = (s.get("dish") or "").strip().lower()[:60] or i["query"]
    # same dish → keep only the best PER_DISH videos as candidates, the rest are duplicates
    per_dish, per_q = {}, {}
    for i in sorted(cands, key=lambda x: (-x["final"], -x["views"])):
        n = per_dish.get(i["dish"], 0)
        i["dup"] = n >= PER_DISH
        per_dish[i["dish"]] = n + 1
        i["over"] = False
        if not i["dup"] and i["final"] >= KEEP_SCORE:
            q = per_q.get(i["query"], 0)
            i["over"] = q >= PER_QUERY_KEEP   # variety: no more than PER_QUERY_KEEP dishes from one query
            per_q[i["query"]] = q + 1
    with db() as c:
        for i in cands:
            s, final = i["s"], i["final"]
            reason = (s.get("reason") or "")[:300]
            st = "new" if final >= KEEP_SCORE and not i["dup"] and not i["over"] else "low"
            if i["dup"] and final >= KEEP_SCORE:
                reason = f"כפילות ({i['dish']}) · " + reason
            elif i["over"]:
                reason = "עודף לשאילתה · " + reason
            kept += st == "new"; low += st == "low"
            c.execute("INSERT OR IGNORE INTO cands(id,url,title,channel,duration,views,thumb,query,lang,cuisine,category,"
                      "score,fit,novelty,reason,status,found_at,dish) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (i["id"], i["url"], i["title"], i["channel"], i["duration"], i["views"], i["thumb"], i["query"],
                       (s.get("lang") or "")[:8], (s.get("cuisine") or "")[:40], (s.get("category") or "")[:40],
                       final, float(s.get("fit") or 0), float(s.get("novelty") or 0), reason, st, now, i["dish"]))
        # keep the table small: drop old 'low' rows after 60 days
        cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=60)).isoformat()
        c.execute("DELETE FROM cands WHERE status='low' AND found_at<?", (cutoff,))
    res = {"at": now, "queries": queries, "raw": len(raw), "filtered": len(cands), "new": kept, "low": low,
           "tokens": tokens, "secs": round(time.time() - t0)}
    _meta("last_scan", json.dumps(res, ensure_ascii=False))
    log(f"cands: scan done {res}")
    return res


def start_scan(n_queries=None, reset=False):
    with _lock:
        if _state["running"]:
            return False
        _state["running"] = True
    if reset:  # drop undecided rows (new/low) so the next scan re-evaluates from scratch
        with db() as c:
            c.execute("DELETE FROM cands WHERE status IN ('new','low')")
        _meta("recent_queries", "[]")

    def run():
        try:
            _state["last_result"] = scan(n_queries)
        except Exception as e:
            log(f"cands: scan crashed: {e}\n{traceback.format_exc()}")
            _state["last_result"] = {"error": str(e)[:300], "at": now_iso()}
        finally:
            _state["running"] = False
    threading.Thread(target=run, daemon=True).start()
    return True


def _scheduler():
    while True:
        now = datetime.datetime.now(datetime.timezone.utc)
        nxt = now.replace(hour=SCAN_HOUR_UTC, minute=5, second=0, microsecond=0)
        if nxt <= now:
            nxt += datetime.timedelta(days=1)
        time.sleep(max(60, (nxt - now).total_seconds()))
        last = json.loads(_meta("last_scan") or "{}").get("at") or ""
        if last[:10] != datetime.date.today().isoformat():
            start_scan()


def start_scheduler():
    init()
    if SCAN_ENABLED:
        threading.Thread(target=_scheduler, daemon=True).start()
    log(f"cands: scheduler {'on' if SCAN_ENABLED else 'off'} ({SCAN_HOUR_UTC:02d}:05 UTC)")


# ---------------------------------------------------------------- approval ---
def _admin_owner_id(user):
    if user and user.get("id") and user["id"] != "admin-token":
        return user["id"]
    with db() as c:
        emails = tuple(admin_emails())
        r = c.execute(f"SELECT id FROM users WHERE lower(email) IN ({','.join('?' * len(emails))}) "
                      "ORDER BY last_seen DESC LIMIT 1", emails).fetchone() if emails else None
    return r["id"] if r else None


def decide(user, cid, decision):
    with db() as c:
        r = c.execute("SELECT * FROM cands WHERE id=?", (cid,)).fetchone()
    if not r:
        return {"error": "not found"}, 404
    if decision == "no":
        with db() as c:
            c.execute("UPDATE cands SET status='no', decided_at=? WHERE id=?", (now_iso(), cid))
        return {"ok": True, "status": "no"}, 200
    if decision == "undo":
        if r["dish_id"]:
            return {"error": "already added as a dish; delete it from the site instead"}, 400
        with db() as c:
            c.execute("UPDATE cands SET status='new', decided_at=NULL WHERE id=?", (cid,))
        return {"ok": True, "status": "new"}, 200
    if decision != "yes":
        return {"error": "bad decision"}, 400
    if r["dish_id"]:
        return {"ok": True, "status": "yes", "dish_id": r["dish_id"]}, 200
    owner = _admin_owner_id(user)
    if not owner:
        return {"error": "no admin user row — sign in once with Google"}, 400
    if not secret("GEMINI_API_KEY"):
        return {"error": "extraction not configured"}, 503
    import secrets as _secrets
    did = "u" + _secrets.token_hex(5)
    with db() as c:
        c.execute("INSERT INTO dishes(id,owner_id,visibility,status,source_url,created_at,updated_at) "
                  "VALUES(?,?,?,?,?,?,?)", (did, owner, "public", "processing", r["url"], now_iso(), now_iso()))
        c.execute("UPDATE cands SET status='yes', dish_id=?, decided_at=? WHERE id=?", (did, now_iso(), cid))
    start_processing(did)
    return {"ok": True, "status": "yes", "dish_id": did}, 200


def _rows(status, limit=200):
    with db() as c:
        rows = [dict(r) for r in c.execute(
            "SELECT c.*, d.status AS dish_status, d.he AS dish_he, d.error AS dish_error FROM cands c "
            "LEFT JOIN dishes d ON d.id=c.dish_id WHERE c.status=? "
            "ORDER BY CASE WHEN c.status IN ('new','low') THEN c.score END DESC, c.views DESC, c.decided_at DESC, c.found_at DESC LIMIT ?",
            (status, limit))]
    for r in rows:
        try:
            r["dish_name"] = (json.loads(r.pop("dish_he") or "null") or {}).get("name")
        except Exception:
            r["dish_name"] = None
    return rows


def _counts():
    with db() as c:
        return {r["status"]: r["n"] for r in c.execute("SELECT status, COUNT(*) n FROM cands GROUP BY status")}


# ------------------------------------------------------------------- routes ---
def _require_admin(handler, redirect):
    user = current_user(handler)
    if user and user.get("admin"):
        return user
    if redirect and not user:
        handler.send_response(302)
        handler.send_header("Location", "/auth/login?next=" + urllib.parse.quote(handler.path))
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return None
    handler._json({"error": "forbidden"}, 403)
    return None


def handle_get(handler, path, qs):
    if path in ("/cands", "/cands/"):
        if _require_admin(handler, redirect=True):
            handler._html(PAGE, "no-store")
        return True
    if path == "/api/admin/cands":
        if not _require_admin(handler, redirect=False):
            return True
        st = qs.get("status", ["new"])[0]
        if st not in ("new", "yes", "no", "low"):
            st = "new"
        handler._json({"ok": True, "status": st, "rows": _rows(st), "counts": _counts(),
                       "scan": {"running": _state["running"], "last": json.loads(_meta("last_scan") or "null"),
                                "last_result": _state["last_result"]}})
        return True
    return False


def handle_post(handler, path, qs, read_json):
    if path == "/api/admin/cands/scan":
        if not _require_admin(handler, redirect=False):
            return True
        req = read_json()
        started = start_scan(int(req.get("queries") or 0) or None, reset=bool(req.get("reset")))
        handler._json({"ok": True, "started": started, "running": _state["running"]})
        return True
    if path == "/api/admin/cands/decide":
        user = _require_admin(handler, redirect=False)
        if not user:
            return True
        req = read_json()
        cid = str(req.get("id") or "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", cid):
            handler._json({"error": "bad id"}, 400)
            return True
        body, code = decide(user, cid, str(req.get("decision") or ""))
        handler._json(body, code)
        return True
    return False


# --------------------------------------------------------------------- page ---
PAGE = r"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Cookin · מועמדים</title>
<style>
:root{--bg:#faf7f2;--card:#fff;--ink:#222;--mut:#777;--line:#e8e2d8;--acc:#c0392b;--ok:#2e7d32;--no:#9e9e9e}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"Segoe UI",Arial,sans-serif;padding:16px}
header{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px}
h1{font-size:22px;margin:0 8px 0 0}h1 small{color:var(--mut);font-weight:400;font-size:13px}
.tabs{display:flex;gap:6px}.tab{border:1px solid var(--line);background:#fff;padding:6px 12px;border-radius:20px;cursor:pointer;font-size:14px}
.tab.on{background:var(--ink);color:#fff;border-color:var(--ink)}
button.scan{margin-inline-start:auto;background:var(--acc);color:#fff;border:0;padding:8px 14px;border-radius:8px;cursor:pointer;font-size:14px}
button.scan[disabled]{opacity:.5}
.meta{font-size:12px;color:var(--mut);width:100%}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;display:flex;flex-direction:column}
.th{position:relative;aspect-ratio:16/9;background:#000;cursor:pointer}
.th img{width:100%;height:100%;object-fit:cover;display:block}.th iframe{width:100%;height:100%;border:0}
.th .dur{position:absolute;bottom:6px;left:6px;background:rgba(0,0,0,.75);color:#fff;font-size:11px;padding:2px 6px;border-radius:4px;direction:ltr}
.th .sc{position:absolute;top:6px;right:6px;background:var(--acc);color:#fff;font-weight:700;font-size:13px;padding:3px 8px;border-radius:20px}
.th .sc.hi{background:var(--ok)}
.b{padding:10px 12px;display:flex;flex-direction:column;gap:6px;flex:1}
.t{font-weight:600;font-size:14px;line-height:1.35;direction:ltr;text-align:left}
.c{font-size:12px;color:var(--mut);direction:ltr;text-align:left}
.r{font-size:13px;line-height:1.4}
.tags{display:flex;gap:6px;flex-wrap:wrap;font-size:11px}.tags span{background:#f1ece4;border-radius:6px;padding:2px 7px}
.act{display:flex;gap:8px;margin-top:auto;padding-top:6px}
.act button{flex:1;border:0;padding:9px;border-radius:8px;font-size:15px;cursor:pointer;color:#fff}
.yes{background:var(--ok)}.no{background:var(--no)}.undo{background:#607d8b}
.act a{flex:1;text-align:center;padding:9px;border-radius:8px;font-size:14px;background:#eee;color:var(--ink);text-decoration:none}
.st{font-size:12px;color:var(--mut)}
.empty{color:var(--mut);padding:40px;text-align:center}
</style></head><body>
<header>
 <h1>🍳 מועמדים <small id="cnt"></small></h1>
 <div class="tabs">
  <div class="tab on" data-s="new">חדשים</div><div class="tab" data-s="yes">אושרו</div>
  <div class="tab" data-s="no">נדחו</div><div class="tab" data-s="low">ציון נמוך</div>
 </div>
 <button class="scan" id="scan">🔍 סרוק עכשיו</button>
 <div class="meta" id="meta"></div>
</header>
<div class="grid" id="grid"></div>
<script>
let S='new', busy=false;
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dur=s=>`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
const views=n=>n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?Math.round(n/1e3)+'K':n;
async function load(){
  const r=await fetch('/api/admin/cands?status='+S,{credentials:'same-origin'});
  if(r.status===403||r.status===401){location.href='/auth/login?next=/cands';return}
  const d=await r.json();
  const c=d.counts||{};$('#cnt').textContent=`חדשים ${c.new||0} · אושרו ${c.yes||0} · נדחו ${c.no||0}`;
  const L=d.scan&&d.scan.last, R=d.scan&&d.scan.last_result;
  $('#scan').disabled=!!(d.scan&&d.scan.running);
  $('#meta').textContent=(d.scan&&d.scan.running?'סריקה רצה… (1-3 דק׳) ':'')+
    (L?`סריקה אחרונה ${new Date(L.at).toLocaleString('he-IL')} · ${L.new} חדשים מתוך ${L.filtered} (${L.raw} תוצאות, ${L.secs}s)`:'עוד לא נסרק')+
    (R&&R.error?` · שגיאה: ${R.error}`:'');
  if(d.scan&&d.scan.running)setTimeout(load,8000);
  render(d.rows||[]);
}
function render(rows){
  const g=$('#grid');
  if(!rows.length){g.innerHTML='<div class="empty">אין פריטים</div>';return}
  g.innerHTML=rows.map(x=>`<div class="card" data-id="${x.id}">
   <div class="th" onclick="play(this,'${x.id}')"><img src="${esc(x.thumb)}" alt="" loading="lazy">
     <span class="dur">${dur(x.duration)} · ${views(x.views)}</span>
     <span class="sc ${x.score>=8?'hi':''}">${x.score}</span></div>
   <div class="b">
    <div class="t">${esc(x.title)}</div>
    <div class="c">${esc(x.channel)}${x.lang?' · '+esc(x.lang):''}</div>
    <div class="tags">${x.dish?`<span>${esc(x.dish)}</span>`:''}${x.cuisine?`<span>${esc(x.cuisine)}</span>`:''}${x.category?`<span>${esc(x.category)}</span>`:''}<span>fit ${x.fit} · novelty ${x.novelty}</span></div>
    <div class="r">${esc(x.reason)}</div>
    ${x.dish_id?`<div class="st">מנה ${esc(x.dish_id)} · ${esc(x.dish_status||'')}${x.dish_name?' · '+esc(x.dish_name):''}${x.dish_error?' · '+esc(x.dish_error):''}</div>`:''}
    <div class="act">
     ${S==='new'||S==='low'?`<button class="yes" onclick="dec('${x.id}','yes')">✅ כן</button><button class="no" onclick="dec('${x.id}','no')">❌ לא</button>`:''}
     ${S==='no'?`<button class="undo" onclick="dec('${x.id}','undo')">↩︎ החזר</button>`:''}
     ${S==='yes'&&x.dish_id?`<a href="/d/${x.dish_id}" target="_blank">פתח מנה</a>`:''}
     <a href="${esc(x.url)}" target="_blank" rel="noopener">YouTube ↗</a>
    </div>
   </div></div>`).join('');
}
function play(el,id){el.innerHTML=`<iframe src="https://www.youtube.com/embed/${id}?autoplay=1" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;el.onclick=null}
async function dec(id,decision){
  if(busy)return;busy=true;
  const card=document.querySelector(`.card[data-id="${id}"]`);if(card)card.style.opacity=.4;
  const r=await fetch('/api/admin/cands/decide',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,decision})});
  const d=await r.json();busy=false;
  if(!r.ok){alert(d.error||'שגיאה');if(card)card.style.opacity=1;return}
  if(card)card.remove();load();
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));t.classList.add('on');S=t.dataset.s;load()});
$('#scan').onclick=async()=>{$('#scan').disabled=true;await fetch('/api/admin/cands/scan',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'});setTimeout(load,1500)};
load();
</script></body></html>"""
