#!/usr/bin/env python3
"""Cookin multi-user layer: Google sign-in, per-user dishes, visibility,
per-user hidden base dishes, include-other-users' public dishes, and the
paste-a-reel → yt-dlp → Gemini extraction pipeline.

State lives on the persistent disk:
  DATA_DIR/cookin.db      SQLite (users, sessions, dishes, prefs, usage)
  DATA_DIR/videos/u*.mp4  user dish videos   (served as /videos/u<id>.mp4)
  DATA_DIR/images/u*.jpg  user dish thumbs   (served as /images/u<id>.jpg)
  DATA_DIR/secrets.json   optional secrets (env vars take precedence)

Pure stdlib + yt-dlp + Pillow + imageio-ffmpeg (see requirements.txt).
"""
import base64, datetime, glob, hashlib, json, os, re, secrets, shutil, sqlite3
import subprocess, sys, tempfile, threading, time, traceback, html as _html
import urllib.error, urllib.parse, urllib.request
from zoneinfo import ZoneInfo

DATA_DIR = os.environ.get("DATA_DIR", "/var/data")
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
DB_PATH = os.path.join(DATA_DIR, "cookin.db")
VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
UIMAGES_DIR = os.path.join(DATA_DIR, "images")
SECRETS_PATH = os.path.join(DATA_DIR, "secrets.json")
TZ = ZoneInfo("Asia/Jerusalem")
DAILY_LIMIT = int(os.environ.get("COOKIN_DAILY_LIMIT", "15"))
SESSION_DAYS = 90
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
MAX_VIDEO_MB = 200
COOKIE = "cookin_sid"
LOG_PATH = os.path.join(DATA_DIR, "multiuser.log")

CATS_HE = ["פסטה", "עוף", "בקר", "דגים", "סלטים", "ירקות ותוספות", "מרקים ורטבים"]
CATS_EN = ["Pasta", "Chicken", "Beef", "Fish", "Salads", "Vegetables & Sides", "Soups & Sauces"]
CAT_HE2EN = dict(zip(CATS_HE, CATS_EN))
DIET_HE = ["בשרי", "דגים", "צמחוני"]
DIET_EN = ["Meat", "Fish", "Vegetarian"]
DIET_HE2EN = dict(zip(DIET_HE, DIET_EN))

_LOCK = threading.Lock()


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print("[multiuser]", line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------- secrets ---
_SECRETS = None


def secret(name, default=None):
    global _SECRETS
    v = os.environ.get(name)
    if v:
        return v
    if _SECRETS is None:
        try:
            with open(SECRETS_PATH, encoding="utf-8") as f:
                _SECRETS = json.load(f)
        except Exception:
            _SECRETS = {}
    return _SECRETS.get(name, default)


def admin_emails():
    raw = secret("ADMIN_EMAILS", "eedo.b@taboola.com") or ""
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


# --------------------------------------------------------------------- db ---
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id TEXT PRIMARY KEY, email TEXT, name TEXT, avatar TEXT,
  created_at TEXT, last_seen TEXT);
CREATE TABLE IF NOT EXISTS sessions(
  token TEXT PRIMARY KEY, user_id TEXT, created_at TEXT, expires_at TEXT);
CREATE TABLE IF NOT EXISTS oauth_states(state TEXT PRIMARY KEY, created_at TEXT, next TEXT);
CREATE TABLE IF NOT EXISTS dishes(
  id TEXT PRIMARY KEY, owner_id TEXT, visibility TEXT DEFAULT 'private',
  status TEXT DEFAULT 'processing', source_url TEXT, he TEXT, en TEXT,
  needs TEXT, has_video INTEGER DEFAULT 0, error TEXT, tokens INTEGER DEFAULT 0,
  created_at TEXT, updated_at TEXT);
CREATE INDEX IF NOT EXISTS dishes_owner ON dishes(owner_id);
CREATE INDEX IF NOT EXISTS dishes_vis ON dishes(visibility, status);
CREATE TABLE IF NOT EXISTS prefs(
  user_id TEXT PRIMARY KEY, hidden TEXT DEFAULT '[]', hide_base INTEGER DEFAULT 0,
  sources TEXT DEFAULT '[]');
CREATE TABLE IF NOT EXISTS usage(user_id TEXT, day TEXT, n INTEGER DEFAULT 0,
  PRIMARY KEY(user_id, day));
"""


def db():
    c = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init():
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    os.makedirs(UIMAGES_DIR, exist_ok=True)
    with db() as c:
        c.executescript(SCHEMA)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(prefs)")}
        if "muted" not in cols:
            c.execute("ALTER TABLE prefs ADD COLUMN muted TEXT DEFAULT '[]'")
    # resume dishes interrupted by a redeploy
    with db() as c:
        c.execute("UPDATE dishes SET status='processing', error=NULL WHERE status IN ('failed','queued') "
                  "AND error LIKE '%No module named%'")
        rows = c.execute("SELECT id FROM dishes WHERE status='processing'").fetchall()
    for r in rows:
        start_processing(r["id"])
    log(f"init ok, db={DB_PATH}, resumed={len(rows)}")


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def today():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%d")


# ------------------------------------------------------------------- auth ---
def parse_cookies(header):
    out = {}
    for part in (header or "").split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            out[k] = v
    return out


def current_user(handler):
    # Headless admin (queue watcher / drain scripts on Eedo's Mac): Authorization: Bearer <COOKIN_ADMIN_TOKEN>
    auth = handler.headers.get("Authorization") or ""
    atok = secret("COOKIN_ADMIN_TOKEN")
    if atok and auth.startswith("Bearer ") and secrets.compare_digest(auth[7:].strip(), atok):
        return {"id": "admin-token", "email": next(iter(sorted(admin_emails())), "admin"), "name": "Admin",
                "avatar": "", "admin": True}
    tok = parse_cookies(handler.headers.get("Cookie")).get(COOKIE)
    if not tok:
        return None
    with db() as c:
        row = c.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id "
            "WHERE s.token=? AND s.expires_at>?", (tok, now_iso())).fetchone()
        if not row:
            return None
        c.execute("UPDATE users SET last_seen=? WHERE id=?", (now_iso(), row["id"]))
    u = dict(row)
    u["admin"] = (u.get("email") or "").lower() in admin_emails()
    return u


def base_url(handler):
    host = handler.headers.get("Host") or "cookin.jarcud.com"
    scheme = "http" if host.startswith(("localhost", "127.0.0.1")) else "https"
    return f"{scheme}://{host}"


def auth_login(handler, qs):
    cid = secret("GOOGLE_CLIENT_ID")
    if not cid:
        return handler._json({"error": "Google sign-in not configured (GOOGLE_CLIENT_ID)"}, 503)
    nxt = (qs.get("next", ["/"])[0] or "/")
    if not nxt.startswith("/") or nxt.startswith("//"):
        nxt = "/"
    state = secrets.token_urlsafe(24)
    with db() as c:
        c.execute("DELETE FROM oauth_states WHERE created_at<?",
                  ((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=20)).isoformat(),))
        c.execute("INSERT INTO oauth_states VALUES(?,?,?)", (state, now_iso(), nxt))
    params = {
        "client_id": cid,
        "redirect_uri": base_url(handler) + "/auth/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    handler.send_response(302)
    handler.send_header("Location", url)
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", "0")
    handler.end_headers()


def _post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def auth_callback(handler, qs):
    state = qs.get("state", [""])[0]
    code = qs.get("code", [""])[0]
    with db() as c:
        row = c.execute("SELECT next FROM oauth_states WHERE state=?", (state,)).fetchone()
        c.execute("DELETE FROM oauth_states WHERE state=?", (state,))
    if not row or not code:
        return handler._html("<p>Sign-in failed (bad state). <a href='/'>Back</a></p>")
    nxt = row["next"] or "/"
    try:
        tok = _post_form("https://oauth2.googleapis.com/token", {
            "code": code, "client_id": secret("GOOGLE_CLIENT_ID"),
            "client_secret": secret("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": base_url(handler) + "/auth/callback",
            "grant_type": "authorization_code"})
        req = urllib.request.Request("https://openidconnect.googleapis.com/v1/userinfo",
                                     headers={"Authorization": "Bearer " + tok["access_token"]})
        with urllib.request.urlopen(req, timeout=20) as r:
            info = json.loads(r.read().decode())
    except Exception as e:
        log(f"oauth error: {e}")
        return handler._html(f"<p>Sign-in failed: {_html.escape(str(e))}. <a href='/'>Back</a></p>")
    uid = "g" + info["sub"]
    session = secrets.token_urlsafe(32)
    exp = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=SESSION_DAYS))
    with db() as c:
        c.execute("INSERT INTO users(id,email,name,avatar,created_at,last_seen) VALUES(?,?,?,?,?,?) "
                  "ON CONFLICT(id) DO UPDATE SET email=excluded.email, name=excluded.name, "
                  "avatar=excluded.avatar, last_seen=excluded.last_seen",
                  (uid, info.get("email", ""), info.get("name") or info.get("email", "").split("@")[0],
                   info.get("picture", ""), now_iso(), now_iso()))
        c.execute("INSERT INTO sessions VALUES(?,?,?,?)",
                  (session, uid, now_iso(), exp.isoformat(timespec="seconds")))
        c.execute("INSERT OR IGNORE INTO prefs(user_id) VALUES(?)", (uid,))
    handler.send_response(302)
    handler.send_header("Location", nxt)
    secure = "; Secure" if base_url(handler).startswith("https") else ""
    handler.send_header("Set-Cookie", f"{COOKIE}={session}; Path=/; Max-Age={SESSION_DAYS*86400}; "
                                      f"HttpOnly; SameSite=Lax{secure}")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", "0")
    handler.end_headers()


def auth_logout(handler):
    tok = parse_cookies(handler.headers.get("Cookie")).get(COOKIE)
    if tok:
        with db() as c:
            c.execute("DELETE FROM sessions WHERE token=?", (tok,))
    body = b'{"ok": true}'
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Set-Cookie", f"{COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


# ------------------------------------------------------------ dish access ---
def _dish_public(row, lang_both=True):
    """Row → API dict (both languages)."""
    d = {
        "id": row["id"], "owner_id": row["owner_id"], "visibility": row["visibility"],
        "status": row["status"], "source_url": row["source_url"],
        "has_video": bool(row["has_video"]), "error": row["error"],
        "created_at": row["created_at"], "needs": json.loads(row["needs"] or "[]"),
    }
    for k in ("he", "en"):
        try:
            d[k] = json.loads(row[k]) if row[k] else None
        except Exception:
            d[k] = None
    return d


def get_prefs(uid):
    with db() as c:
        r = c.execute("SELECT * FROM prefs WHERE user_id=?", (uid,)).fetchone()
    if not r:
        return {"hidden": [], "hideBase": False, "muted": []}
    return {"hidden": json.loads(r["hidden"] or "[]"), "hideBase": bool(r["hide_base"]),
            "muted": json.loads(r["muted"] or "[]")}


def usage_today(uid):
    with db() as c:
        r = c.execute("SELECT n FROM usage WHERE user_id=? AND day=?", (uid, today())).fetchone()
    return r["n"] if r else 0


def _community(c, exclude_owner=None):
    """All public+ready dishes (with owner info) and the owners list."""
    owners, dishes = {}, []
    for r in c.execute(
            "SELECT d.*, u.name AS oname, u.avatar AS oavatar FROM dishes d JOIN users u ON u.id=d.owner_id "
            "WHERE d.visibility='public' AND d.status='ready' ORDER BY d.created_at DESC"):
        if r["owner_id"] == exclude_owner:
            continue
        o = owners.setdefault(r["owner_id"], {"id": r["owner_id"], "name": r["oname"], "avatar": r["oavatar"], "count": 0})
        o["count"] += 1
        d = _dish_public(r)
        d["owner"] = {"name": r["oname"], "avatar": r["oavatar"]}
        dishes.append(d)
    return dishes, sorted(owners.values(), key=lambda o: -o["count"])


def api_me(handler, user):
    if not user:
        with db() as c:
            community, owners = _community(c)
        return handler._json({"user": None, "configured": bool(secret("GOOGLE_CLIENT_ID")),
                              "included": community, "explore": owners})
    uid = user["id"]
    prefs = get_prefs(uid)
    with db() as c:
        mine = [_dish_public(r) for r in c.execute(
            "SELECT * FROM dishes WHERE owner_id=? ORDER BY created_at DESC", (uid,))]
        community, owners = _community(c, exclude_owner=uid)
        queued = 0
        if user.get("admin"):
            queued = c.execute("SELECT COUNT(*) FROM dishes WHERE status='queued'").fetchone()[0]
    muted = set(prefs["muted"])
    for o in owners:
        o["muted"] = o["id"] in muted
    included = [d for d in community if d["owner_id"] not in muted]
    return handler._json({
        "user": {"id": uid, "name": user["name"], "avatar": user["avatar"], "email": user["email"],
                 "admin": user.get("admin", False)},
        "prefs": prefs, "mine": mine, "included": included, "explore": owners,
        "usage": {"today": usage_today(uid), "limit": DAILY_LIMIT}, "queued": queued,
    })


def api_prefs(handler, user, req):
    if not user:
        return handler._json({"error": "sign in"}, 401)
    prefs = get_prefs(user["id"])
    if "hidden" in req and isinstance(req["hidden"], list):
        prefs["hidden"] = [str(x)[:32] for x in req["hidden"]][:2000]
    if "hideBase" in req:
        prefs["hideBase"] = bool(req["hideBase"])
    if "muted" in req and isinstance(req["muted"], list):
        prefs["muted"] = [str(x)[:64] for x in req["muted"]][:500]
    with db() as c:
        c.execute("INSERT INTO prefs(user_id,hidden,hide_base,muted) VALUES(?,?,?,?) "
                  "ON CONFLICT(user_id) DO UPDATE SET hidden=excluded.hidden, "
                  "hide_base=excluded.hide_base, muted=excluded.muted",
                  (user["id"], json.dumps(prefs["hidden"]), int(prefs["hideBase"]),
                   json.dumps(prefs["muted"])))
    return handler._json({"ok": True, "prefs": prefs})


def api_dish_get(handler, user, did):
    with db() as c:
        r = c.execute("SELECT * FROM dishes WHERE id=?", (did,)).fetchone()
    if not r:
        return handler._json({"error": "not found"}, 404)
    if r["visibility"] != "public" and (not user or (user["id"] != r["owner_id"] and not user.get("admin"))):
        return handler._json({"error": "forbidden"}, 403)
    return handler._json({"ok": True, "dish": _dish_public(r)})


URL_RE = re.compile(r"^https?://[^\s]+$")


def _norm_url(u):
    u = (u or "").strip()
    if not URL_RE.match(u) or len(u) > 1000:
        return None
    # strip tracking params from FB/IG share links
    try:
        pr = urllib.parse.urlsplit(u)
        if any(h in pr.netloc for h in ("facebook.com", "instagram.com", "fb.watch")):
            keep = [(k, v) for k, v in urllib.parse.parse_qsl(pr.query) if k in ("v", "story_fbid", "id")]
            u = urllib.parse.urlunsplit((pr.scheme, pr.netloc, pr.path, urllib.parse.urlencode(keep), ""))
    except Exception:
        pass
    return u.rstrip("/")


def api_dish_create(handler, user, req):
    """Accepts {url} or {urls:[...]} (bulk, up to 100). Enforces the daily cap,
    dedupes against the user's existing dishes."""
    if not user:
        return handler._json({"error": "sign in"}, 401)
    raw = req.get("urls") if isinstance(req.get("urls"), list) else [req.get("url")]
    urls, seen = [], set()
    for u in raw[:100]:
        n = _norm_url(str(u or ""))
        if n and n not in seen:
            seen.add(n); urls.append(n)
    if not urls:
        return handler._json({"error": "bad url"}, 400)
    if not secret("GEMINI_API_KEY"):
        return handler._json({"error": "extraction not configured"}, 503)
    uid = user["id"]
    with _LOCK:
        with db() as c:
            have = {(_norm_url(r["source_url"]) or r["source_url"]) for r in
                    c.execute("SELECT source_url FROM dishes WHERE owner_id=?", (uid,))}
            n = usage_today(uid)
            remaining = 10**6 if user.get("admin") else max(0, DAILY_LIMIT - n)
            ids, dupes, over = [], 0, 0
            for u in urls:
                if u in have:
                    dupes += 1; continue
                if len(ids) >= remaining:
                    over += 1; continue
                did = "u" + secrets.token_hex(5)
                c.execute("INSERT INTO dishes(id,owner_id,visibility,status,source_url,created_at,updated_at) "
                          "VALUES(?,?,?,?,?,?,?)", (did, uid, "private", "processing", u, now_iso(), now_iso()))
                have.add(u); ids.append(did)
            if ids:
                c.execute("INSERT INTO usage(user_id,day,n) VALUES(?,?,?) "
                          "ON CONFLICT(user_id,day) DO UPDATE SET n=n+excluded.n", (uid, today(), len(ids)))
    if not ids and over and not dupes:
        return handler._json({"error": "limit", "message": f"הגעת למכסה היומית ({DAILY_LIMIT} מנות ביום)"}, 429)
    for did in ids:
        start_processing(did)
    return handler._json({"ok": True, "ids": ids, "added": len(ids), "skipped_limit": over, "skipped_dupe": dupes,
                          "usage": {"today": n + len(ids), "limit": DAILY_LIMIT}})


def api_dish_action(handler, user, did, req):
    if not user:
        return handler._json({"error": "sign in"}, 401)
    with db() as c:
        r = c.execute("SELECT * FROM dishes WHERE id=?", (did,)).fetchone()
    if not r:
        return handler._json({"error": "not found"}, 404)
    if r["owner_id"] != user["id"] and not user.get("admin"):
        return handler._json({"error": "forbidden"}, 403)
    action = req.get("action")
    with db() as c:
        if action == "setVisibility" and req.get("visibility") in ("public", "private"):
            c.execute("UPDATE dishes SET visibility=?, updated_at=? WHERE id=?",
                      (req["visibility"], now_iso(), did))
        elif action == "delete":
            c.execute("DELETE FROM dishes WHERE id=?", (did,))
            for p in (os.path.join(VIDEOS_DIR, did + ".mp4"), os.path.join(UIMAGES_DIR, did + ".jpg")):
                try:
                    os.remove(p)
                except OSError:
                    pass
            return handler._json({"ok": True, "deleted": did})
        elif action == "retry" and r["status"] in ("failed", "queued"):
            c.execute("UPDATE dishes SET status='processing', error=NULL, updated_at=? WHERE id=?",
                      (now_iso(), did))
            c.commit()
            start_processing(did)
        elif action == "queue" and r["status"] == "failed":
            # fall back to the owner's manual pipeline (Claude on Eedo's Mac)
            c.execute("UPDATE dishes SET status='queued', updated_at=? WHERE id=?", (now_iso(), did))
        elif action == "edit" and r["status"] == "ready":
            he, en = r["he"], r["en"]
            if isinstance(req.get("he"), dict):
                he = json.dumps(_clean_lang(req["he"], "he"), ensure_ascii=False)
            if isinstance(req.get("en"), dict):
                en = json.dumps(_clean_lang(req["en"], "en"), ensure_ascii=False)
            c.execute("UPDATE dishes SET he=?, en=?, updated_at=? WHERE id=?", (he, en, now_iso(), did))
        else:
            return handler._json({"error": "unknown action"}, 400)
        row = c.execute("SELECT * FROM dishes WHERE id=?", (did,)).fetchone()
    return handler._json({"ok": True, "dish": _dish_public(row)})


def api_bulk_visibility(handler, user, req):
    if not user:
        return handler._json({"error": "sign in"}, 401)
    vis = req.get("visibility")
    if vis not in ("public", "private"):
        return handler._json({"error": "bad visibility"}, 400)
    with db() as c:
        c.execute("UPDATE dishes SET visibility=?, updated_at=? WHERE owner_id=?", (vis, now_iso(), user["id"]))
    return handler._json({"ok": True})


# --- admin: manual queue drained from the Mac via the /cookin skill ---
def api_admin_queue(handler, user):
    if not user or not user.get("admin"):
        return handler._json({"error": "forbidden"}, 403)
    with db() as c:
        rows = [dict(_dish_public(r), owner_name=r["name"], owner_email=r["email"],
                     has_image=os.path.exists(os.path.join(UIMAGES_DIR, r["id"] + ".jpg"))) for r in c.execute(
            "SELECT d.*, u.name, u.email FROM dishes d JOIN users u ON u.id=d.owner_id "
            "WHERE d.status IN ('queued','failed') ORDER BY d.created_at")]
        processing = c.execute("SELECT COUNT(*) FROM dishes WHERE status='processing'").fetchone()[0]
    return handler._json({"ok": True, "queue": rows, "processing": processing})


def api_admin_fill(handler, user, req):
    """Admin writes a finished dish (he/en/needs) for a queued id; video/image
    are uploaded separately (POST /api/admin/media)."""
    if not user or not user.get("admin"):
        return handler._json({"error": "forbidden"}, 403)
    did = str(req.get("id") or "")
    with db() as c:
        r = c.execute("SELECT * FROM dishes WHERE id=?", (did,)).fetchone()
        if not r:
            return handler._json({"error": "not found"}, 404)
        he = _clean_lang(req.get("he") or {}, "he")
        en = _clean_lang(req.get("en") or {}, "en")
        needs = [k for k in (req.get("needs") or []) if k in ingredient_keys()]
        has_video = os.path.exists(os.path.join(VIDEOS_DIR, did + ".mp4"))
        c.execute("UPDATE dishes SET he=?, en=?, needs=?, status='ready', error=NULL, has_video=?, updated_at=? "
                  "WHERE id=?", (json.dumps(he, ensure_ascii=False), json.dumps(en, ensure_ascii=False),
                                 json.dumps(needs), int(has_video), now_iso(), did))
        row = c.execute("SELECT * FROM dishes WHERE id=?", (did,)).fetchone()
    return handler._json({"ok": True, "dish": _dish_public(row)})


def api_admin_media(handler, user, qs):
    """PUT raw bytes: /api/admin/media?id=u123&kind=video|image"""
    if not user or not user.get("admin"):
        return handler._json({"error": "forbidden"}, 403)
    did = qs.get("id", [""])[0]
    kind = qs.get("kind", [""])[0]
    if not re.fullmatch(r"u[0-9a-f]{10}", did) or kind not in ("video", "image"):
        return handler._json({"error": "bad params"}, 400)
    n = int(handler.headers.get("Content-Length", 0))
    if n <= 0 or n > MAX_VIDEO_MB * 1024 * 1024:
        return handler._json({"error": "bad length"}, 400)
    dest = os.path.join(VIDEOS_DIR, did + ".mp4") if kind == "video" else os.path.join(UIMAGES_DIR, did + ".jpg")
    tmp = dest + ".part"
    with open(tmp, "wb") as f:
        left = n
        while left > 0:
            chunk = handler.rfile.read(min(1 << 20, left))
            if not chunk:
                break
            f.write(chunk)
            left -= len(chunk)
    os.replace(tmp, dest)
    if kind == "video":
        with db() as c:
            c.execute("UPDATE dishes SET has_video=1 WHERE id=?", (did,))
    return handler._json({"ok": True, "bytes": n})


# ------------------------------------------------------- ingredient keys ---
_ING = None


def ingredient_keys():
    """{key: (he_label, he_group, en_label)} parsed from site/data*.js."""
    global _ING
    if _ING is not None:
        return _ING
    out = {}
    rx = re.compile(r'^\s*"?([a-z0-9-]+)"?\s*:\s*\{\s*label\s*:\s*"([^"]*)"\s*,\s*group\s*:\s*"([^"]*)"', re.M)
    for f in sorted(glob.glob(os.path.join(SITE, "data*.js"))):
        is_en = f.endswith("-en.js")
        try:
            src = open(f, encoding="utf-8").read()
        except OSError:
            continue
        for m in rx.finditer(src):
            k, label, group = m.groups()
            cur = out.setdefault(k, ["", "", ""])
            if is_en:
                cur[2] = label
            else:
                cur[0], cur[1] = label, group
    _ING = {k: tuple(v) for k, v in out.items()}
    return _ING


def _clean_lang(d, lang):
    """Normalize one language variant to the RECIPES shape."""
    cats = CATS_HE if lang == "he" else CATS_EN
    diets = DIET_HE if lang == "he" else DIET_EN
    s = lambda k, n=300: str(d.get(k) or "").strip()[:n]
    lines, last_group = [], None
    for l in (d.get("ingredientLines") or [])[:80]:
        if isinstance(l, dict):
            g = str(l.get("group") or "").strip()[:120]
            t = str(l.get("text") or "").strip()[:300]
            # Gemini tends to repeat the group on every line: emit a header only when it changes
            if g and g != last_group:
                lines.append({"group": g}); last_group = g
            if t:
                lines.append({"text": t})
        elif isinstance(l, str) and l.strip():
            lines.append({"text": l.strip()[:300]})
    if len(lines) == 1 and "group" in lines[0]:
        lines = []
    steps = [str(x).strip()[:600] for x in (d.get("steps") or [])[:40] if str(x).strip()]
    cat = s("category")
    if cat not in cats:
        cat = cats[-2] if lang == "he" else cats[-2]
    diet = s("diet")
    if diet not in diets:
        diet = diets[-1]
    return {"name": s("name", 120), "intro": s("intro", 600), "time": s("time", 60), "serves": s("serves", 60),
            "creator": s("creator", 120), "category": cat, "diet": diet, "ingredientLines": lines,
            "steps": steps, "tips": s("tips", 800)}


# --------------------------------------------------------------- pipeline ---
_running = set()
_WORKERS = threading.Semaphore(int(os.environ.get("COOKIN_WORKERS", "2")))  # 512 MB box: don't run many yt-dlp/ffmpeg at once


def start_processing(did):
    with _LOCK:
        if did in _running:
            return
        _running.add(did)
    threading.Thread(target=_process_wrapper, args=(did,), daemon=True).start()


class BudgetExhausted(RuntimeError):
    pass


def _process_wrapper(did):
    try:
        with _WORKERS:
            process_dish(did)
    except BudgetExhausted as e:
        log(f"{did} QUEUED (gemini budget): {e}")
        with db() as c:
            c.execute("UPDATE dishes SET status='queued', error=?, updated_at=? WHERE id=?",
                      ("Gemini budget exhausted — sent to Eedo's manual queue", now_iso(), did))
    except Exception as e:
        log(f"{did} FAILED → queued: {e}\n{traceback.format_exc()}")
        with db() as c:
            c.execute("UPDATE dishes SET status='queued', error=?, updated_at=? WHERE id=?",
                      (str(e)[:500], now_iso(), did))
    finally:
        with _LOCK:
            _running.discard(did)


def _fail(did, msg):
    with db() as c:
        c.execute("UPDATE dishes SET status='failed', error=?, updated_at=? WHERE id=?", (msg, now_iso(), did))
        # refund the daily slot
        r = c.execute("SELECT owner_id, created_at FROM dishes WHERE id=?", (did,)).fetchone()
        if r:
            c.execute("UPDATE usage SET n=MAX(n-1,0) WHERE user_id=? AND day=?", (r["owner_id"], today()))


def _ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def _run(cmd, timeout=600):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "").strip()[-800:] or f"exit {p.returncode}")
    return p.stdout


def _is_av1(path):
    with open(path, "rb") as f:
        head = f.read(3 * 1024 * 1024)
    return b"av01" in head and b"avc1" not in head


def process_dish(did):
    with db() as c:
        r = c.execute("SELECT * FROM dishes WHERE id=?", (did,)).fetchone()
    if not r:
        return
    url = r["source_url"]
    log(f"{did} start {url}")
    tmp = tempfile.mkdtemp(prefix="cookin-")
    try:
        ff = _ffmpeg()
        cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-warnings",
               "-f", "b[vcodec^=avc1][ext=mp4]/bv*[vcodec^=avc1]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
               "--merge-output-format", "mp4",
               "--max-filesize", f"{MAX_VIDEO_MB}M", "--write-thumbnail", "--print-json",
               "-o", os.path.join(tmp, "v.%(ext)s"), url]
        if ff:
            cmd += ["--ffmpeg-location", os.path.dirname(ff)]
        out = _run(cmd, timeout=900)
        info = json.loads(out.strip().splitlines()[-1])
        video = None
        for f in os.listdir(tmp):
            if f.startswith("v.") and f.split(".")[-1] in ("mp4", "mkv", "webm", "mov"):
                video = os.path.join(tmp, f)
        thumb = None
        for f in os.listdir(tmp):
            if f.split(".")[-1].lower() in ("jpg", "jpeg", "webp", "png") and f.startswith("v."):
                thumb = os.path.join(tmp, f)
        if not video:
            raise RuntimeError("video download failed")
        # Safari can't play AV1 → transcode to H.264
        if (_is_av1(video) or not video.endswith(".mp4")) and ff:
            fixed = os.path.join(tmp, "fixed.mp4")
            _run([ff, "-y", "-i", video, "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                  "-vf", "scale='min(1080,iw)':-2", "-c:a", "aac", "-b:a", "128k",
                  "-movflags", "+faststart", fixed], timeout=1500)
            video = fixed
        if not thumb and ff:
            thumb = os.path.join(tmp, "thumb.jpg")
            _run([ff, "-y", "-ss", "1", "-i", video, "-frames:v", "1", thumb])
        caption = (info.get("description") or info.get("title") or "")[:6000]
        creator = info.get("uploader") or info.get("channel") or info.get("uploader_id") or ""
        canonical = info.get("webpage_url") or url

        data, tokens = gemini_extract(video, caption, creator, canonical)

        # persist media
        with open(video, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
        shutil.copyfile(video, os.path.join(VIDEOS_DIR, did + ".mp4.part"))
        os.replace(os.path.join(VIDEOS_DIR, did + ".mp4.part"), os.path.join(VIDEOS_DIR, did + ".mp4"))
        _save_thumb(thumb, os.path.join(UIMAGES_DIR, did + ".jpg"))
        he, en = _clean_lang(data.get("he") or {}, "he"), _clean_lang(data.get("en") or {}, "en")
        if not he.get("creator"):
            he["creator"] = creator
        if not en.get("creator"):
            en["creator"] = creator
        # keep category/diet consistent across languages (trust Hebrew)
        en["category"] = CAT_HE2EN.get(he["category"], en["category"])
        en["diet"] = DIET_HE2EN.get(he["diet"], en["diet"])
        keys = ingredient_keys()
        needs = [k for k in dict.fromkeys(data.get("needs") or []) if k in keys][:30]
        with db() as c:
            c.execute("UPDATE dishes SET he=?, en=?, needs=?, has_video=1, status='ready', error=NULL, "
                      "source_url=?, tokens=?, updated_at=? WHERE id=?",
                      (json.dumps(he, ensure_ascii=False), json.dumps(en, ensure_ascii=False),
                       json.dumps(needs), canonical, tokens, now_iso(), did))
        log(f"{did} ready: {he['name']} ({size//1024} KB, {tokens} tokens)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _save_thumb(src, dest):
    try:
        from PIL import Image
        im = Image.open(src).convert("RGB")
        w, h = im.size
        if max(w, h) > 900:
            k = 900 / max(w, h)
            im = im.resize((int(w * k), int(h * k)))
        im.save(dest + ".part", "JPEG", quality=82, optimize=True)
        os.replace(dest + ".part", dest)
    except Exception as e:
        log(f"thumb convert failed ({e}); copying raw")
        if src:
            shutil.copyfile(src, dest)


# ----------------------------------------------------------------- gemini ---
def _gemini_upload(path, key):
    size = os.path.getsize(path)
    start = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={key}",
        data=json.dumps({"file": {"display_name": os.path.basename(path)}}).encode(),
        headers={"X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                 "X-Goog-Upload-Header-Content-Length": str(size),
                 "X-Goog-Upload-Header-Content-Type": "video/mp4",
                 "Content-Type": "application/json"})
    upload_url = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(start, timeout=60) as r:
                upload_url = r.headers.get("X-Goog-Upload-URL")
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:500]
            if e.code == 429 and "spending cap" in body:
                raise BudgetExhausted(body)
            if e.code in (429, 500, 503) and attempt < 2:
                time.sleep(8 * (attempt + 1)); continue
            raise RuntimeError(f"gemini upload {e.code}: {body}")
    if not upload_url:
        raise RuntimeError("gemini upload: no upload url")
    with open(path, "rb") as f:
        data = f.read()
    up = urllib.request.Request(upload_url, data=data, method="POST",
                                headers={"Content-Length": str(size), "X-Goog-Upload-Offset": "0",
                                         "X-Goog-Upload-Command": "upload, finalize"})
    with urllib.request.urlopen(up, timeout=600) as r:
        finfo = json.loads(r.read().decode())["file"]
    # wait until ACTIVE
    for _ in range(90):
        if finfo.get("state") == "ACTIVE":
            break
        time.sleep(2)
        with urllib.request.urlopen(f"https://generativelanguage.googleapis.com/v1beta/{finfo['name']}?key={key}",
                                    timeout=30) as r:
            finfo = json.loads(r.read().decode())
        if finfo.get("state") == "FAILED":
            raise RuntimeError("gemini file processing failed")
    return finfo


def _gemini_delete(name, key):
    try:
        req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/{name}?key={key}",
                                     method="DELETE")
        urllib.request.urlopen(req, timeout=30).read()
    except Exception:
        pass


LANG_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"}, "intro": {"type": "STRING"}, "time": {"type": "STRING"},
        "serves": {"type": "STRING"}, "creator": {"type": "STRING"},
        "category": {"type": "STRING"}, "diet": {"type": "STRING"},
        "ingredientLines": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "group": {"type": "STRING"}, "text": {"type": "STRING"}}}},
        "steps": {"type": "ARRAY", "items": {"type": "STRING"}},
        "tips": {"type": "STRING"},
    },
    "required": ["name", "category", "diet", "ingredientLines", "steps"],
}
SCHEMA_JSON = {"type": "OBJECT", "properties": {"he": LANG_SCHEMA, "en": LANG_SCHEMA,
                                                "needs": {"type": "ARRAY", "items": {"type": "STRING"}}},
               "required": ["he", "en", "needs"]}


def _prompt(caption, creator, url):
    keys = ingredient_keys()
    klist = "\n".join(f"- {k}: {v[0]}" + (f" / {v[2]}" if v[2] else "") for k, v in sorted(keys.items()))
    return f"""You are the recipe editor of "Cookin", a Hebrew family recipe book built from cooking reels.
Watch the attached video carefully (what is cooked, ingredients shown, quantities said or written on screen)
and read the caption below. Produce ONE structured recipe in TWO languages: Hebrew ("he") and English ("en").

Caption / description from the post:
\"\"\"{caption}\"\"\"
Creator handle (if known): {creator}
Source: {url}

Rules:
- "he": everything in natural Israeli Hebrew (RTL). "en": the same recipe in natural English.
- name: short dish name (Hebrew name in he, English name in en). Do not include the creator's name.
- intro: 1 sentence of context/why it's great (may mention the creator by name).
- time: total time, e.g. "25 דק'" / "25 min". serves: e.g. "4 מנות" / "Serves 4". Leave "" if unknown.
- creator: the creator's display name or handle as written (same string in both languages).
- category (he) MUST be exactly one of: {", ".join(CATS_HE)}.
  category (en) MUST be the matching one of: {", ".join(CATS_EN)}.
- diet (he) MUST be one of: בשרי (contains meat/poultry), דגים (fish/seafood, no meat), צמחוני (no meat or fish).
  diet (en) the matching one of: Meat, Fish, Vegetarian.
- ingredientLines: list of {{"text": "quantity + ingredient"}} items; use {{"group": "..."}} items only to
  separate sub-recipes (e.g. sauce vs. main). Quantities in metric (grams, ml, cups, tbsp/tsp).
  If the video has NO quantities, estimate sensible ones and say so in intro (Hebrew: "כמויות משוערות").
- steps: numbered cooking steps as clear imperative sentences, 4-12 steps.
- tips: substitutions and tips (from caption/comments or common sense). "" if none.
- If wheat flour, breadcrumbs, semolina, noodles or dumpling wrappers are used, make sure the matching
  ingredient key appears in needs (gluten detection is key-based).
- needs: the list of ingredient KEYS (from the allowed list below) that this dish requires — only the
  main ingredients, skip salt/pepper/oil/water/sugar. Use ONLY keys from this list, 3-12 keys:
{klist}
Return only JSON matching the schema."""


def gemini_extract(video_path, caption, creator, url):
    key = secret("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")
    finfo = _gemini_upload(video_path, key)
    try:
        body = {
            "contents": [{"role": "user", "parts": [
                {"file_data": {"mime_type": finfo.get("mimeType", "video/mp4"), "file_uri": finfo["uri"]}},
                {"text": _prompt(caption, creator, url)}]}],
            "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json",
                                 "response_schema": SCHEMA_JSON, "maxOutputTokens": 8192},
        }
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}",
            data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        last = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    res = json.loads(r.read().decode())
                break
            except urllib.error.HTTPError as e:
                last = e.read().decode()[:500]
                if e.code == 429 and "spending cap" in last:
                    raise BudgetExhausted(last)
                if e.code in (429, 500, 503) and attempt < 2:
                    time.sleep(8 * (attempt + 1))
                    continue
                raise RuntimeError(f"gemini {e.code}: {last}")
        text = res["candidates"][0]["content"]["parts"][0]["text"]
        tokens = int((res.get("usageMetadata") or {}).get("totalTokenCount") or 0)
        data = json.loads(text)
        if not isinstance(data, dict) or "he" not in data:
            raise RuntimeError("gemini returned no recipe")
        return data, tokens
    finally:
        _gemini_delete(finfo["name"], key)


# ------------------------------------------------------- dynamic dish page ---
DISH_CSS = """
:root{--bg:#faf7f2;--card:#fff;--ink:#2b2420;--muted:#8a7f74;--accent:#e07a3f;--accent-dark:#c05f28;
--amber:#b7791f;--amber-bg:#fdf3e0;--line:#eee5d8;--chip:#f3ece1;
--shadow:0 2px 10px rgba(80,60,40,.08),0 10px 30px rgba(80,60,40,.06);}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,"Segoe UI",Rubik,Arial,sans-serif;padding:18px 16px 60px}
.wrap{max-width:980px;margin:0 auto}
.topbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:16px}
.back{display:inline-block;background:var(--chip);border-radius:999px;padding:9px 20px;font-weight:700;
color:var(--ink);text-decoration:none}
.back:hover{background:#eadfce}
.own{display:flex;gap:8px;margin-inline-start:auto;flex-wrap:wrap}
.own button{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:8px 14px;cursor:pointer;
font-family:inherit;font-size:.9rem;color:var(--ink)}
.own button.danger{color:#a53a2c;border-color:#f0c9c2}
.own button.pub{background:#e4f3e4;border-color:#bfe0c1;color:#2f6b34}
.dish{background:var(--card);border-radius:20px;box-shadow:var(--shadow);border:1px solid var(--line);overflow:hidden;display:flex;flex-direction:column}
.dimg{width:100%}
.dimg img{width:100%;object-fit:cover;display:block;min-height:260px;max-height:460px}
.dimg video{width:100%;object-fit:contain;background:#111;display:block;min-height:260px;max-height:480px}
.dmain{display:flex;flex-direction:column;min-width:0}
.dhead{padding:24px 28px;display:flex;flex-direction:column;gap:12px}
h1{font-size:1.6rem;line-height:1.3}
.dsub{color:var(--muted);font-size:.95rem}
.badge{display:inline-block;background:var(--chip);border-radius:6px;padding:2px 10px;font-size:.8rem;color:#6b5d4f;margin-inline-end:6px}
.diet-meat{background:#fbe3e0;color:#a53a2c}.diet-fish{background:#e0eefb;color:#2b5f96}.diet-veg{background:#e4f3e4;color:#3a7a3f}
.dnote{font-size:.9rem;color:var(--muted);background:var(--chip);border-radius:10px;padding:10px 14px;line-height:1.5}
.dbody{display:grid;grid-template-columns:340px 1fr;border-top:1px solid var(--line)}
@media(max-width:820px){.dbody{grid-template-columns:1fr}}
.ingcol{padding:24px 28px;border-inline-end:1px solid var(--line);background:#fffdf9}
@media(max-width:820px){.ingcol{border-inline-end:0;border-bottom:1px solid var(--line)}}
.stepcol{padding:24px 28px}
h3{font-size:1.1rem;margin-bottom:14px;color:var(--accent-dark)}
.ing-list{list-style:none;display:flex;flex-direction:column;gap:8px}
.ing-list li{display:flex;gap:10px;font-size:.96rem;line-height:1.45}
.ing-list li::before{content:"•";color:var(--accent);font-weight:700}
.ing-group{font-weight:700;margin-top:10px;color:#6b5d4f;font-size:.9rem}
.steps{list-style:none;counter-reset:st;display:flex;flex-direction:column;gap:14px}
.steps li{counter-increment:st;display:flex;gap:12px;line-height:1.6;font-size:.98rem}
.steps li::before{content:counter(st);flex:0 0 26px;height:26px;border-radius:50%;background:var(--accent);
color:#fff;display:flex;align-items:center;justify-content:center;font-size:.85rem;font-weight:700;margin-top:2px}
.tips{margin-top:20px;background:var(--amber-bg);border-radius:12px;padding:14px 16px;font-size:.92rem;line-height:1.6}
.tips b{color:var(--amber)}
.origlink{margin-top:22px;padding-top:14px;border-top:1px dashed var(--line);font-size:.85rem;color:var(--muted);line-height:1.5;word-break:break-all}
.origlink a{color:var(--accent-dark)}
.owner{display:flex;align-items:center;gap:8px;font-size:.85rem;color:var(--muted)}
.owner img{width:22px;height:22px;border-radius:50%}
@media(min-width:1020px){
html,body{height:100%;overflow:hidden}
body{padding:14px 18px}
.wrap{max-width:1360px;height:100%;display:flex;flex-direction:column}
.topbar{margin-bottom:10px}
.dish{flex:1;min-height:0;display:grid;grid-template-columns:auto minmax(0,1fr)}
.dimg{width:clamp(280px,44vh,440px);height:100%;border-inline-end:1px solid var(--line)}
.dimg video,.dimg img{height:100%;max-height:none;min-height:0}
.dmain{min-height:0}
.dhead{flex:0 0 auto;padding:18px 26px 14px;gap:8px}
h1{font-size:1.45rem}
.dbody{flex:1;min-height:0}
.ingcol,.stepcol{overflow-y:auto;scrollbar-width:thin}
}
"""

T = {
    "he": {"back": "→ חזרה לכל המתכונים 🍳", "by": "מאת", "ing": "🧺 מצרכים", "steps": "👨‍🍳 אופן ההכנה",
           "tips": "💡 טיפים:", "orig": "🎬 הסרטון המקורי:", "public": "🌍 ציבורי", "private": "🔒 פרטי",
           "make_public": "🌍 הפוך לציבורי", "make_private": "🔒 הפוך לפרטי", "delete": "🗑 מחיקה",
           "confirm": "למחוק את המנה לצמיתות?", "home": "/", "other": "/d/{id}?lang=en", "flag": "🇺🇸",
           "processing": "המנה עדיין בהכנה…", "failed": "העיבוד נכשל", "queued": "ממתין לטיפול ידני של אידו",
           "diet_cls": {"בשרי": "diet-meat", "דגים": "diet-fish", "צמחוני": "diet-veg"},
           "diet_emoji": {"בשרי": "🥩", "דגים": "🐟", "צמחוני": "🥦"}, "dir": "rtl", "lang": "he"},
    "en": {"back": "← Back to all recipes 🍳", "by": "By", "ing": "🧺 Ingredients", "steps": "👨‍🍳 Instructions",
           "tips": "💡 Tips:", "orig": "🎬 Original video:", "public": "🌍 Public", "private": "🔒 Private",
           "make_public": "🌍 Make public", "make_private": "🔒 Make private", "delete": "🗑 Delete",
           "confirm": "Delete this dish permanently?", "home": "/en.html", "other": "/d/{id}", "flag": "🇮🇱",
           "processing": "This dish is still being prepared…", "failed": "Processing failed",
           "queued": "Waiting for Eedo's manual pipeline",
           "diet_cls": {"Meat": "diet-meat", "Fish": "diet-fish", "Vegetarian": "diet-veg"},
           "diet_emoji": {"Meat": "🥩", "Fish": "🐟", "Vegetarian": "🥦"}, "dir": "ltr", "lang": "en"},
}


def dish_page(handler, user, did, qs):
    lang = "en" if qs.get("lang", [""])[0] == "en" else "he"
    t = T[lang]
    e = _html.escape
    with db() as c:
        r = c.execute("SELECT d.*, u.name AS oname, u.avatar AS oavatar FROM dishes d "
                      "LEFT JOIN users u ON u.id=d.owner_id WHERE d.id=?", (did,)).fetchone()
    if not r:
        return handler._html(f"<!doctype html><meta charset=utf-8><p style='font-family:sans-serif;padding:40px'>"
                             f"Dish not found. <a href='/'>Cookin</a></p>", "no-store")
    is_owner = bool(user) and (user["id"] == r["owner_id"] or user.get("admin"))
    if r["visibility"] != "public" and not is_owner:
        handler.send_response(302)
        handler.send_header("Location", "/auth/login?next=" + urllib.parse.quote(handler.path))
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return
    d = _dish_public(r)
    rec = d.get(lang) or d.get("he") or {}
    other_link = t["other"].format(id=did)
    own = ""
    if is_owner:
        vis = r["visibility"]
        own = f"""<div class="own">
  <span class="badge">{t['public'] if vis == 'public' else t['private']}</span>
  <button class="{'pub' if vis != 'public' else ''}" onclick="act('setVisibility','{'private' if vis == 'public' else 'public'}')">{t['make_private'] if vis == 'public' else t['make_public']}</button>
  <button class="danger" onclick="if(confirm({json.dumps(t['confirm'], ensure_ascii=False)}))act('delete')">{t['delete']}</button>
</div>"""
    if r["status"] != "ready":
        msg = {"processing": t["processing"], "failed": t["failed"], "queued": t["queued"]}.get(r["status"], r["status"])
        err = f"<div class='dnote'>{e(r['error'] or '')}</div>" if r["error"] else ""
        body = f"""<!DOCTYPE html><html lang="{t['lang']}" dir="{t['dir']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Cookin 🍳</title><style>{DISH_CSS}</style></head>
<body><div class="wrap"><div class="topbar"><a class="back" href="{t['home']}">{t['back']}</a>{own}</div>
<div class="dish"><div class="dhead"><h1>{msg}</h1>{err}<div class="dsub">{e(r['source_url'] or '')}</div></div></div></div>
<script>{_ACT_JS}</script></body></html>"""
        return handler._html(body, "no-store")
    hero = (f'<video controls playsinline preload="metadata" poster="/images/{did}.jpg" src="/videos/{did}.mp4"></video>'
            if r["has_video"] else f'<img src="/images/{did}.jpg" alt="">')
    ing = "\n".join(f'<div class="ing-group">{e(l["group"])}</div>' if l.get("group") else f'<li>{e(l.get("text", ""))}</li>'
                    for l in rec.get("ingredientLines", []))
    steps = "\n".join(f"<li><span>{e(s)}</span></li>" for s in rec.get("steps", []))
    diet = rec.get("diet", "")
    cls = t["diet_cls"].get(diet, "")
    emoji = t["diet_emoji"].get(diet, "")
    meta = " · ".join(x for x in (f"{t['by']} {e(rec.get('creator', ''))}" if rec.get("creator") else "",
                                  e(rec.get("serves", "")), f"⏱ {e(rec['time'])}" if rec.get("time") else "") if x)
    owner_html = ""
    if r["oname"]:
        av = f'<img src="{e(r["oavatar"])}" alt="" referrerpolicy="no-referrer">' if r["oavatar"] else ""
        owner_html = f'<div class="owner">{av}<span>{e(r["oname"])}</span></div>'
    src = r["source_url"] or ""
    body = f"""<!DOCTYPE html>
<html lang="{t['lang']}" dir="{t['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(rec.get('name', ''))} — Cookin 🍳</title>
<meta property="og:title" content="{e(rec.get('name', ''))}">
<meta property="og:image" content="/images/{did}.jpg">
<style>{DISH_CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="topbar"><a class="back" href="{t['home']}">{t['back']}</a>
    <a class="back" href="{other_link}" title="language">{t['flag']}</a>{own}</div>
  <div class="dish">
    <div class="dimg">{hero}</div>
    <div class="dmain">
      <div class="dhead">
        <h1>{e(rec.get('name', ''))}</h1>
        <div class="dsub">{meta}</div>
        <div><span class="badge {cls}">{emoji} {e(diet)}</span><span class="badge">{e(rec.get('category', ''))}</span></div>
        {owner_html}
        {f'<div class="dnote">{e(rec["intro"])}</div>' if rec.get('intro') else ''}
      </div>
      <div class="dbody">
        <div class="ingcol"><h3>{t['ing']}</h3><ul class="ing-list">{ing}</ul></div>
        <div class="stepcol">
          <h3>{t['steps']}</h3><ol class="steps">{steps}</ol>
          {f'<div class="tips"><b>{t["tips"]}</b> {e(rec["tips"])}</div>' if rec.get('tips') else ''}
          <div class="origlink">{t['orig']} <a href="{e(src)}" target="_blank" rel="noopener">{e(src.replace('https://www.', ''))}</a></div>
        </div>
      </div>
    </div>
  </div>
</div>
<script>{_ACT_JS}</script>
</body>
</html>"""
    return handler._html(body, "no-store")


_ACT_JS = """
async function act(action, visibility){
  const id = location.pathname.split('/').pop();
  const r = await fetch('/api/dishes/'+id, {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action, visibility})});
  const j = await r.json();
  if(action==='delete' && j.ok){ location.href = document.documentElement.lang==='en' ? '/en.html' : '/'; return; }
  location.reload();
}
"""


# ------------------------------------------------------------------ routes ---
def handle_get(handler, path, qs):
    """Return True if handled."""
    if path == "/auth/login":
        auth_login(handler, qs); return True
    if path == "/auth/callback":
        auth_callback(handler, qs); return True
    if path == "/api/me":
        api_me(handler, current_user(handler)); return True
    if path.startswith("/api/dishes/"):
        api_dish_get(handler, current_user(handler), path.rsplit("/", 1)[1]); return True
    if path == "/api/admin/queue":
        api_admin_queue(handler, current_user(handler)); return True
    if path.startswith("/d/"):
        did = path[3:].strip("/")
        if re.fullmatch(r"u[0-9a-f]{10}", did):
            dish_page(handler, current_user(handler), did, qs); return True
    return False


def handle_post(handler, path, qs, read_json):
    if path == "/auth/logout":
        auth_logout(handler); return True
    if path == "/api/prefs":
        api_prefs(handler, current_user(handler), read_json()); return True
    if path == "/api/dishes":
        api_dish_create(handler, current_user(handler), read_json()); return True
    if path == "/api/dishes/bulk-visibility":
        api_bulk_visibility(handler, current_user(handler), read_json()); return True
    if path.startswith("/api/dishes/"):
        api_dish_action(handler, current_user(handler), path.rsplit("/", 1)[1], read_json()); return True
    if path == "/api/admin/fill":
        api_admin_fill(handler, current_user(handler), read_json()); return True
    return False


def handle_put(handler, path, qs):
    if path == "/api/admin/media":
        api_admin_media(handler, current_user(handler), qs); return True
    return False


def user_media_path(path):
    """Map /images/u*.jpg and /videos/u*.mp4 to the persistent disk; None otherwise."""
    name = os.path.basename(path)
    if path.startswith("/images/") and re.fullmatch(r"u[0-9a-f]{10}\.jpg", name):
        return os.path.join(UIMAGES_DIR, name)
    return None
