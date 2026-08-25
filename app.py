#!/usr/bin/env python3
"""Cookin — family recipe site, Render deployment.

Serves the static site from ./site plus the family-vote JSON API.
Mutable data lives on the persistent disk (DATA_DIR, default /var/data):
  DATA_DIR/family.json   — family vote state
  DATA_DIR/videos/*.mp4  — dish videos (uploaded once via SSH, not in the repo)

Pure stdlib — no requirements. Includes HTTP Range support (Safari/iOS video).
"""
import json, os, re, random, threading, datetime, time
import urllib.request, urllib.parse
from collections import Counter
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT", "10000"))
DATA_DIR = os.environ.get("DATA_DIR", "/var/data")
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
GAME_PATH = os.path.join(ASSETS, "lielmali.html")
SUMMER_PATH = os.path.join(ASSETS, "ilsummer.html")
BARRACE_PATH = os.path.join(ASSETS, "barrace.html")
VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
STATE_PATH = os.path.join(DATA_DIR, "family.json")
LOCK = threading.Lock()

# Vidsum Discover: topic -> recent podcast episodes (iTunes Search API, which
# indexes the open-RSS ecosystem incl. non-exclusive Spotify shows) + a job
# queue on the persistent disk, processed later from the owner's Mac.
VIDSUM_PAGE_PATH = os.path.join(ASSETS, "vidsum_discover.html")
VIDSUM_QUEUE_PATH = os.path.join(DATA_DIR, "vidsum_queue.json")
VIDSUM_LOCK = threading.Lock()
VIDSUM_MAX_PENDING = 100


def vidsum_load_queue():
    try:
        with open(VIDSUM_QUEUE_PATH, encoding="utf-8") as f:
            q = json.load(f)
        q.setdefault("jobs", [])
        return q
    except Exception:
        return {"jobs": []}


def vidsum_save_queue(q):
    tmp = VIDSUM_QUEUE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=1)
    os.replace(tmp, VIDSUM_QUEUE_PATH)


def vidsum_search(topic):
    url = ("https://itunes.apple.com/search?media=podcast&entity=podcastEpisode"
           "&limit=200&term=" + urllib.parse.quote(topic))
    req = urllib.request.Request(url, headers={"User-Agent": "jarcud-vidsum/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.load(r)
    cutoff = (datetime.datetime.now(datetime.timezone.utc)
              - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    eps = []
    for it in data.get("results", []):
        rel = (it.get("releaseDate") or "")[:10]
        if rel < cutoff or not it.get("episodeUrl"):
            continue
        eps.append({
            "id": str(it.get("trackId") or it.get("episodeGuid") or it.get("episodeUrl")),
            "title": it.get("trackName", ""),
            "show": it.get("collectionName", ""),
            "date": rel,
            "duration_ms": it.get("trackTimeMillis") or 0,
            "mp3": it.get("episodeUrl"),
            "page": it.get("trackViewUrl") or "",
        })
    eps.sort(key=lambda e: e["date"], reverse=True)
    return eps[:100]

DEFAULT = {"members": [], "votes": {}, "decision": None, "tieCounter": None, "history": []}

# Google Analytics (GA4) — property "Jarcud". Injected into HTML responses for
# the public host only (skip onrender.com previews and health checks).
GA_ID = "G-TFS1NEQBVQ"
GA_SNIPPET = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=' + GA_ID + '"></script>'
    "<script>window.dataLayer=window.dataLayer||[];"
    "function gtag(){dataLayer.push(arguments);}"
    "gtag('js',new Date());gtag('config','" + GA_ID + "');</script>"
)

SUMMER_PREFIX = (
    "<!doctype html>\n"
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<link rel="icon" href="data:image/svg+xml,'
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<text y='.9em' font-size='90'>&#9728;&#65039;</text></svg>\">\n"
)

# Same wrapper for other artifact-style assets, different favicon.
BARRACE_PREFIX = SUMMER_PREFIX.replace("&#9728;&#65039;", "&#127937;")

JARCUD_LANDING = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jarcud</title>
<style>
  body { margin:0; min-height:100vh; display:flex; align-items:center;
         justify-content:center; background:#241c12; color:#f6ecd8;
         font-family:system-ui,-apple-system,"Segoe UI",sans-serif; }
  h1 { font-size:clamp(30px,7vw,58px); letter-spacing:.12em; margin:0;
       text-transform:uppercase; text-align:center; padding:0 16px; }
</style>
<h1>Jarcud is King &#128081;</h1>
"""

JARCUD_ARTIFACTS = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jarcud Artifacts</title>
<style>
  body { margin:0; min-height:100vh; display:flex; flex-direction:column;
         align-items:center; justify-content:center; gap:14px;
         background:#241c12; color:#f6ecd8;
         font-family:system-ui,-apple-system,"Segoe UI",sans-serif; }
  h1 { font-size:clamp(28px,6vw,44px); letter-spacing:.14em; margin:0 0 10px;
       text-transform:uppercase; }
  a.card { display:flex; align-items:center; gap:14px; width:min(420px,86vw);
      padding:18px 22px; border-radius:14px; text-decoration:none;
      background:rgba(246,236,216,.07); border:1px solid rgba(246,236,216,.22);
      color:#f6ecd8; font-size:18px; font-weight:600; }
  a.card:hover { background:rgba(246,236,216,.14); }
  a.card span.e { font-size:26px; }
  a.card small { display:block; font-weight:400; font-size:13px; color:rgba(246,236,216,.65); }
  a.home { margin-top:14px; color:rgba(246,236,216,.55); text-decoration:none;
           font-size:14px; letter-spacing:.06em; }
  a.home:hover { color:#f6ecd8; }
</style>
<h1>Artifacts</h1>
<a class="card" href="https://cookin.jarcud.com"><span class="e">&#127859;</span><span>Cookin<small>ספר המתכונים המשפחתי</small></span></a>
<a class="card" href="/ilsummer"><span class="e">&#9728;&#65039;</span><span>IL Summer<small>How much summer is left?</small></span></a>
<a class="card" href="/lielmali"><span class="e">&#128373;&#65039;</span><span>Where in the World are Liel &amp; Mali?<small>The detective game</small></span></a>
<a class="card" href="/barrace"><span class="e">&#127937;</span><span>Bar Race<small>7-color racing game</small></span></a>
<a class="card" href="/vidsum"><span class="e">&#127916;</span><span>Vidsum Discover<small>Topic search &rarr; queue episodes to summarize</small></span></a>
<a class="home" href="/">&#128081; Jarcud</a>
"""


class _LimitedFile:
    """File wrapper that stops after `remaining` bytes (for HTTP 206 responses)."""
    def __init__(self, f, remaining):
        self.f, self.remaining = f, remaining

    def read(self, n=-1):
        if self.remaining <= 0:
            return b""
        n = self.remaining if n < 0 else min(n, self.remaining)
        data = self.f.read(n)
        self.remaining -= len(data)
        return data

    def close(self):
        self.f.close()


def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            s = json.load(f)
        for k, v in DEFAULT.items():
            s.setdefault(k, v if not isinstance(v, (list, dict)) else type(v)())
        return s
    except Exception:
        return json.loads(json.dumps(DEFAULT))


def save_state(s):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_PATH)


def maybe_finalize(s, force=False):
    """Finalize tomorrow's lunch if conditions are met. Returns True if changed."""
    now = datetime.datetime.now()
    target = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    if s.get("decision") and s["decision"].get("date", "") >= target:
        return False
    members, votes = s.get("members", []), s.get("votes", {})
    votes = {m: d for m, d in votes.items() if m in members}
    if not members or not votes:
        return False
    all_voted = all(m in votes for m in members)
    deadline = now.hour >= 22
    if not (all_voted or deadline or force):
        return False
    tally = Counter(votes.values())
    top = max(tally.values())
    tied = sorted([d for d, n in tally.items() if n == top])
    is_tie = len(tied) > 1
    if is_tie:
        if s.get("tieCounter") is None:
            idx = random.randrange(len(tied))
            s["tieCounter"] = idx + 1
        else:
            idx = s["tieCounter"] % len(tied)
            s["tieCounter"] += 1
        dish = tied[idx]
    else:
        dish = tied[0]
    s["decision"] = {
        "date": target,
        "dishId": dish,
        "decidedAt": now.isoformat(timespec="seconds"),
        "reason": "all-voted" if all_voted else ("manual" if force and not deadline else "deadline-22"),
        "tie": is_tie,
        "tiedWith": tied if is_tie else [],
        "votes": dict(votes),
    }
    s["history"] = (s.get("history") or [])[-29:] + [s["decision"]]
    s["votes"] = {}
    return True


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=SITE, **kw)

    def log_message(self, *a):
        pass

    def translate_path(self, path):
        # /videos/* is served from the persistent disk, not the repo.
        p = path.split("?")[0]
        if p.startswith("/videos/"):
            name = os.path.basename(p)
            return os.path.join(VIDEOS_DIR, name)
        return super().translate_path(path)

    def _inject_ga(self):
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        return host == "jarcud.com" or host.endswith(".jarcud.com")

    def _is_main_host(self):
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        return host in ("jarcud.com", "www.jarcud.com")

    def _ga(self, body):
        if not self._inject_ga():
            return body
        snip = GA_SNIPPET.encode("utf-8")
        i = body.rfind(b"</body>")
        return body[:i] + snip + body[i:] if i != -1 else body + snip

    def _html(self, body, cache_control=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        body = self._ga(body)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cache_control:
            self.send_header("Cache-Control", cache_control)
        self.end_headers()
        self.wfile.write(body)

    # --- HTTP Range support (required by Safari/iOS for <video>) ---
    def send_head(self):
        path = self.translate_path(self.path)
        rng = self.headers.get("Range")
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
        if not m or (m.group(1) == "" and m.group(2) == ""):
            return super().send_head()
        size = os.path.getsize(path)
        start_s, end_s = m.groups()
        if start_s == "":
            start = max(0, size - int(end_s)); end = size - 1
        else:
            start = int(start_s)
            end = min(int(end_s), size - 1) if end_s else size - 1
        if start > end or start >= size:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        return _LimitedFile(f, end - start + 1)

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split("?")[0]
        if self._is_main_host() and p == "/":
            self._html(JARCUD_LANDING)
            return
        if self._is_main_host() and p in ("/artifacts", "/artifacts/"):
            self._html(JARCUD_ARTIFACTS)
            return
        if self._is_main_host() and p in ("/game", "/game/", "/lielmali", "/lielmali/"):
            try:
                with open(GAME_PATH, "rb") as f:
                    self._html(f.read())
            except OSError:
                self._json({"error": "game not found"}, 404)
            return
        if self._is_main_host() and p in ("/summer", "/summer/", "/ilsummer", "/ilsummer/"):
            try:
                with open(SUMMER_PATH, encoding="utf-8") as f:
                    self._html(SUMMER_PREFIX + f.read(), "no-store")
            except OSError:
                self._json({"error": "summer page not found"}, 404)
            return
        if self._is_main_host() and p in ("/vidsum", "/vidsum/"):
            try:
                with open(VIDSUM_PAGE_PATH, "rb") as f:
                    self._html(f.read(), "no-store")
            except OSError:
                self._json({"error": "vidsum page not found"}, 404)
            return
        if p == "/api/vidsum/search":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            topic = (qs.get("topic", [""])[0] or "").strip()[:100]
            if not topic:
                self._json({"ok": False, "error": "missing topic"}, 400)
                return
            try:
                self._json({"ok": True, "episodes": vidsum_search(topic)})
            except Exception as e:
                self._json({"ok": False, "error": f"search failed: {e}"}, 502)
            return
        if p == "/api/vidsum/queue":
            with VIDSUM_LOCK:
                self._json({"ok": True, **vidsum_load_queue()})
            return
        if self._is_main_host() and p in ("/barrace", "/barrace/", "/race", "/race/"):
            try:
                with open(BARRACE_PATH, encoding="utf-8") as f:
                    self._html(BARRACE_PREFIX + f.read(), "no-store")
            except OSError:
                self._json({"error": "bar race not found"}, 404)
            return
        # legacy path: the site used to be mounted at /cookin/ on jarcud.com
        if p == "/cookin" or p.startswith("/cookin/"):
            target = self.path[len("/cookin"):] or "/"
            if self._is_main_host():
                target = "https://cookin.jarcud.com" + target
            self.send_response(301)
            self.send_header("Location", target)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if p == "/healthz":
            self._json({"ok": True})
            return
        if p == "/api/family":
            with LOCK:
                s = load_state()
                if maybe_finalize(s):
                    save_state(s)
                self._json(s)
            return
        # HTML gets the GA snippet; everything else (images/videos/Range) falls through.
        if self._inject_ga():
            fs = self.translate_path(self.path)
            if os.path.isdir(fs):
                fs = os.path.join(fs, "index.html")
            if fs.endswith(".html") and os.path.isfile(fs):
                with open(fs, "rb") as f:
                    body = self._ga(f.read())
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
        super().do_GET()

    def do_POST(self):
        p = self.path.split("?")[0]
        if p not in ("/api/family", "/api/vidsum/queue", "/api/vidsum/complete"):
            self._json({"error": "not found"}, 404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(min(n, 1 << 20)) or b"{}")
        except Exception:
            self._json({"error": "bad json"}, 400)
            return
        if p == "/api/vidsum/queue":
            eps = req.get("episodes") or []
            if not isinstance(eps, list) or not eps:
                self._json({"ok": False, "error": "no episodes"}, 400)
                return
            topic = str(req.get("topic") or "")[:100]
            with VIDSUM_LOCK:
                q = vidsum_load_queue()
                pending = [j for j in q["jobs"] if j.get("status") == "pending"]
                known = {j.get("ep_id") for j in q["jobs"]}
                added = 0
                for ep in eps[:50]:
                    if not isinstance(ep, dict) or not ep.get("mp3"):
                        continue
                    ep_id = str(ep.get("id") or ep.get("mp3"))
                    if ep_id in known or len(pending) + added >= VIDSUM_MAX_PENDING:
                        continue
                    q["jobs"].append({
                        "ep_id": ep_id, "status": "pending", "topic": topic,
                        "title": str(ep.get("title") or "")[:300],
                        "show": str(ep.get("show") or "")[:200],
                        "date": str(ep.get("date") or "")[:10],
                        "duration_ms": int(ep.get("duration_ms") or 0),
                        "mp3": str(ep.get("mp3"))[:2000],
                        "page": str(ep.get("page") or "")[:2000],
                        "queued_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    known.add(ep_id)
                    added += 1
                vidsum_save_queue(q)
                pend = sum(1 for j in q["jobs"] if j["status"] == "pending")
            self._json({"ok": True, "added": added, "pending": pend})
            return
        if p == "/api/vidsum/complete":
            ids = req.get("ids") or []
            status = req.get("status") if req.get("status") in ("done", "failed") else "done"
            with VIDSUM_LOCK:
                q = vidsum_load_queue()
                hit = 0
                for j in q["jobs"]:
                    if j.get("ep_id") in ids and j.get("status") == "pending":
                        j["status"] = status
                        j["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                        hit += 1
                vidsum_save_queue(q)
            self._json({"ok": True, "updated": hit})
            return
        action = req.get("action")
        with LOCK:
            s = load_state()
            name = (req.get("name") or "").strip()
            if action == "addMember" and name:
                if name not in s["members"]:
                    s["members"].append(name)
            elif action == "removeMember" and name:
                s["members"] = [m for m in s["members"] if m != name]
                s["votes"].pop(name, None)
            elif action == "vote" and name and req.get("dishId"):
                if name in s["members"]:
                    s["votes"][name] = str(req["dishId"])
            elif action == "unvote" and name:
                s["votes"].pop(name, None)
            elif action == "newRound":
                s["votes"] = {}
            else:
                self._json({"error": "unknown action"}, 400)
                return
            maybe_finalize(s)
            save_state(s)
            self._json(s)


if __name__ == "__main__":
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    if not os.path.exists(STATE_PATH):
        save_state(json.loads(json.dumps(DEFAULT)))
    print(f"cookin serving on 0.0.0.0:{PORT}, data={DATA_DIR}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
