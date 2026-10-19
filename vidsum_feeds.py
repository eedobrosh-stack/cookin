# -*- coding: utf-8 -*-
"""Podcast-feed sources for Pawed: turn any page / feed URL / show name into an RSS feed and read its episodes.

resolve_feed(ref, name)  -> {"id", "feed_url", "name", "image", "language"}   (raises ValueError with a user-facing hint)
parse_feed(xml_text)     -> {"title", "image", "language", "items": [{"guid", "title", "link", "audio", "published_at",
                              "duration", "description", "image"}]}
episode_id(item)         -> 11-char id ("r" + 10 hex) that fits everywhere a YouTube video id is used
"""
import datetime
import email.utils
import hashlib
import html as _html
import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# full browser headers: some publisher sites (e.g. mako.co.il) answer 403 to anything that does not look like Chrome
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "he-IL,he;q=0.9,en;q=0.8", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none",
      "Upgrade-Insecure-Requests": "1"}
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
MAX_BYTES = 8_000_000


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(MAX_BYTES)
        enc = r.headers.get_content_charset() or "utf-8"
    return raw.decode(enc, "replace")


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", " ", s)


def _words(s):
    return {w for w in _norm(s).split() if len(w) > 1}


def overlap(a, b):
    A, B = _words(a), _words(b)
    return len(A & B) / max(1, min(len(A), len(B)))


def looks_like_feed(text):
    head = (text or "")[:3000].lower()
    return "<rss" in head or "<feed" in head or "<rdf:rdf" in head


def feed_id(feed_url):
    return "rss:" + hashlib.sha1(feed_url.strip().lower().encode()).hexdigest()[:12]


def episode_id(item):
    return "r" + hashlib.sha1((item.get("guid") or item.get("audio") or item.get("title") or "").encode()).hexdigest()[:10]


def _dur(s):
    if not s:
        return None
    s = s.strip()
    try:
        if ":" in s:
            parts = [int(float(x)) for x in s.split(":")]
            sec = 0
            for p in parts:
                sec = sec * 60 + p
            return sec
        return int(float(s))
    except ValueError:
        return None


def _iso(pub):
    try:
        d = email.utils.parsedate_to_datetime(pub)
        if d.tzinfo is None:
            d = d.replace(tzinfo=datetime.timezone.utc)
        return d.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def _strip(html_text):
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", html_text or ""))).strip()


def parse_feed(xml_text):
    root = ET.fromstring(xml_text.lstrip("﻿").encode("utf-8"))
    ch = root.find("channel")
    if ch is None:
        raise ValueError("not an RSS podcast feed")
    img = ch.find(ITUNES + "image")
    out = {"title": _strip(ch.findtext("title") or ""), "language": (ch.findtext("language") or "")[:2].lower(),
           "image": (img.get("href") if img is not None else None) or ch.findtext("image/url") or "", "items": []}
    for it in ch.findall("item"):
        enc = it.find("enclosure")
        audio = enc.get("url") if enc is not None else ""
        if not audio:
            continue
        iimg = it.find(ITUNES + "image")
        out["items"].append({
            "guid": (it.findtext("guid") or audio).strip(), "title": _strip(it.findtext("title") or ""),
            "link": (it.findtext("link") or "").strip(), "audio": audio.strip(),
            "published_at": _iso(it.findtext("pubDate") or ""), "duration": _dur(it.findtext(ITUNES + "duration")),
            "description": _strip(it.findtext("description") or it.findtext(ITUNES + "summary") or "")[:3000],
            "image": (iimg.get("href") if iimg is not None else "") or out["image"]})
    out["items"].sort(key=lambda i: i["published_at"] or "", reverse=True)
    return out


def _gj(url):
    import json
    req = urllib.request.Request(url, headers={"User-Agent": "pawed/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def itunes_find(term):
    """Best matching show feed URL for a name (Israel store first, then US), or None."""
    best = None
    for cc in ("il", "us"):
        try:
            res = _gj(f"https://itunes.apple.com/search?media=podcast&entity=podcast&limit=8&country={cc}&term=" + urllib.parse.quote(term)).get("results", [])
        except Exception:
            continue
        for r in res:
            if not r.get("feedUrl"):
                continue
            sc = max(overlap(term, r.get("collectionName", "")), overlap(r.get("collectionName", ""), term))
            if best is None or sc > best[0]:
                best = (sc, r["feedUrl"])
        if best and best[0] >= 0.99:
            break
    return best[1] if best and best[0] >= 0.6 else None


def _clean_title(t):
    t = _html.unescape(t or "")
    return re.split(r"\s+[-|–—]\s+|\s*\|\s*", t)[0].strip()


def resolve_feed(ref, name=None):
    ref = (ref or "").strip()
    name = (name or "").strip()
    feed_url, page_title, text = None, "", None
    if ref.startswith("http"):
        try:
            text = fetch(ref)
        except Exception:
            text = None
        if text and looks_like_feed(text):
            feed_url = ref
        elif text:
            m = (re.search(r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]*href=["\']([^"\']+)', text, re.I)
                 or re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/(?:rss|atom)\+xml', text, re.I))
            if m:
                feed_url = urllib.parse.urljoin(ref, _html.unescape(m.group(1)))
            t = (re.search(r'property=["\']og:title["\'][^>]*content=["\']([^"\']+)', text, re.I)
                 or re.search(r"<title[^>]*>([^<]+)", text, re.I))
            page_title = _clean_title(t.group(1)) if t else ""
    if not feed_url:
        terms = [name, page_title] if ref.startswith("http") else [name, ref]       # a bare word typed instead of a URL is a show name
        for term in dict.fromkeys(x for x in terms if x):
            feed_url = itunes_find(term)
            if feed_url:
                break
    if not feed_url:
        raise ValueError("no podcast feed found for this link. Type the show's name in the name field (for example the Hebrew title) and try again")
    feed = parse_feed(fetch(feed_url))
    if not feed["items"]:
        raise ValueError("the podcast feed has no episodes")
    return {"id": feed_id(feed_url), "feed_url": feed_url, "name": name or feed["title"] or page_title or feed_url,
            "image": feed["image"], "language": "he" if feed["language"] in ("he", "iw") else ("en" if feed["language"] == "en" else "other")}
