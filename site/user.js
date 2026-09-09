/* Cookin multi-user client layer (shared by index.html + en.html).
   Loaded after data*.js / videos.js / gf.js and BEFORE the page's main script.
   Exposes VIS(all) — the recipe list the page should render (base minus the
   user's hidden set, plus own + included dishes) — and renders the header
   user bar, the add-dish modal and the sources/settings drawer. */
(function(){
const LANG = document.documentElement.lang === "en" ? "en" : "he";
const S = LANG === "he" ? {
  signin:"התחברות", signout:"התנתקות", add:"➕ מנה חדשה", settings:"⚙️ המנות והמקורות שלי",
  addTitle:"הוספת מנה מסרטון", addHint:"הדביקו קישור לריל מפייסבוק / אינסטגרם / טיקטוק / יוטיוב. הסרטון יורד, ג'מיני יכתוב את המתכון בעברית ובאנגלית, ותוכלו לערוך. המנה נשמרת פרטית — אתם מחליטים אם לפרסם.",
  addBtn:"הוספה", adding:"שולח…", usage:(a,b)=>`נותרו היום ${Math.max(0,b-a)} מתוך ${b}`,
  processing:"בהכנה… ⏳", failed:"העיבוד נכשל ✗", queued:"ממתין לטיפול של אידו ⏳",
  myDishes:"המנות שלי", noMine:"עדיין לא הוספתם מנות.", allPublic:"🌍 כולן ציבוריות", allPrivate:"🔒 כולן פרטיות",
  pub:"🌍 ציבורי", priv:"🔒 פרטי", makePub:"פרסום", makePriv:"הסתרה", del:"מחיקה", retry:"נסו שוב", toQueue:"שלחו לאידו",
  confirmDel:"למחוק את המנה לצמיתות?",
  base:"מנות הבסיס (Cookin)", showBase:"הצג את מנות הבסיס", hiddenN:n=>`מנות מוסתרות: ${n}`, restore:"החזר", restoreAll:"החזר הכל",
  hideDish:"הסתר מנה זו", others:"מנות של משתמשים אחרים", noOthers:"עדיין אין מנות ציבוריות של משתמשים אחרים.",
  include:"כלול", dishes:n=>`${n} מנות`, close:"✕", limit:"הגעתם למכסה היומית.", err:"שגיאה", mine:"שלי",
  adminQ:n=>`בתור לטיפול ידני: ${n}`, notConfigured:"ההתחברות עוד לא מוגדרת",
  urlsPh:"קישור אחד בכל שורה — פייסבוק / אינסטגרם / טיקטוק / יוטיוב",
  importFile:"📂 ייבוא מקובץ ייצוא (פייסבוק / אינסטגרם)", found:n=>`נמצאו ${n} קישורים בקובץ`, noneFound:"לא נמצאו קישורים בקובץ",
  howTo:"איך מייצאים מנות שמורות מפייסבוק ואינסטגרם?",
  howToHtml:`<p><b>דרך מהירה (כמה מנות):</b> פותחים את הסרטון השמור ← ⋯ / שיתוף ← <b>העתקת קישור</b> ← מדביקים כאן, שורה לכל קישור.</p>
<p><b>ייצוא מלא של כל השמורים (פייסבוק):</b> פייסבוק ← הגדרות ופרטיות ← הגדרות ← <b>מרכז החשבונות</b> ← המידע וההרשאות שלך ← <b>הורדת המידע שלך</b> ← "הורדה או העברה של מידע" ← בוחרים את פרופיל הפייסבוק ← "מידע מסוים" ← מסמנים <b>פריטים שמורים ואוספים</b> (Saved items and collections) ← פורמט <b>JSON</b>, טווח "כל הזמן" ← יוצרים קבצים. אחרי כמה דקות מגיע מייל עם ZIP; מחלצים ומעלים כאן את הקובץ <code>saved_items_and_collections.json</code> (או את כל ה-ZIP המחולץ, קובץ אחר קובץ) בכפתור "ייבוא מקובץ".</p>
<p><b>אינסטגרם:</b> אותו מסלול במרכז החשבונות ← בוחרים את חשבון האינסטגרם ← "מידע מסוים" ← <b>שמורים</b> (Saved) ← JSON. הקובץ הוא <code>saved/saved_posts.json</code>. שימו לב: אינסטגרם חוסמת לפעמים הורדת סרטונים ללא התחברות — מנות כאלה ייכנסו לתור של אידו במקום להיכשל.</p>
<p>הקובץ נקרא רק בדפדפן שלכם: שולפים ממנו את הקישורים ומדביקים אותם בתיבה למעלה. המכסה היומית (5) נשמרת — השאר פשוט לא ייכנסו, אפשר להדביק שוב מחר.</p>`,
  bulkResult:(a,l,d)=>`נוספו ${a} מנות` + (l?` · ${l} לא נוספו (מכסה יומית)`:"") + (d?` · ${d} כבר קיימות`:""),
} : {
  signin:"Sign in", signout:"Sign out", add:"➕ New dish", settings:"⚙️ My dishes & sources",
  addTitle:"Add a dish from a video", addHint:"Paste a Facebook / Instagram / TikTok / YouTube reel link. The video is downloaded, Gemini writes the recipe in Hebrew and English, and you can edit it. The dish is saved private — you decide whether to publish.",
  addBtn:"Add", adding:"Sending…", usage:(a,b)=>`${Math.max(0,b-a)} of ${b} left today`,
  processing:"Preparing… ⏳", failed:"Processing failed ✗", queued:"Waiting for Eedo ⏳",
  myDishes:"My dishes", noMine:"You haven't added dishes yet.", allPublic:"🌍 All public", allPrivate:"🔒 All private",
  pub:"🌍 Public", priv:"🔒 Private", makePub:"Publish", makePriv:"Unpublish", del:"Delete", retry:"Retry", toQueue:"Send to Eedo",
  confirmDel:"Delete this dish permanently?",
  base:"Base dishes (Cookin)", showBase:"Show the base dishes", hiddenN:n=>`Hidden dishes: ${n}`, restore:"Restore", restoreAll:"Restore all",
  hideDish:"Hide this dish", others:"Other users' dishes", noOthers:"No public dishes from other users yet.",
  include:"Include", dishes:n=>`${n} dishes`, close:"✕", limit:"Daily limit reached.", err:"Error", mine:"mine",
  adminQ:n=>`Manual queue: ${n}`, notConfigured:"Sign-in not configured yet",
  urlsPh:"One link per line — Facebook / Instagram / TikTok / YouTube",
  importFile:"📂 Import from an export file (Facebook / Instagram)", found:n=>`Found ${n} links in the file`, noneFound:"No links found in the file",
  howTo:"How do I export my saved dishes from Facebook and Instagram?",
  howToHtml:`<p><b>Quick way (a few dishes):</b> open the saved reel → ⋯ / Share → <b>Copy link</b> → paste here, one link per line.</p>
<p><b>Full export of everything you saved (Facebook):</b> Facebook → Settings & privacy → Settings → <b>Accounts Center</b> → Your information and permissions → <b>Download your information</b> → "Download or transfer information" → pick your Facebook profile → "Some of your information" → tick <b>Saved items and collections</b> → format <b>JSON</b>, date range "All time" → Create files. A few minutes later you get an email with a ZIP; unzip it and upload <code>saved_items_and_collections.json</code> (or any file from the unzipped folder, one at a time) with the "Import from an export file" button.</p>
<p><b>Instagram:</b> same path in Accounts Center → pick the Instagram account → "Some of your information" → <b>Saved</b> → JSON. The file is <code>saved/saved_posts.json</code>. Note: Instagram sometimes blocks anonymous video downloads; those dishes go to Eedo's queue instead of failing.</p>
<p>The file is read only in your browser: the links are extracted and pasted into the box above. The daily cap (5) still applies; the rest are simply not added, paste again tomorrow.</p>`,
  bulkResult:(a,l,d)=>`Added ${a} dishes` + (l?` · ${l} not added (daily cap)`:"") + (d?` · ${d} already existed`:""),
};

const css = `
header{z-index:60 !important}
.card{position:relative}
.ubar{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.ubtn{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:7px 14px;cursor:pointer;font-family:inherit;font-size:.9rem;color:var(--ink);font-weight:600;display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.ubtn:hover{background:var(--chip)}
.ubtn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.ubtn.primary:hover{background:var(--accent-dark)}
.uav{width:34px;height:34px;border-radius:50%;cursor:pointer;border:2px solid var(--card);box-shadow:0 1px 4px rgba(80,60,40,.25)}
.umenu{position:absolute;top:46px;inset-inline-end:0;background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);padding:10px;min-width:200px;z-index:80;display:none;font-size:.9rem}
.umenu .n{font-weight:700}.umenu .e{color:var(--muted);font-size:.8rem;margin-bottom:8px;word-break:break-all}
.uwrap{position:relative}
.uhide{position:absolute;top:8px;inset-inline-start:8px;width:26px;height:26px;border-radius:50%;border:0;background:rgba(43,36,32,.55);color:#fff;cursor:pointer;font-size:.8rem;line-height:26px;text-align:center;opacity:0;transition:opacity .15s}
.card:hover .uhide{opacity:1}
@media(hover:none){.uhide{opacity:.85}}
.uhide:hover{background:#a53a2c}
.ubadge{display:inline-flex;align-items:center;gap:4px;background:var(--chip);border-radius:6px;padding:2px 8px;font-size:.75rem;color:#6b5d4f}
.ubadge img{width:16px;height:16px;border-radius:50%}
.ubadge.pub{background:#e4f3e4;color:#2f6b34}.ubadge.priv{background:#f3ece1}
.card.uproc .thumb{filter:grayscale(.6) brightness(.85)}
.uspin{position:absolute;top:0;left:0;right:0;aspect-ratio:4/3;display:flex;align-items:center;justify-content:center;color:#fff;font-size:2rem;text-shadow:0 2px 8px rgba(0,0,0,.6)}
.uspin span{animation:uspin 1.4s linear infinite;display:inline-block}
@keyframes uspin{to{transform:rotate(360deg)}}
.card.ufail .thumb{filter:grayscale(1) brightness(.7)}
#umodal{position:fixed;inset:0;background:rgba(43,36,32,.45);z-index:100;display:none;align-items:center;justify-content:center;padding:16px}
#umodal .box{background:var(--card);border-radius:18px;box-shadow:var(--shadow);width:min(680px,100%);max-height:92vh;overflow:auto;padding:22px 24px}
#umodal h3{font-size:1.2rem;margin-bottom:8px;display:flex;align-items:center;gap:10px}
#umodal h3 .x{margin-inline-start:auto;border:0;background:var(--chip);border-radius:50%;width:32px;height:32px;cursor:pointer;font-size:1rem}
#umodal .hint{color:var(--muted);font-size:.9rem;line-height:1.5;margin-bottom:14px}
#umodal input[type=url]{width:100%;border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:1rem;font-family:inherit;color:var(--ink);direction:ltr}
#umodal textarea{width:100%;min-height:110px;border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:.95rem;font-family:inherit;color:var(--ink);direction:ltr;resize:vertical;line-height:1.5}
#umodal details{margin-top:14px;border:1px solid var(--line);border-radius:12px;padding:10px 14px;background:var(--bg)}
#umodal summary{cursor:pointer;font-weight:600;color:var(--accent-dark)}
#umodal details p{font-size:.88rem;line-height:1.6;margin:8px 0;color:var(--ink)}
#umodal details code{background:var(--chip);border-radius:4px;padding:0 4px;direction:ltr;unicode-bidi:embed}
#umodal .row{display:flex;gap:10px;align-items:center;margin-top:12px;flex-wrap:wrap}
#umodal .row .u{color:var(--muted);font-size:.85rem;margin-inline-start:auto}
#umodal .msg{margin-top:10px;font-size:.9rem;color:#a53a2c;min-height:1.2em}
#umodal .sec{border-top:1px solid var(--line);padding:16px 0 6px;margin-top:10px}
#umodal .sec h4{font-size:1rem;margin-bottom:8px;color:var(--accent-dark);display:flex;align-items:center;gap:8px;flex-wrap:wrap}
#umodal .sec h4 .r{margin-inline-start:auto;display:flex;gap:6px;flex-wrap:wrap}
#umodal .mini{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:4px 10px;cursor:pointer;font-family:inherit;font-size:.8rem;color:var(--ink)}
#umodal .mini:hover{background:var(--chip)}
#umodal .mini.danger{color:#a53a2c}
#umodal .mini.on{background:#e4f3e4;border-color:#bfe0c1;color:#2f6b34}
.ulist{display:flex;flex-direction:column;gap:6px}
.uitem{display:flex;align-items:center;gap:10px;padding:6px 8px;border-radius:10px;background:var(--bg);font-size:.9rem}
.uitem img{width:44px;height:33px;object-fit:cover;border-radius:6px;background:#e9e2d6}
.uitem .t{flex:1;min-width:0}.uitem .t .n{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.uitem .t .m{color:var(--muted);font-size:.78rem}
.uitem .a{display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end}
.uitem img.av{width:32px;height:32px;border-radius:50%}
label.uchk{display:flex;align-items:center;gap:8px;cursor:pointer;font-size:.92rem}
.gbtn{display:inline-flex;align-items:center;gap:8px}
.gbtn svg{width:16px;height:16px}
`;
const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

let ME = null, hidden = new Set(), hideBase = false, sources = [];
let pollTimer = null;

window.VIS = function(all){
  return RECIPES.filter(r => {
    if(r._user) return all || r._status === "ready";
    if(!ME || !ME.user) return true;
    return !hideBase && !hidden.has(r.id);
  });
};
window.cardExtras = function(r){
  if(!ME || !ME.user) return "";
  if(!r._user) return `<button class="uhide" title="${S.hideDish}" onclick="event.stopPropagation();cookinHide('${r.id}')">✕</button>`;
  if(r._status === "processing" || r._status === "queued") return `<div class="uspin"><span>⏳</span></div>`;
  return "";
};
window.ownerBadge = function(r){
  if(!r._user) return "";
  if(r._mine) return `<span class="ubadge ${r._vis==='public'?'pub':'priv'}">${r._vis==='public'?S.pub:S.priv}</span>`;
  const o = r._owner || {};
  return `<span class="ubadge">${o.avatar?`<img src="${o.avatar}" alt="" referrerpolicy="no-referrer">`:"👤"} ${esc(o.name||"")}</span>`;
};
window.cardClass = function(r){
  if(!r._user) return "";
  if(r._status === "processing" || r._status === "queued") return " uproc";
  if(r._status === "failed") return " ufail";
  return "";
};
function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }

async function api(url, body, method){
  const r = await fetch(url, body ? {method: method||"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body)} : {});
  let j = {}; try { j = await r.json(); } catch(e){}
  if(!r.ok) throw new Error(j.message || j.error || (S.err + " " + r.status));
  return j;
}

function rerender(){
  try { renderGallery(); } catch(e){}
  try { if(document.querySelector("#pantryView").style.display === "block") renderPantry(); } catch(e){}
}

function applyDishes(){
  for(let i = RECIPES.length - 1; i >= 0; i--) if(RECIPES[i]._user) RECIPES.splice(i, 1);
  if(!ME || !ME.user) return;
  const mineIds = new Set();
  const add = (d, mine) => {
    const rec = d[LANG] || d.he || {};
    const r = Object.assign({name:"", intro:"", time:"", serves:"", creator:"", category:"", diet:"",
                             ingredientLines:[], steps:[], tips:""}, rec);
    r.id = d.id; r.image = d.id + ".jpg"; r.video = d.source_url || ""; r.needs = d.needs || [];
    r._user = true; r._mine = mine; r._status = d.status; r._vis = d.visibility; r._owner = d.owner || null;
    if(d.status !== "ready"){
      r.name = d.status === "failed" ? S.failed : (d.status === "queued" ? S.queued : S.processing);
      r.creator = (d.source_url||"").replace(/^https?:\/\/(www\.)?/,"").slice(0,40);
    }
    if(d.has_video && typeof LOCAL_VIDEOS !== "undefined") LOCAL_VIDEOS.add(d.id);
    RECIPES.push(r);
  };
  (ME.mine||[]).forEach(d => { mineIds.add(d.id); add(d, true); });
  (ME.included||[]).forEach(d => { if(!mineIds.has(d.id)) add(d, false); });
}

async function refresh(){
  try { ME = await api("/api/me"); } catch(e){ ME = {user:null}; }
  if(ME.user){
    hidden = new Set(ME.prefs.hidden||[]); hideBase = !!ME.prefs.hideBase; sources = ME.prefs.sources||[];
  }
  applyDishes(); renderBar(); rerender();
  try { setHeaderH(); } catch(e){}
  if(document.querySelector("#umodal") && document.querySelector("#umodal").style.display === "flex" && modalMode === "settings") renderSettings();
  clearTimeout(pollTimer);
  if(ME.user && (ME.mine||[]).some(d => d.status === "processing")) pollTimer = setTimeout(refresh, 6000);
  // deep link to a user dish (en.html renders in-page via #id)
  if(LANG === "en" && location.hash && location.hash.slice(1).startsWith("u") && typeof openDish === "function"){
    const id = location.hash.slice(1); if(RECIPES.some(r => r.id === id)) openDish(id, true);
  }
}

/* ---------- header bar ---------- */
const G_SVG = `<svg viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.5 30.3 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.9 6.1C12.4 13.6 17.7 9.5 24 9.5z"/><path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4.1 7.1-10.1 7.1-17.5z"/><path fill="#FBBC05" d="M10.5 28.7A14.5 14.5 0 0 1 9.5 24c0-1.6.3-3.2.8-4.7l-7.9-6.1A24 24 0 0 0 0 24c0 3.9.9 7.5 2.6 10.8l7.9-6.1z"/><path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.5-5.8c-2.1 1.4-4.8 2.3-8.4 2.3-6.3 0-11.6-4.1-13.5-9.8l-7.9 6.1C6.5 42.6 14.6 48 24 48z"/></svg>`;
function renderBar(){
  let bar = document.querySelector("#userBar");
  if(!bar){
    bar = document.createElement("div"); bar.id = "userBar"; bar.className = "ubar";
    const hw = document.querySelector(".hwrap"); if(hw) hw.appendChild(bar); else return;
  }
  if(!ME || !ME.user){
    if(ME && ME.configured === false){ bar.innerHTML = ""; return; }
    bar.innerHTML = `<a class="ubtn gbtn" href="/auth/login?next=${encodeURIComponent(location.pathname+location.hash)}">${G_SVG} ${S.signin}</a>`;
    return;
  }
  const u = ME.user;
  bar.innerHTML = `
    <button class="ubtn primary" onclick="cookinOpen('add')">${S.add}</button>
    <button class="ubtn" onclick="cookinOpen('settings')" title="${S.settings}">⚙️</button>
    <div class="uwrap">
      <img class="uav" src="${esc(u.avatar)}" alt="${esc(u.name)}" referrerpolicy="no-referrer" onclick="document.querySelector('.umenu').style.display=document.querySelector('.umenu').style.display==='block'?'none':'block'">
      <div class="umenu"><div class="n">${esc(u.name)}</div><div class="e">${esc(u.email)}</div>
        ${u.admin && ME.queued ? `<div class="e">${S.adminQ(ME.queued)}</div>` : ""}
        <button class="ubtn" onclick="cookinLogout()">${S.signout}</button></div>
    </div>`;
}
document.addEventListener("click", e => {
  const m = document.querySelector(".umenu");
  if(m && !e.target.closest(".uwrap")) m.style.display = "none";
});
window.cookinLogout = async function(){ await api("/auth/logout", {}); location.reload(); };

/* ---------- hide base dishes ---------- */
async function savePrefs(){
  await api("/api/prefs", {hidden:[...hidden], hideBase, sources});
}
window.cookinHide = async function(id){ hidden.add(id); rerender(); await savePrefs(); };
window.cookinUnhide = async function(id){ if(id === "*") hidden.clear(); else hidden.delete(id); rerender(); await savePrefs(); renderSettings(); };

/* ---------- modal ---------- */
let modalMode = null;
function modal(){
  let m = document.querySelector("#umodal");
  if(!m){
    m = document.createElement("div"); m.id = "umodal";
    m.innerHTML = `<div class="box" id="ubox"></div>`;
    m.addEventListener("click", e => { if(e.target.id === "umodal") cookinClose(); });
    document.body.appendChild(m);
  }
  return m;
}
window.cookinClose = function(){ const m = document.querySelector("#umodal"); if(m) m.style.display = "none"; modalMode = null; };
window.cookinOpen = function(mode){
  modalMode = mode; const m = modal(); m.style.display = "flex";
  if(mode === "add") renderAdd(); else renderSettings();
};
function renderAdd(){
  const u = ME.usage || {today:0, limit:5};
  document.querySelector("#ubox").innerHTML = `
    <h3>${S.addTitle}<button class="x" onclick="cookinClose()">${S.close}</button></h3>
    <div class="hint">${S.addHint}</div>
    <textarea id="uurl" placeholder="${S.urlsPh}" autocomplete="off"></textarea>
    <div class="row">
      <button class="ubtn primary" id="uadd" onclick="cookinSubmit()">${S.addBtn}</button>
      <label class="ubtn" style="cursor:pointer">${S.importFile}<input type="file" id="ufile" accept=".json,.html,.htm,.txt,.csv" style="display:none" onchange="cookinImportFile(this)"></label>
      <span class="u" id="uusage">${S.usage(u.today,u.limit)}</span>
    </div>
    <div class="msg" id="umsg"></div>
    <details><summary>${S.howTo}</summary>${S.howToHtml}</details>`;
  setTimeout(() => document.querySelector("#uurl").focus(), 50);
}
const URL_RX = /https?:\/\/[^\s"'<>\\)\]]+/g;
function extractUrls(text){
  const out = [], seen = new Set();
  text = text.replace(/\\\//g, "/").replace(/&amp;/g, "&");
  for(const m of (text.match(URL_RX) || [])){
    let u = m.replace(/\\\//g, "/").replace(/[.,;:]+$/, "");
    if(!/facebook\.com|fb\.watch|instagram\.com|tiktok\.com|youtube\.com|youtu\.be/.test(u)) continue;
    if(/facebook\.com\/(login|help|privacy|settings|profile\.php)/.test(u)) continue;
    if(/instagram\.com\/(accounts|explore|direct)\b/.test(u) || /instagram\.com\/[^\/]+\/?$/.test(u)) continue;
    if(!seen.has(u)){ seen.add(u); out.push(u); }
  }
  return out;
}
window.cookinImportFile = function(input){
  const f = input.files && input.files[0]; if(!f) return;
  const rd = new FileReader();
  rd.onload = () => {
    let text = String(rd.result || "");
    try { text = JSON.stringify(JSON.parse(text)); } catch(e){}
    const urls = extractUrls(text);
    const ta = document.querySelector("#uurl");
    const cur = ta.value.trim();
    ta.value = (cur ? cur + "\n" : "") + urls.join("\n");
    document.querySelector("#umsg").textContent = urls.length ? S.found(urls.length) : S.noneFound;
    input.value = "";
  };
  rd.readAsText(f);
};
window.cookinSubmit = async function(){
  const urls = extractUrls(document.querySelector("#uurl").value); const msg = document.querySelector("#umsg");
  if(!urls.length){ msg.textContent = "URL?"; return; }
  const b = document.querySelector("#uadd"); b.disabled = true; b.textContent = S.adding; msg.textContent = "";
  try {
    const r = await api("/api/dishes", {urls});
    await refresh();
    if(urls.length === 1 && r.added === 1){ cookinClose(); window.scrollTo({top:0}); return; }
    msg.style.color = "var(--muted)"; msg.textContent = S.bulkResult(r.added, r.skipped_limit, r.skipped_dupe);
    document.querySelector("#uurl").value = "";
    document.querySelector("#uusage").textContent = S.usage(r.usage.today, r.usage.limit);
    b.disabled = false; b.textContent = S.addBtn;
  } catch(e){ msg.style.color = ""; msg.textContent = e.message === "limit" ? S.limit : e.message; b.disabled = false; b.textContent = S.addBtn; }
};

function renderSettings(){
  const box = document.querySelector("#ubox"); if(!box || modalMode !== "settings") return;
  const mine = ME.mine || [];
  const nameOf = d => ((d[LANG]||d.he||{}).name) || (d.status === "failed" ? S.failed : d.status === "queued" ? S.queued : S.processing);
  const mineHtml = mine.length ? mine.map(d => `
    <div class="uitem">
      <img src="/images/${d.id}.jpg" alt="" onerror="this.style.visibility='hidden'">
      <div class="t"><div class="n"><a href="/d/${d.id}${LANG==='en'?'?lang=en':''}" style="color:inherit;text-decoration:none">${esc(nameOf(d))}</a></div>
        <div class="m">${d.status === "ready" ? (d.visibility === "public" ? S.pub : S.priv) : esc(d.error||"")}</div></div>
      <div class="a">
        ${d.status === "ready" ? `<button class="mini ${d.visibility==='public'?'on':''}" onclick="cookinDish('${d.id}','setVisibility','${d.visibility==='public'?'private':'public'}')">${d.visibility==='public'?S.makePriv:S.makePub}</button>` : ""}
        ${d.status === "failed" ? `<button class="mini" onclick="cookinDish('${d.id}','retry')">${S.retry}</button><button class="mini" onclick="cookinDish('${d.id}','queue')">${S.toQueue}</button>` : ""}
        ${d.status !== "processing" ? `<button class="mini danger" onclick="if(confirm('${S.confirmDel}'))cookinDish('${d.id}','delete')">${S.del}</button>` : ""}
      </div>
    </div>`).join("") : `<div class="hint">${S.noMine}</div>`;
  const hiddenList = [...hidden].map(id => RECIPES.find(r => r.id === id)).filter(Boolean);
  const hiddenHtml = hiddenList.length ? `<div class="ulist" style="margin-top:8px">${hiddenList.map(r => `
    <div class="uitem"><img src="images/${r.image}" alt=""><div class="t"><div class="n">${esc(r.name)}</div></div>
    <div class="a"><button class="mini" onclick="cookinUnhide('${r.id}')">${S.restore}</button></div></div>`).join("")}</div>` : "";
  const others = ME.explore || [];
  const othersHtml = others.length ? others.map(o => `
    <div class="uitem"><img class="av" src="${esc(o.avatar)}" alt="" referrerpolicy="no-referrer">
      <div class="t"><div class="n">${esc(o.name)}</div><div class="m">${S.dishes(o.count)}</div></div>
      <div class="a"><label class="uchk"><input type="checkbox" ${sources.includes(o.id)?"checked":""} onchange="cookinSource('${o.id}',this.checked)"> ${S.include}</label></div></div>`).join("")
    : `<div class="hint">${S.noOthers}</div>`;
  box.innerHTML = `
    <h3>${S.settings}<button class="x" onclick="cookinClose()">${S.close}</button></h3>
    <div class="sec"><h4>${S.myDishes} (${mine.length})
      ${mine.length ? `<span class="r"><button class="mini" onclick="cookinBulk('public')">${S.allPublic}</button><button class="mini" onclick="cookinBulk('private')">${S.allPrivate}</button></span>` : ""}</h4>
      <div class="ulist">${mineHtml}</div></div>
    <div class="sec"><h4>${S.base}</h4>
      <label class="uchk"><input type="checkbox" ${hideBase?"":"checked"} onchange="cookinHideBase(!this.checked)"> ${S.showBase}</label>
      <div class="hint" style="margin:8px 0 0;display:flex;gap:10px;align-items:center;flex-wrap:wrap">${S.hiddenN(hidden.size)}
        ${hidden.size ? `<button class="mini" onclick="cookinUnhide('*')">${S.restoreAll}</button>` : ""}</div>${hiddenHtml}</div>
    <div class="sec"><h4>${S.others}</h4><div class="ulist">${othersHtml}</div></div>`;
}
window.cookinDish = async function(id, action, visibility){
  try { await api("/api/dishes/" + id, {action, visibility}); } catch(e){ alert(e.message); }
  await refresh(); renderSettings();
};
window.cookinBulk = async function(visibility){
  await api("/api/dishes/bulk-visibility", {visibility}); await refresh(); renderSettings();
};
window.cookinHideBase = async function(v){ hideBase = v; rerender(); await savePrefs(); renderSettings(); };
window.cookinSource = async function(id, on){
  sources = sources.filter(s => s !== id); if(on) sources.push(id);
  await savePrefs(); await refresh(); renderSettings();
};

document.addEventListener("DOMContentLoaded", refresh);
})();
