"""Visitor traffic log for the portal: every HTML page load is counted per day by class (human / bot-UA), country and device, with the top
user agents and the busiest bot IPs; a client-side beacon counts the loads that showed real interaction ("engaged"). Aggregates only, persisted
to DATA_DIR/traffic.json. Also decides whether the Google Analytics tag is served at all (never for bot user agents)."""
import json, os, re, threading, time

import multiuser

PATH = os.path.join(multiuser.DATA_DIR, "traffic.json")
LOCK = threading.Lock()
KEEP_DAYS = 45
BOT_RE = re.compile(r"bot|crawl|spider|slurp|preview|headless|phantom|python|curl|wget|httpclient|http-client|go-http|java/|okhttp|libwww|scrapy|"
                    r"monitor|uptime|pingdom|lighthouse|gtmetrix|semrush|ahrefs|mj12|dataforseo|bytespider|petalbot|facebookexternalhit|embedly|"
                    r"whatsapp|telegram|discord|slack|twitterbot|linkedin|pinterest|applebot|duckduck|yandex|baidu|bingpreview|"
                    r"gptbot|claude|perplexity|ccbot|amazonbot|chatgpt|axios|node-fetch|aiohttp|requests|postman|insomnia", re.I)
_D = {}
_dirty = False
_last = 0.0


def _load():
    global _D
    try:
        with open(PATH, encoding="utf-8") as f:
            _D = json.load(f)
    except (OSError, ValueError):
        _D = {}


_load()


def is_bot_ua(ua):
    return not ua or len(ua) < 20 or bool(BOT_RE.search(ua))


def _ip(h):
    return ((h.get("CF-Connecting-IP") or (h.get("X-Forwarded-For") or "").split(",")[0] or "").strip()) or "?"


def _bump(d, k, n=1):
    d[k] = d.get(k, 0) + n


def _day():
    return time.strftime("%Y-%m-%d", time.gmtime())


def _row():
    r = _D.setdefault(_day(), {"human": 0, "bot": 0, "engaged": 0, "ga_served": 0, "country": {}, "bot_country": {}, "device": {}, "ua": {}, "bot_ip": {}, "hours": {}, "paths": {}})
    return r


def record(handler, path, ga_served):
    """One HTML page load. Humans are counted without any IP; bot IPs are kept (top few) to spot datacenters."""
    global _dirty
    h = handler.headers
    ua = h.get("User-Agent") or ""
    bot = is_bot_ua(ua) or not (h.get("Accept-Language") or "")
    cc = (h.get("CF-IPCountry") or "?").upper()
    with LOCK:
        r = _row()
        _bump(r, "bot" if bot else "human")
        _bump(r["bot_country" if bot else "country"], cc)
        if not bot:
            _bump(r["device"], "mobile" if re.search(r"Mobi|Android|iPhone|iPad", ua) else "desktop")
        _bump(r["ua"], ("BOT " if bot else "") + ua[:110])
        _bump(r["hours"], time.strftime("%H", time.gmtime()))
        _bump(r["paths"], (path or "/")[:60])
        if bot:
            _bump(r["bot_ip"], _ip(h))
        if ga_served:
            _bump(r, "ga_served")
        _dirty = True
    _flush()


def engaged(handler):
    """The page's script saw a real interaction (pointer, key, scroll, touch) or 8 s of visible time."""
    global _dirty
    with LOCK:
        r = _row()
        _bump(r, "engaged")
        _bump(r.setdefault("eng_device", {}), "mobile" if re.search(r"Mobi|Android|iPhone|iPad", handler.headers.get("User-Agent") or "") else "desktop")
        _dirty = True
    _flush()


def _flush(force=False):
    global _dirty, _last
    if not _dirty or (not force and time.time() - _last < 60):
        return
    with LOCK:
        for d in sorted(_D)[:-KEEP_DAYS]:
            del _D[d]
        for r in _D.values():
            for k in ("ua", "bot_ip", "paths"):
                if len(r.get(k, {})) > 60:
                    r[k] = dict(sorted(r[k].items(), key=lambda kv: -kv[1])[:40])
        tmp = PATH + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(_D, f, ensure_ascii=False)
            os.replace(tmp, PATH)
        except OSError:
            return
        _dirty, _last = False, time.time()


def report(days=7):
    _flush(True)
    ds = sorted(_D)[-days:]
    tot = {"human": 0, "bot": 0, "engaged": 0, "ga_served": 0}
    agg = {k: {} for k in ("country", "bot_country", "device", "eng_device", "ua", "bot_ip", "hours", "paths")}
    for d in ds:
        r = _D[d]
        for k in tot:
            tot[k] += r.get(k, 0)
        for k in agg:
            for a, n in r.get(k, {}).items():
                _bump(agg[k], a, n)
    top = lambda m, n=15: sorted(m.items(), key=lambda kv: -kv[1])[:n]
    loads = tot["human"] + tot["bot"]
    return {"days": ds, "loads": loads, "human_loads": tot["human"], "bot_loads": tot["bot"], "bot_share": round(tot["bot"] / loads, 3) if loads else 0,
            "engaged": tot["engaged"], "engaged_of_human": round(tot["engaged"] / tot["human"], 3) if tot["human"] else 0, "ga_served": tot["ga_served"],
            "per_day": {d: {k: _D[d].get(k, 0) for k in ("human", "bot", "engaged")} for d in ds},
            "human_countries": top(agg["country"]), "bot_countries": top(agg["bot_country"]), "device_human": top(agg["device"]), "device_engaged": top(agg["eng_device"]),
            "top_uas": top(agg["ua"], 25), "top_bot_ips": top(agg["bot_ip"], 15), "hours_utc": sorted(agg["hours"].items()), "top_paths": top(agg["paths"], 15)}
