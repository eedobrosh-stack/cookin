/* Cookin favorites + share link (site-wide). Loaded on the galleries (index.html, en.html), base dish pages and /d/<id>.
   - 🔖 bookmark on every card and on every dish page; "My Favorites" flag at the top filters the gallery.
   - Share button copies the short link: /dish/<id> (base dishes) or /d/<id> (community dishes).
   - Storage: signed-in users -> server profile (/api/favs, follows the account across devices).
              Guests -> cookie "cookin_favs" (1 year), merged into the profile at sign-in. */
(function(){
  if(window.cookinFav) return;
  var EN = document.documentElement.lang === "en" || /[?&]lang=en/.test(location.search);
  var S = EN ? {
    add:"Add to Favorites", remove:"Remove from Favorites", share:"Share", mine:"My Favorites", added:"Added to your favorites",
    removed:"Removed from favorites", copied:"Link copied", empty:"No favorites yet. Press the bookmark on any dish to save it here.",
    guest:"Saved on this device. Sign in to keep your favorites in your account."
  } : {
    add:"הוספה למועדפים", remove:"הסרה מהמועדפים", share:"שיתוף", mine:"המועדפים שלי", added:"נוסף למועדפים",
    removed:"הוסר מהמועדפים", copied:"הקישור הועתק", empty:"עוד אין מועדפים. לחצו על הסימנייה במנה כדי לשמור אותה כאן.",
    guest:"נשמר במכשיר הזה. התחברו כדי לשמור את המועדפים בחשבון."
  };
  var COOKIE = "cookin_favs", ID_RE = /^(\d+|u[0-9a-f]{10})$/, favs = [], user = false, ready = false, tmr = null, onlyFav = false;

  function readCookie(){
    var m = document.cookie.match(/(?:^|;\s*)cookin_favs=([^;]*)/);
    return m ? decodeURIComponent(m[1]).split(",").filter(function(x){return ID_RE.test(x);}) : [];
  }
  function writeCookie(a){
    document.cookie = COOKIE + "=" + encodeURIComponent(a.join(",")) + ";path=/;max-age=31536000;SameSite=Lax" + (location.protocol === "https:" ? ";Secure" : "");
  }
  function clearCookie(){ document.cookie = COOKIE + "=;path=/;max-age=0;SameSite=Lax"; }
  function union(a, b){ var s = {}, o = []; a.concat(b).forEach(function(x){ if(ID_RE.test(x) && !s[x]){ s[x] = 1; o.push(x); } }); return o; }
  function has(id){ return favs.indexOf(String(id)) >= 0; }

  function persist(){
    if(user){
      clearTimeout(tmr);
      tmr = setTimeout(function(){
        fetch("/api/favs", {method:"POST", headers:{"Content-Type":"application/json"}, credentials:"same-origin", body:JSON.stringify({favs:favs})}).catch(function(){});
      }, 300);
    } else writeCookie(favs.slice(-600));
  }

  /* ---------- styles ---------- */
  var css = document.createElement("style");
  css.textContent =
  ".fav-b{position:absolute;top:8px;inset-inline-end:8px;width:34px;height:34px;border-radius:50%;border:0;background:rgba(43,36,32,.55);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;z-index:3;transition:background .15s,transform .15s}"+
  ".fav-b:hover{background:rgba(43,36,32,.8);transform:scale(1.08)}.fav-b.on{background:#e07a3f}"+
  ".fav-b svg,.ft-b svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linejoin:round}.fav-b.on svg,.ft-b.on svg{fill:currentColor}"+
  ".dishtools{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px}"+
  ".ft-b{display:inline-flex;align-items:center;gap:7px;background:#fff;color:#2b2420;border:1px solid #e6dccf;border-radius:999px;padding:8px 14px;font:700 .88rem -apple-system,'Segoe UI',Rubik,Arial,sans-serif;cursor:pointer}"+
  ".ft-b:hover{border-color:#e07a3f}.ft-b.on{background:#fff1e6;border-color:#e07a3f;color:#c05f28}"+
  ".fav-flag{display:inline-flex;width:fit-content;align-items:center;gap:6px;background:#e07a3f;color:#fff;border:0;border-radius:6px 6px 14px 14px;padding:7px 12px 9px;font:700 .85rem -apple-system,'Segoe UI',Rubik,Arial,sans-serif;cursor:pointer;text-decoration:none;white-space:nowrap}"+
  ".fav-flag svg{width:15px;height:15px;fill:currentColor;stroke:currentColor;stroke-width:2;stroke-linejoin:round}.fav-flag b{background:#fff;color:#c05f28;border-radius:999px;min-width:20px;padding:0 6px;text-align:center}"+
  ".fav-flag.act{background:#2b2420}.fav-empty{grid-column:1/-1;text-align:center;color:#8a7d70;padding:40px 12px}"+
  "#favtoast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#2b2420;color:#fff;padding:11px 18px;border-radius:12px;font:.92rem/1.5 -apple-system,'Segoe UI',Rubik,Arial,sans-serif;max-width:min(560px,92vw);z-index:9999;display:none;text-align:center}";
  document.head.appendChild(css);

  var ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4.5L5 21V4a1 1 0 0 1 1-1z"/></svg>';
  var SHARE = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 10.5l6.8-4M8.6 13.5l6.8 4"/></svg>';
  function toast(msg){
    var t = document.getElementById("favtoast");
    if(!t){ t = document.createElement("div"); t.id = "favtoast"; document.body.appendChild(t); }
    t.textContent = msg; t.style.display = "block"; clearTimeout(t._h); t._h = setTimeout(function(){ t.style.display = "none"; }, 2600);
  }
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }

  /* ---------- share ---------- */
  function shortLink(id){ return location.origin + (/^u/.test(id) ? "/d/" : "/dish/") + id; }
  function dishName(el){
    var h = el && (el.closest(".dmain,.dish") || document).querySelector("h1,h2");
    return h ? h.textContent.trim() : document.title;
  }
  function share(id, el){
    var url = shortLink(id), title = dishName(el);
    if(navigator.share && /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)){
      navigator.share({title:title, url:url}).catch(function(){});
      return;
    }
    function done(){ toast(S.copied + ": " + url); }
    if(navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(done, fallback); else fallback();
    function fallback(){
      var ta = document.createElement("textarea"); ta.value = url; ta.style.cssText = "position:fixed;opacity:0"; document.body.appendChild(ta);
      ta.select(); try{ document.execCommand("copy"); }catch(e){} ta.remove(); done();
    }
  }

  /* ---------- toggle + paint ---------- */
  function toggle(id){
    id = String(id);
    if(!ID_RE.test(id)) return;
    var i = favs.indexOf(id), on = i < 0;
    if(on) favs.push(id); else favs.splice(i, 1);
    persist(); paint();
    toast(on ? S.added : S.removed);
    if(on && !user && favs.length === 1) setTimeout(function(){ toast(S.guest); }, 2800);
  }
  function mountTools(){
    [].forEach.call(document.querySelectorAll(".dishtools[data-dish]:not([data-ready])"), function(el){
      var id = el.getAttribute("data-dish"); el.setAttribute("data-ready", "1");
      el.innerHTML = '<button type="button" class="ft-b fav-t" data-fav="'+esc(id)+'">'+ICON+'<span></span></button>'+
                     '<button type="button" class="ft-b sh-t">'+SHARE+'<span>'+S.share+'</span></button>';
      el.querySelector(".fav-t").onclick = function(){ toggle(id); };
      el.querySelector(".sh-t").onclick = function(){ share(id, el); };
    });
  }
  function paint(){
    mountTools();
    [].forEach.call(document.querySelectorAll("[data-fav]"), function(b){
      var on = has(b.getAttribute("data-fav"));
      b.classList.toggle("on", on); b.title = on ? S.remove : S.add; b.setAttribute("aria-pressed", String(on));
      var sp = b.querySelector("span"); if(sp) sp.textContent = on ? S.remove : S.add;
    });
    [].forEach.call(document.querySelectorAll(".fav-flag"), function(f){
      f.querySelector("b").textContent = favs.length; f.classList.toggle("act", onlyFav);
    });
  }

  /* ---------- top flag ---------- */
  var inGallery = function(){ return !!document.getElementById("galleryView") && typeof window.renderGallery === "function"; };
  function setOnly(v){
    onlyFav = v; paint();
    if(inGallery()){
      var gv = document.getElementById("galleryView");
      if(gv && gv.style.display === "none" && typeof window.showView === "function") window.showView("gallery");
      window.renderGallery();
    }
  }
  function mountFlag(){
    if(document.querySelector(".fav-flag")) return;
    var f;
    if(inGallery()){
      f = document.createElement("button"); f.type = "button";
      f.onclick = function(){ setOnly(!onlyFav); };
    } else {
      f = document.createElement("a"); f.href = "/?favs=1" + (EN ? "&lang=en" : "");
      if(EN) f.href = "/en.html?favs=1";
    }
    f.className = "fav-flag"; f.innerHTML = ICON + '<span>' + S.mine + '</span><b>0</b>';
    var host = document.querySelector("header .hwrap .spacer") || document.querySelector(".topbar") || document.querySelector(".wrap > .back");
    if(!host) return;
    if(host.classList.contains("spacer")) host.parentNode.insertBefore(f, host.nextSibling);
    else if(host.classList.contains("back")) host.parentNode.insertBefore(f, host.nextSibling);
    else host.appendChild(f);
  }

  /* ---------- exposed hooks used by the gallery ---------- */
  window.favBtn = function(id){
    return '<button type="button" class="fav-b'+(has(id)?' on':'')+'" data-fav="'+esc(id)+'" title="'+(has(id)?S.remove:S.add)+'" aria-pressed="'+has(id)+'" onclick="event.stopPropagation();cookinFav.toggle(\''+esc(id)+'\')">'+ICON+'</button>';
  };
  window.cookinFav = {
    has:has, toggle:toggle, share:share, only:function(){ return onlyFav; }, emptyMsg:function(){ return '<div class="fav-empty">'+S.empty+'</div>'; },
    list:function(){ return favs.slice(); }
  };

  async function init(){
    var ck = readCookie();
    try{
      var r = await fetch("/api/favs", {credentials:"same-origin"});
      if(r.ok){
        user = true;
        var srv = (await r.json()).favs || [];
        favs = union(srv, ck);
        if(ck.length){ clearCookie(); if(favs.length !== srv.length) persist(); }   // first sign-in: carry the guest favorites into the account
      } else favs = ck;
    }catch(e){ favs = ck; }
    ready = true; mountFlag(); paint();
    if(/[?&]favs=1/.test(location.search) && inGallery()) onlyFav = true;
    if(inGallery()) window.renderGallery();
  }
  if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
  new MutationObserver(function(){ if(ready && document.querySelector(".dishtools[data-dish]:not([data-ready])")) paint(); }).observe(document.documentElement, {childList:true, subtree:true});
})();
