"""Bernard: family shopping list API (served at /bernard/api/*). State on the persistent disk.
Shared by the Render app (app.py) and the local dev server (~/.claude/scripts/bernard/server.py)."""
import json, os, re, threading, time, uuid
from bernard_classify import classify, SECTIONS, SEC_IDS

LOCK = threading.Lock()
MAX_ITEMS, MAX_USERDB = 400, 2000
_s = {}

def init(base_db_path, state_dir):
    os.makedirs(state_dir, exist_ok=True)
    _s["state_p"] = os.path.join(state_dir, "bernard_state.json")
    _s["user_p"] = os.path.join(state_dir, "bernard_user_db.json")
    _s["state"] = _load(_s["state_p"], {"rev": 0, "items": []})
    _s["user"] = _load(_s["user_p"], [])
    _s["base"] = _load(base_db_path, [])

def _load(p, d):
    try:
        with open(p, encoding="utf8") as f: return json.load(f)
    except Exception: return d

def _save(p, o):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf8") as f: json.dump(o, f, ensure_ascii=False)
    os.replace(tmp, p)

def _norm(s): return re.sub(r"\s+", " ", re.sub(r"[\"'׳״]", "", s or "")).strip().lower()
def _is_he(s): return bool(re.search(r"[א-ת]", s))
def _lookup(name):
    k = _norm(name)
    for e in _s["user"] + _s["base"]:
        if _norm(e.get("he")) == k or _norm(e.get("en")) == k: return e
def _bump(): _s["state"]["rev"] += 1; _save(_s["state_p"], _s["state"])

def handle_get(h, p):
    if p == "/bernard/api/db": h._json({"sections": SECTIONS, "db": _s["user"] + _s["base"]}); return True
    if p == "/bernard/api/state": h._json(_s["state"]); return True
    return False

def handle_post(h, p, d):
    if not p.startswith("/bernard/api/"): return False
    p = p[len("/bernard/api"):]; who = str(d.get("who") or "").strip()[:30]; st = _s["state"]
    with LOCK:
        if p == "/add":
            name = re.sub(r"\s+", " ", str(d.get("name") or "")).strip()[:60]
            if not name: h._json({"error": "empty"}, 400); return True
            e = _lookup(name); new = False
            if e: sec = e["sec"]; he, en = e.get("he", ""), e.get("en", "")
            else:
                if len(_s["user"]) >= MAX_USERDB: h._json({"error": "db full"}, 429); return True
                sec = classify(name); new = True
                he, en = (name, "") if _is_he(name) else ("", name)
                _s["user"].insert(0, {"he": he, "en": en, "sec": sec, "src": "user"}); _save(_s["user_p"], _s["user"])
            label = name
            if e: label = (he if _is_he(name) and he else en if not _is_he(name) and en else he or en) or name
            dup = next((i for i in st["items"] if not i["done"] and _norm(i["name"]) == _norm(label)), None)
            if dup: dup["qty"] = min(99, dup.get("qty", 1) + 1); _bump(); h._json({"item": dup, "dup": True, "new": False}); return True
            if len(st["items"]) >= MAX_ITEMS: h._json({"error": "list full"}, 429); return True
            it = {"id": uuid.uuid4().hex[:8], "name": label, "he": he, "en": en, "sec": sec, "qty": 1, "by": who, "at": int(time.time()), "done": False, "doneBy": "", "doneAt": 0}
            st["items"].append(it); _bump(); h._json({"item": it, "new": new}); return True
        it = next((i for i in st["items"] if i["id"] == d.get("id")), None)
        if p == "/toggle" and it:
            it["done"] = not it["done"]; it["doneBy"] = who if it["done"] else ""; it["doneAt"] = int(time.time()) if it["done"] else 0
            _bump(); h._json({"item": it}); return True
        if p == "/remove" and it: st["items"].remove(it); _bump(); h._json({"ok": True}); return True
        if p == "/qty" and it:
            try: q = int(d.get("qty") or 1)
            except Exception: q = 1
            it["qty"] = max(1, min(99, q)); _bump(); h._json({"item": it}); return True
        if p == "/clear": st["items"] = [i for i in st["items"] if not i["done"]]; _bump(); h._json({"ok": True}); return True
    h._json({"error": "not found"}, 404); return True
