#!/usr/bin/env python3
"""Cookin — family recipe site, Render deployment.

Serves the static site from ./site plus the family-vote JSON API.
Mutable data lives on the persistent disk (DATA_DIR, default /var/data):
  DATA_DIR/family.json   — family vote state
  DATA_DIR/videos/*.mp4  — dish videos (uploaded once via SSH, not in the repo)

Pure stdlib — no requirements. Includes HTTP Range support (Safari/iOS video).
"""
import json, os, re, random, threading, datetime
from collections import Counter
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT", "10000"))
DATA_DIR = os.environ.get("DATA_DIR", "/var/data")
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
STATE_PATH = os.path.join(DATA_DIR, "family.json")
LOCK = threading.Lock()

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

    def _ga(self, body):
        if not self._inject_ga():
            return body
        snip = GA_SNIPPET.encode("utf-8")
        i = body.rfind(b"</body>")
        return body[:i] + snip + body[i:] if i != -1 else body + snip

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
        # legacy path: the site used to be mounted at /cookin/ on jarcud.com
        if p == "/cookin" or p.startswith("/cookin/"):
            target = self.path[len("/cookin"):] or "/"
            self.send_response(301)
            self.send_header("Location", target)
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
        if self.path.split("?")[0] != "/api/family":
            self._json({"error": "not found"}, 404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            self._json({"error": "bad json"}, 400)
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
