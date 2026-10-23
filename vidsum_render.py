"""News-article renderer for vidsum articles (pure function, no server deps).

article dict:
  title, standfirst, topic, channel, vid, url, published (YYYY-MM-DD), duration (sec),
  key_points [str], blocks [{"type": "h2"|"p"|"quote"|"list", "text", "ts", "speaker", "items"}]
"""
import os
import re
import html as _html
import urllib.parse

THEMES = {  # very mild page tint per portal category: bg, hairline, quote box, quote accent
    "כלכלה": ("#fdf8e1", "#eadfb0", "#f6e9b0", "#8a4a06"),      # yellow
    "פוליטיקה": ("#f2f8ee", "#d0e4c7", "#dcedd2", "#2f5d1f"),   # green
    "טכנולוגיה": ("#fdf1ef", "#f1cfca", "#f8dad6", "#a3231a"),  # red
    "ספורט": ("#fff4e9", "#f2d9bd", "#fde2c8", "#9a4a08"),      # orange
    "תרבות": ("#f7f1fb", "#e0d2ee", "#e8dbf4", "#5d2f87"),      # purple
    "לייפסטייל": ("#fdf0f6", "#f1cfdf", "#f9d9e7", "#9b2a5c"),     # pink
    "בריאות": ("#edf8f6", "#c9e6e0", "#d3efe9", "#17665a"),     # teal
}

SITE = os.environ.get("PAWED_SITE", "https://pawed.io")      # public address (share links, canonical, og:url)

TOPICS = ["פוליטיקה", "טכנולוגיה", "כלכלה", "ספורט", "תרבות", "לייפסטייל", "בריאות"]
HE_MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]

CSS = """
:root{--bg:#fdf8e1;--line:#eadfb0;--quote:#f6e9b0;--acc:#8a4a06;--red:#e3222b;--red-dark:#b9141c;--ink:#171717;--muted:#6c6c6c;--line:#e5e5e5;--soft:#f4f4f4;--yellow:#ffc400}
*{box-sizing:border-box}
body{margin:0;color:var(--ink);background:var(--bg);font-family:Arial,"Noto Sans Hebrew",sans-serif;direction:rtl}
a{color:inherit;text-decoration:none}
.topline{height:5px;background:var(--red)}
.utility{border-bottom:1px solid var(--line);color:#777;font-size:12px}
.utility-inner,.masthead,.nav,.page,.footer-inner{max-width:1180px;margin:auto;padding-inline:22px}
.utility-inner{min-height:34px;display:flex;align-items:center;justify-content:space-between;gap:18px}
.utility-links{display:flex;gap:18px}.live{color:var(--red);font-weight:700}
.masthead{height:96px;display:flex;align-items:center;justify-content:center}
.brand{display:flex;align-items:center;gap:12px}
.brand-logo{height:58px;width:auto;display:block}
.brand-mark{color:#2a211b;font-weight:900;font-size:46px;letter-spacing:-1.5px;line-height:1;font-family:"Arial Black",Arial,sans-serif}
.brand-note{color:#777;font-size:13px;border-right:1px solid #ccc;padding-right:12px}
.nav-wrap{border-block:1px solid var(--line)}
.nav{display:flex;min-height:48px;align-items:center;justify-content:center;overflow:auto;scrollbar-width:none}
.nav::-webkit-scrollbar{display:none}
.nav a{padding:15px 18px;font-size:15px;font-weight:700;white-space:nowrap;border-bottom:3px solid transparent}
.nav a:hover,.nav a.active{color:var(--red);border-bottom-color:var(--red)}
.page{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:42px;padding-top:22px;padding-bottom:70px}
.crumbs{font-size:13px;color:#888;margin-bottom:14px}.crumbs a:hover{color:var(--red)}
h1{font-size:40px;line-height:1.12;margin:0 0 14px;letter-spacing:-1px;font-weight:900}
.standfirst{font-size:20px;line-height:1.5;color:#666;font-style:italic;margin:0 0 16px}
.byline{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;font-size:13px;color:#777;padding:12px 0;border-block:1px solid var(--line);margin-bottom:22px}
.byline b{color:var(--ink)}
.share{margin-inline-start:auto;display:flex;gap:8px}
.share a{border:1px solid #d8d8d8;border-radius:50%;width:30px;height:30px;display:grid;place-items:center;font-size:12px;font-weight:700;color:#555}
.share a:hover{border-color:var(--red);color:var(--red)}
figure{margin:0 0 24px}
figure img{width:100%;display:block;aspect-ratio:16/9;object-fit:cover;background:#222}
.imgw{position:relative;overflow:hidden;aspect-ratio:16/9;background:#222}.imgw::before{content:"";position:absolute;inset:-34px;background:var(--img) center/cover no-repeat;filter:blur(26px) brightness(.82) saturate(1.1)}.imgw img{position:relative;display:block;width:100%!important;height:100%!important;aspect-ratio:auto!important;object-fit:contain!important;background:none!important}
figcaption{font-size:12px;color:#888;padding-top:8px;font-style:italic}
.keybox{background:rgba(255,255,255,.6);border-right:4px solid var(--red);padding:16px 20px;margin:0 0 26px}
.keybox h4{margin:0 0 8px;font-size:14px;color:var(--red)}
.keybox ul{margin:0;padding-inline-start:20px}.keybox li{margin:4px 0;line-height:1.5;font-size:15px}
.body{font-size:19px;line-height:1.75}
.body p{margin:0 0 20px}
.body h2{font-size:26px;line-height:1.2;margin:34px 0 12px;font-weight:800}
.body ul.l{margin:0 0 20px;padding-inline-start:22px}.body ul.l li{margin:8px 0}
.ts{display:inline-block;margin-inline-start:6px;padding:1px 8px;background:#e3edff;color:#1556d6;border:1px solid #b9cffb;border-radius:20px;font-size:11px;font-weight:700;vertical-align:middle;direction:ltr;white-space:nowrap;text-decoration:underline;text-underline-offset:2px}
.ts:hover{background:#1556d6;color:#fff;border-color:#1556d6}
.pull{float:right;clear:right;width:42%;margin:6px 0 14px 24px;padding:12px 16px;background:var(--quote);border:0;border-right:5px solid var(--acc)}
.pull.alt{float:left;clear:left;margin:6px 24px 14px 0;border-right:0;border-left:5px solid var(--acc)}
.pull q{display:block;quotes:none;font-family:Georgia,"Frank Ruhl Libre","David Libre","Times New Roman",serif;font-style:italic;font-size:21px;line-height:1.35;font-weight:700;color:var(--acc)}
.pull cite{display:block;margin-top:8px;font-size:12px;color:var(--acc);opacity:.8;font-style:italic;font-family:Georgia,serif;line-height:1.4}
.body::after{content:"";display:block;clear:both}
.hero{position:relative;display:block}
.hero::after{content:"▶";position:absolute;inset:auto auto 14px 14px;width:44px;height:44px;border-radius:50%;background:rgba(0,0,0,.65);color:#fff;display:grid;place-items:center;font-size:16px;padding-inline-start:3px}
.hero:hover::after{background:var(--red)}
.watch{display:inline-block;margin:6px 0 30px;padding:11px 20px;background:var(--red);color:#fff;font-weight:700;font-size:15px}
.watch:hover{background:var(--red-dark)}
.disclaimer{font-size:13px;color:#888;border-top:1px solid var(--line);padding-top:14px;margin-top:10px}
.related{margin-top:34px;border-top:3px solid var(--ink);padding-top:14px}
.related h3{margin:0 0 14px;font-size:22px}
.rel-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.rel-card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:#222}
.rel-card .t{font-size:12px;font-weight:700;color:var(--red);margin-top:8px}
.rel-card h4{margin:4px 0 0;font-size:16px;line-height:1.25}.rel-card:hover h4{text-decoration:underline}
aside .box{background:rgba(255,255,255,.6);border:1px solid var(--line);border-top:3px solid var(--ink);padding:14px 16px;margin-bottom:22px}
aside h3{margin:0 0 10px;font-size:14px;letter-spacing:.3px;font-weight:900}
aside ol{margin:0;padding:0;list-style:none;counter-reset:n}
aside li{counter-increment:n;display:grid;grid-template-columns:22px 1fr;gap:6px;padding:10px 0;border-top:1px solid var(--line);font-size:15px;line-height:1.3;font-weight:700}
aside li:first-child{border-top:0;padding-top:0}
aside li::before{content:counter(n);color:var(--red);font-weight:900}
aside li small{display:block;color:#888;font-weight:400;font-size:12px;margin-top:3px}
aside li:hover span{text-decoration:underline}
footer{background:#222;color:#aaa;padding:26px 0;font-size:12px}
.footer-inner{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}
@media(max-width:900px){.page{grid-template-columns:1fr}.rel-grid{grid-template-columns:1fr}h1{font-size:31px}}
@media(max-width:640px){.pull,.pull.alt{float:none;width:auto;margin:20px 0}}
@media(max-width:520px){.page,.utility-inner,.masthead,.nav,.footer-inner{padding-inline:14px}.brand-note{display:none}.body{font-size:18px}.pull q{font-size:22px}}
@media(max-width:640px){
body{-webkit-text-size-adjust:100%}
.utility-inner{padding-inline:12px;min-height:34px;justify-content:flex-start}
.utility-inner>span{display:none}
.utility-links{display:flex;gap:14px;overflow-x:auto;white-space:nowrap;scrollbar-width:none;font-size:13px}
.utility-links::-webkit-scrollbar{display:none}
.masthead{height:auto;min-height:64px;padding-inline:12px;justify-content:center}
.brand{gap:8px}.brand-logo{height:38px}.brand-mark{font-size:30px;letter-spacing:-1px}.brand-note{display:none}
.nav-wrap{position:sticky;top:0;z-index:60;background:var(--bg);box-shadow:0 1px 0 var(--line)}
.nav{justify-content:flex-start;padding:7px 12px;min-height:0;gap:8px;-webkit-overflow-scrolling:touch}
.nav a{flex:0 0 auto;border:1px solid var(--line);border-radius:999px;padding:8px 15px;font-size:14px;background:rgba(255,255,255,.6)}
.nav a.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.page{padding:12px 14px 50px;gap:26px}
h1{font-size:26px;line-height:1.14;letter-spacing:-.5px}
.standfirst{font-size:17px;line-height:1.45}
.byline{gap:4px 12px;font-size:12px;padding:10px 0}
.share{margin-inline-start:0;width:100%;order:9}
figure{margin-inline:-14px}figure img{aspect-ratio:16/9}figcaption{padding-inline:14px}
.keybox{padding:12px 14px;margin-bottom:20px}.keybox li{font-size:14.5px}
.body{font-size:18px;line-height:1.7}.body p{margin-bottom:17px}.body h2{font-size:22px;margin:26px 0 10px}
.pull{padding:12px 14px}.pull q{font-size:20px}
.watch{display:block;text-align:center;padding:13px}
.rel-grid{display:flex;overflow-x:auto;gap:12px;scroll-snap-type:x mandatory;margin-inline:-14px;padding-inline:14px;scrollbar-width:none}
.rel-grid::-webkit-scrollbar{display:none}
.rel-card{flex:0 0 74%;scroll-snap-align:start}
aside{margin-top:6px}
footer .footer-inner{flex-direction:column;gap:6px;padding-inline:14px;font-size:11px}
}
"""


CSS += ".brand-txt{display:flex;flex-direction:column;align-items:flex-start;line-height:1}.brand-note{display:block!important;border:0!important;padding:0!important;font-style:italic;font-size:15px;color:#6c6c6c;margin-top:-2px;direction:ltr}@media(max-width:640px){.brand-note{font-size:11px}}"
CSS += ".brand-wordmark{height:88px;width:auto;display:block}@media(max-width:640px){.brand-wordmark{height:56px}}.auth-only,.admin-only{display:none}body.authed .auth-only,body.admin .admin-only{display:inline}.listen{display:flex;align-items:center;gap:10px;margin:-6px 0 20px;font-size:13px;color:var(--muted)}.listen-ic{display:inline-flex;transition:transform .12s}.listen-ic:hover{transform:scale(1.12)}"

PAW_JS = """<script>(function(){var seq=['maxresdefault','hq720','mqdefault'];
function fix(img){var v=img.dataset.vid,i=0,own=img.dataset.img;var p=img.parentNode;if(!p.classList||!p.classList.contains('imgw')){var w=document.createElement('div');w.className='imgw';p.insertBefore(w,img);w.appendChild(img);}
function next(){if(own){var o=own;own=null;img.src=o;return;}if(i<seq.length){img.src='https://i.ytimg.com/vi/'+v+'/'+seq[i++]+'.jpg';}
else{img.onload=img.onerror=null;img.src='/vidsum/cover/'+v+'.svg'+(document.documentElement.lang==='en'?'?lang=en':'');}}
img.onerror=next;
img.onload=function(){if(img.naturalWidth<300&&img.src.indexOf('/vidsum/cover/')<0){next();return;}img.parentNode.style.setProperty('--img','url("'+img.src+'")');};
next();}
document.querySelectorAll('img[data-vid]').forEach(fix);})();</script>"""
PAW_JS += "<script>fetch('/api/vidsum/me').then(function(r){return r.json()}).then(function(j){if(j.signed)document.body.classList.add('authed');if(j.admin)document.body.classList.add('admin')}).catch(function(){});</script>"


def _ts_sec(ts):
    try:
        p = [int(x) for x in str(ts).split(":")]
        return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]
    except Exception:
        return None


def _he_date(iso):
    try:
        y, m, d = (int(x) for x in iso[:10].split("-"))
        return f"{d} ב{HE_MONTHS[m - 1]} {y}"
    except Exception:
        return ""


def _theme(topic):
    bg, line, quote, acc = THEMES.get(topic, THEMES["כלכלה"])
    return f"--bg:{bg};--line:{line};--quote:{quote};--acc:{acc}"


_DASH = re.compile(r"\s*(?:--+|[\u2012\u2013\u2014\u2015])\s*")
_KEEP = {"url", "vid", "slug", "source_id", "published", "published_at", "created", "ts", "topic"}


def nodash(s):
    """Double / long dashes (-- — –) always become a single spaced hyphen."""
    return _DASH.sub(" - ", s) if isinstance(s, str) else s


def clean_dashes(o, key=None):
    if isinstance(o, str):
        return o if key in _KEEP else nodash(o)
    if isinstance(o, list):
        return [clean_dashes(x, key) for x in o]
    if isinstance(o, dict):
        return {k: clean_dashes(v, k) for k, v in o.items()}
    return o


EN_TOPICS = {"פוליטיקה": "Politics", "טכנולוגיה": "Technology", "כלכלה": "Economy", "ספורט": "Sports", "תרבות": "Culture",
             "לייפסטייל": "Lifestyle", "בריאות": "Health"}
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
STR = {
    "he": {"main": "ראשי", "live": "● מתעדכן אוטומטית", "all": "כל הסיכומים", "sources": "מקורות", "log": "יומן", "by": "מאת", "desk": "מערכת Pawed",
           "from": "מתוך", "read": "דק׳ קריאה", "ls_pod": "האזנה לפרק", "ls_yt": "צפייה בסרטון ביוטיוב", "shot": " · צילום מסך מתוך הסרטון",
           "also": "האזנה גם ב:", "on": "האזנה ב-", "key": "עיקרי הדברים", "full_pod": "האזנה לפרק המלא ↗", "full_yt": "צפייה בשיחה המלאה ביוטיוב ↗",
           "more": "כתבות נוספות", "new": "הכי חדש", "bytopic": "לפי נושא", "stories": "כתבות",
           "foot": "Pawed · פורטל חדשות המבוסס על סיכומי וידאו", "wait": ""},
    "en": {"main": "Home", "live": "● Updating automatically", "all": "All summaries", "sources": "Resources", "log": "Log", "by": "By", "desk": "Pawed Desk",
           "from": "From", "read": "min read", "ls_pod": "Listen to the episode", "ls_yt": "Watch the video on YouTube", "shot": " · Screenshot from the video",
           "also": "Also listen on:", "on": "Listen on ", "key": "Key points", "full_pod": "Listen to the full episode ↗", "full_yt": "Watch the full conversation on YouTube ↗",
           "more": "More stories", "new": "Latest", "bytopic": "By topic", "stories": "stories",
           "foot": "Pawed · a news portal built on video and podcast summaries",
           "wait": "The English version of this story is being prepared. It will appear here automatically in a few minutes."},
}
EN_DISCLAIMER = "The views expressed are those of the interviewees and have not been verified. This article was compiled automatically from a transcript of the conversation."

LTR_CSS = ("body{direction:ltr}.brand-note{border-right:0;border-left:1px solid #ccc;padding-right:0;padding-left:12px}"
           ".keybox{border-right:0;border-left:4px solid var(--red)}"
           ".pull{float:left;clear:left;margin:6px 24px 14px 0;border-right:0;border-left:5px solid var(--acc)}"
           ".pull.alt{float:right;clear:right;margin:6px 0 14px 24px;border-left:0;border-right:5px solid var(--acc)}"
           "@media(max-width:640px){.pull,.pull.alt{float:none;width:auto;margin:20px 0}}")
LANG_CSS = (".utility-inner{justify-content:flex-start}.utility-links{margin-inline-start:auto}.langsw{display:inline-flex;gap:6px;order:-1;margin-inline-start:6px}"
            "html[dir=ltr] .langsw{order:99}.langsw a{font-size:18px;line-height:1;opacity:.45;cursor:pointer;text-decoration:none;"
            "filter:grayscale(.4)}.langsw a.on{opacity:1;filter:none}.langsw a:hover{opacity:1}"
            ".he h1,.he .standfirst,.he .body,.he .keybox{direction:rtl;text-align:right}.wait{background:#fff6d6;border:1px solid #ecd57a;padding:10px 14px;margin:0 0 16px;font-size:14px;direction:ltr;text-align:left}")
LANG_JS = ("<script>document.querySelectorAll('.langsw a').forEach(function(a){a.onclick=function(e){e.preventDefault();var l=a.dataset.l;"
           "document.cookie='pawed_lang='+l+';path=/;max-age=31536000;samesite=lax';"
           "try{fetch('/api/vidsum/lang',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lang:l})}).finally(function(){location.reload()});}"
           "catch(x){location.reload()}};});</script>")


def _en_date(iso):
    try:
        y, m, d = (int(x) for x in iso[:10].split("-"))
        return f"{EN_MONTHS[m - 1]} {d}, {y}"
    except Exception:
        return ""


def _overlay_en(a):
    """the article with its English text in place of the Hebrew one (ts, links, images stay). -> (article, translated?)"""
    en = a.get("en")
    if not en:
        return a, False
    b = dict(a)
    for k in ("title", "standfirst", "lead", "key_points"):
        if en.get(k):
            b[k] = en[k]
    blocks = []
    for x, y in zip(a.get("blocks") or [], en.get("blocks") or []):
        z = dict(x)
        z["text"] = y.get("text", x.get("text", ""))
        if x.get("speaker") is not None:
            z["speaker"] = y.get("speaker") or x.get("speaker", "")
        if x.get("items"):
            z["items"] = y.get("items") or x["items"]
        blocks.append(z)
    b["blocks"] = blocks or a.get("blocks")
    return b, True


def render(a, latest=(), base="", disclaimer="", lang="he"):
    """a: article dict. latest: [{slug,title,topic,vid,channel}] newest first. base: URL prefix ('' on the server)."""
    en = lang == "en"
    S = STR["en" if en else "he"]
    translated = True
    if en:
        a, translated = _overlay_en(a)
        latest = [dict(x, title=x.get("title_en") or x["title"]) for x in latest]
        disclaimer = EN_DISCLAIMER if disclaimer else ""
    tname = (lambda t: EN_TOPICS.get(t, t)) if en else (lambda t: t)
    fdate = _en_date if en else _he_date
    a = clean_dashes(a)
    latest = clean_dashes(list(latest))
    e = _html.escape
    rss = a.get("kind") == "rss"            # a podcast episode: no YouTube deep links, the time is shown as plain text
    ts_link = lambda ts: ("" if not _ts_sec(ts) else (f'<span class="ts">{e(ts)}</span>' if rss else
                          f'<a class="ts" href="{e(a["url"])}&amp;t={_ts_sec(ts)}s" target="_blank" rel="noopener">▶ {e(ts)}</a>')
                          if _ts_sec(ts) is not None and ts else "")
    art_url = lambda s: f'{base}/vidsum/article/{urllib.parse.quote(s["slug"])}'
    thumb = lambda v: f"https://i.ytimg.com/vi/{v}/hq720.jpg"   # true 16:9 (hqdefault has baked-in black bars)
    mins = max(1, round(sum(len(b.get("text", "").split()) for b in a["blocks"]) / 200))
    others = [x for x in latest if x.get("slug") != a.get("slug")]

    tps = [t for t in (a.get("topics") or []) if t in TOPICS] or [a["topic"]]
    if a["topic"] in tps:
        tps = [a["topic"]] + [t for t in tps if t != a["topic"]]
    crumb_topics = '<a href="%s/vidsum#%s">%s</a>' % (base, urllib.parse.quote(tps[0]), e(tname(tps[0])))   # one highlighted section; the others only list the story
    nav = "".join(f'<a href="{base}/vidsum#{urllib.parse.quote(t)}" class="{"active" if t == tps[0] else ""}">{e(tname(t))}</a>'
                  for t in TOPICS)
    share_url = urllib.parse.quote(f'{SITE}/vidsum/article/{a["slug"]}', safe="")
    share_txt = urllib.parse.quote(a["title"], safe="")
    out = [f'<div class="topline"></div><div class="utility"><div class="utility-inner">'
           f'<span>{e(fdate(a.get("published_at") or a.get("published") or ""))}</span><div class="utility-links"><span class="live">{S["live"]}</span>'
           f'<a class="admin-only" href="{base}/vidsum/articles">{S["all"]}</a><a class="auth-only" href="{base}/vidsum/sources">{S["sources"]}</a><a class="admin-only" href="{base}/vidsum/logs">{S["log"]}</a></div>'
           f'<span class="langsw"><a data-l="en" class="{"on" if en else ""}" title="English">🇺🇸</a><a data-l="he" class="{"" if en else "on"}" title="עברית">🇮🇱</a></span></div></div>'
           f'<header class="masthead"><a class="brand" href="{base}/"><img class="brand-wordmark" src="{base}/vidsum/pawed-wordmark.png" alt="Pawed - Respect Your Pods"></a></header>'
           f'<div class="nav-wrap"><nav class="nav"><a href="{base}/vidsum">{S["main"]}</a>{nav}</nav></div>',
           '<div class="page"><article class="he">' if en and not translated else '<div class="page"><article>',
           f'<div class="crumbs"><a href="{base}/vidsum">{S["main"]}</a> › {crumb_topics}</div>',
           (f'<div class="wait">{S["wait"]}</div>' if en and not translated else ""),
           f'<h1>{e(a["title"])}</h1><p class="standfirst">{e(a["standfirst"])}</p>',
           f'<div class="byline"><span>{S["by"]} <b>{S["desk"]}</b></span><span>{S["from"]} {e(a.get("channel", "").strip())}</span>'
           f'<span>{e(fdate(a.get("published_at") or a.get("published") or ""))}</span><span>{mins} {S["read"]}</span>'
           f'<span class="share"><a href="https://wa.me/?text={share_txt}%20{share_url}" target="_blank" rel="noopener" title="WhatsApp">W</a>'
           f'<a href="https://www.facebook.com/sharer/sharer.php?u={share_url}" target="_blank" rel="noopener" title="Facebook">f</a>'
           f'<a href="https://twitter.com/intent/tweet?url={share_url}&amp;text={share_txt}" target="_blank" rel="noopener" title="X">X</a></span></div>',
           f'<figure><a class="hero" href="{e(a["url"])}" target="_blank" rel="noopener" title="{S["ls_pod"] if rss else S["ls_yt"]}"><img data-vid="{e(a["vid"])}" data-img="{e(a.get("image") or "")}" alt=""></a>'
           f'<figcaption>{e(a.get("caption") or a.get("channel", "").strip())}{"" if rss else S["shot"]}</figcaption></figure>']
    lk = a.get("links") or {}
    icons = ""
    if lk.get("spotify"):
        icons += (f'<a class="listen-ic" href="{e(lk["spotify"])}" target="_blank" rel="noopener" title="{S["on"]}Spotify" aria-label="Spotify">'
                  '<svg viewBox="0 0 24 24" width="30" height="30"><circle cx="12" cy="12" r="12" fill="#1ED760"/>'
                  '<path d="M5.4 9.2c4.2-1.2 9.2-.8 13 1.4M6.2 12.6c3.5-1 7.6-.7 10.7 1.1M7 15.8c2.8-.8 5.9-.5 8.4.9" fill="none" stroke="#000" stroke-width="1.7" stroke-linecap="round"/></svg></a>')
    if lk.get("apple"):
        icons += (f'<a class="listen-ic" href="{e(lk["apple"])}" target="_blank" rel="noopener" title="{S["on"]}Apple Podcasts" aria-label="Apple Podcasts">'
                  '<svg viewBox="0 0 24 24" width="30" height="30"><defs><linearGradient id="apg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F452FF"/><stop offset="1" stop-color="#832BC1"/></linearGradient></defs>'
                  '<rect width="24" height="24" rx="5.5" fill="url(#apg)"/><circle cx="12" cy="10" r="2" fill="#fff"/>'
                  '<path d="M12 13.2c-1 0-1.6.7-1.5 1.6l.4 3.4c.1.8.5 1.3 1.1 1.3s1-.5 1.1-1.3l.4-3.4c.1-.9-.5-1.6-1.5-1.6z" fill="#fff"/>'
                  '<path d="M7.6 12.2a4.7 4.7 0 117.5-.4M5.9 12.6a6.5 6.5 0 1112.2-.2" fill="none" stroke="#fff" stroke-width="1.4" stroke-linecap="round"/></svg></a>')
    if icons:
        out.append(f'<div class="listen"><span>{S["also"]}</span>{icons}</div>')
    if a.get("key_points"):
        out.append(f'<div class="keybox"><h4>{S["key"]}</h4><ul>' + "".join(f"<li>{e(k)}</li>" for k in a["key_points"]) + "</ul></div>")
    out.append('<div class="body">')
    qn = 0
    for b in a["blocks"]:
        t = b["type"]
        if t == "h2":
            out.append(f'<h2>{e(b["text"])}</h2>')
        elif t == "p":
            out.append(f'<p>{e(b["text"])}{ts_link(b.get("ts"))}</p>')
        elif t == "quote":
            out.append(f'<blockquote class="pull{" alt" if qn % 2 else ""}" style="margin-block:6px 14px"><q>{e(b["text"])}</q>'
                       f'<cite>{e(b.get("speaker", ""))}{ts_link(b.get("ts"))}</cite></blockquote>')
            qn += 1
        elif t == "list":
            out.append('<ul class="l">' + "".join(f"<li>{e(i)}</li>" for i in b["items"]) + "</ul>")
    out.append("</div>")
    out.append(f'<a class="watch" href="{e(a["url"])}" target="_blank" rel="noopener">{S["full_pod"] if rss else S["full_yt"]}</a>')
    if disclaimer:
        out.append(f'<p class="disclaimer">{e(disclaimer)}</p>')
    rel = [x for x in others if set(x.get("topics") or [x["topic"]]) & set(tps)][:3] or others[:3]
    if rel:
        out.append(f'<section class="related"><h3>{S["more"]}</h3><div class="rel-grid">' + "".join(
            f'<a class="rel-card" href="{art_url(x)}"><img data-vid="{e(x["vid"])}" data-img="{e(x.get("image") or "")}" alt=""><div class="t">{e(tname(x["topic"]))}</div>'
            f'<h4>{e(x["title"])}</h4></a>' for x in rel) + "</div></section>")
    out.append("</article><aside>")
    if others:
        out.append(f'<div class="box"><h3>{S["new"]}</h3><ol>' + "".join(
            f'<li><a href="{art_url(x)}"><span>{e(x["title"])}</span><small>{e(tname(x["topic"]))}</small></a></li>' for x in others[:5]) + "</ol></div>")
    cnt = {}
    for x in latest:
        cnt[x["topic"]] = cnt.get(x["topic"], 0) + 1
    out.append(f'<div class="box"><h3>{S["bytopic"]}</h3><ol>' + "".join(
        f'<li><a href="{base}/vidsum#{urllib.parse.quote(t)}"><span>{e(tname(t))}</span><small>{cnt.get(t, 0)} {"story" if en and cnt.get(t, 0) == 1 else S["stories"]}</small></a></li>'
        for t in TOPICS) + "</ol></div></aside></div>")
    out.append(f'<footer><div class="footer-inner"><span>{S["foot"]}</span>'
               '<span>Summarized by Pawed (by Mr. Brosh)</span></div></footer>')
    desc = e(a["standfirst"])
    refresh = '<meta http-equiv="refresh" content="60">' if en and not translated else ""
    return (f'<!doctype html><html lang="{lang}" dir="{"ltr" if en else "rtl"}"><head><meta charset="utf-8">'
            f'<meta name="theme-color" content="#e3222b"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(a["title"])} | Pawed</title>'
            f'<meta name="description" content="{desc}"><link rel="canonical" href="{SITE}/vidsum/article/{urllib.parse.quote(a["slug"])}">'
            f'<meta property="og:url" content="{SITE}/vidsum/article/{urllib.parse.quote(a["slug"])}"><meta property="og:title" content="{e(a["title"])}">'
            f'<meta property="og:description" content="{desc}"><meta property="og:image" content="{e(a.get("image")) if rss and a.get("image") else "https://i.ytimg.com/vi/" + e(a["vid"]) + "/maxresdefault.jpg"}">'
            f'<style>{CSS}{LANG_CSS}{LTR_CSS if en else ""}</style>{refresh}</head><body style="{_theme(a["topic"])}">{"".join(out)}{PAW_JS}{LANG_JS}</body></html>')
