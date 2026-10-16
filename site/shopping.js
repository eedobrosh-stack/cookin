/* Cookin shopping list (site-wide). Loaded on every page (gallery, base dish pages, /d/<id>, en.html).
   - Dish pages: a "add to shopping list" button under the ingredients opens checkboxes (all ticked) + quantity boxes.
   - A floating 🛒 button opens the list drawer from any page.
   - Storage: signed-in users -> server (/api/shopping, follows the account across devices).
              Visitors -> localStorage "cookin-shopping-anon" (fallback), merged into the account at sign-in. */
(function(){
  if(window.__cookinShop) return; window.__cookinShop = true;
  var EN = document.documentElement.lang === "en" || /[?&]lang=en/.test(location.search);
  var S = EN ? {
    add:"🛒 Add to shopping list", addSel:"Add selected", cancel:"Cancel", added:function(n){return n+" item"+(n===1?"":"s")+" added to your list";},
    none:"Select at least one ingredient", title:"Shopping list", empty:"Your list is empty. Open a dish and press “Add to shopping list”.",
    copy:"Copy", copied:"Copied", wa:"Send via WhatsApp", clearDone:"Remove checked", clearAll:"Clear all", confirmAll:"Clear the whole list?",
    anon:"Saved on this device only.", signin:"Sign in to keep it in your account", qty:"Quantity", rm:"Remove", close:"Close", saved:"Saved to your account"
  } : {
    add:"🛒 הוסף לרשימת קניות", addSel:"הוסף את המסומנים", cancel:"ביטול", added:function(n){return n===1?"נוסף מצרך אחד לרשימה":"נוספו "+n+" מצרכים לרשימה";},
    none:"סמנו לפחות מצרך אחד", title:"רשימת קניות", empty:"הרשימה ריקה. פתחו מנה ולחצו על ״הוסף לרשימת קניות״.",
    copy:"העתק", copied:"הועתק", wa:"שלח בוואטסאפ", clearDone:"הסר מסומנים", clearAll:"נקה הכול", confirmAll:"לנקות את כל הרשימה?",
    anon:"נשמר במכשיר הזה בלבד.", signin:"התחברו כדי לשמור בחשבון", qty:"כמות", rm:"הסר", close:"סגור", saved:"נשמר בחשבון"
  };
  var KEY = "cookin-shopping-anon", user = false, items = [], loaded = false, tmr = null;

  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
  function lsGet(){try{return JSON.parse(localStorage.getItem(KEY)||"[]")||[];}catch(e){return [];}}
  function lsSet(v){try{ if(v&&v.length) localStorage.setItem(KEY,JSON.stringify(v)); else localStorage.removeItem(KEY);}catch(e){}}
  function merge(base, extra){
    var seen={}; base.forEach(function(i){seen[i.id]=1;});
    extra.forEach(function(i){ if(i&&i.id&&!seen[i.id]){base.push(i);seen[i.id]=1;} });
    return base;
  }
  function persist(){
    if(user){
      clearTimeout(tmr);
      tmr=setTimeout(function(){
        fetch("/api/shopping",{method:"POST",headers:{"Content-Type":"application/json"},credentials:"same-origin",body:JSON.stringify({items:items})}).catch(function(){});
      },350);
    } else lsSet(items);
    paint();
  }
  async function init(){
    try{
      var r = await fetch("/api/shopping",{credentials:"same-origin"});
      if(r.ok){
        user = true;
        var srv = (await r.json()).items || [], loc = lsGet();
        items = merge(srv, loc);
        if(loc.length){ lsSet([]); persist(); }   // first sign-in: carry the visitor list into the account
      } else items = lsGet();
    }catch(e){ items = lsGet(); }
    loaded = true; paint(); hook();
  }

  /* ---------- floating button + drawer ---------- */
  var css = document.createElement("style");
  css.textContent =
  ".cs-fab{position:fixed;z-index:9990;bottom:18px;inset-inline-start:18px;background:#e07a3f;color:#fff;border:0;border-radius:999px;padding:11px 16px;font:700 .95rem system-ui,Arial;box-shadow:0 6px 20px rgba(0,0,0,.25);cursor:pointer;display:flex;gap:6px;align-items:center}"+
  ".cs-fab b{background:#fff;color:#c05f28;border-radius:999px;min-width:22px;padding:0 6px;text-align:center}"+
  ".cs-dr{position:fixed;z-index:9995;top:0;bottom:0;inset-inline-end:0;width:min(400px,100%);background:#fffdf9;color:#2b2420;box-shadow:-8px 0 30px rgba(0,0,0,.25);display:none;flex-direction:column;font-family:-apple-system,'Segoe UI',Rubik,Arial,sans-serif}"+
  ".cs-dr.open{display:flex}.cs-dr h3{padding:16px 18px;border-bottom:1px solid #eee5d8;display:flex;justify-content:space-between;align-items:center;font-size:1.1rem}"+
  ".cs-dr h3 button{border:0;background:#f3ece1;border-radius:8px;padding:6px 10px;cursor:pointer}"+
  ".cs-body{flex:1;overflow-y:auto;padding:10px 18px}.cs-g{font-weight:700;color:#6b5d4f;margin:14px 0 4px;font-size:.9rem}.cs-g a{color:inherit}"+
  ".cs-it{display:flex;gap:10px;align-items:center;padding:6px 0;border-bottom:1px dashed #eee5d8;font-size:.95rem}.cs-it .t{flex:1;line-height:1.35}"+
  ".cs-it.done .t{text-decoration:line-through;opacity:.45}.cs-it input[type=number]{width:52px;padding:3px 5px;border:1px solid #eee5d8;border-radius:7px;text-align:center}"+
  ".cs-it input[type=checkbox]{width:18px;height:18px;accent-color:#e07a3f}.cs-it .x{border:0;background:none;cursor:pointer;color:#a53a2c;font-size:1rem}"+
  ".cs-ft{padding:12px 18px;border-top:1px solid #eee5d8;font-size:.85rem;color:#8a7f74}.cs-ft .r{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}"+
  ".cs-ft .r button{border:0;border-radius:9px;padding:8px 11px;background:#f3ece1;font-weight:700;cursor:pointer;color:#2b2420}"+
  ".cs-btn{margin-top:16px;width:100%;background:#e07a3f;color:#fff;border:0;border-radius:12px;padding:12px;font-size:1rem;font-weight:700;cursor:pointer}"+
  ".cs-bar{display:flex;gap:8px;margin-top:14px}.cs-bar button{flex:1;border:0;border-radius:10px;padding:10px;font-weight:700;cursor:pointer}"+
  ".cs-go{background:#e07a3f;color:#fff}.cs-no{background:#f3ece1;color:#2b2420}"+
  ".ing-list.cs-on li{align-items:center}.ing-list.cs-on li::before{content:none!important}.ing-list.cs-on .cchk{flex:0 0 auto;width:18px;height:18px;accent-color:#e07a3f}"+
  ".ing-list.cs-on .ctxt{flex:1}.ing-list.cs-on .cqty{flex:0 0 auto;width:56px;padding:4px 6px;border:1px solid #eee5d8;border-radius:8px;text-align:center}"+
  ".ing-list.cs-on li.off .ctxt{opacity:.4;text-decoration:line-through}.ing-list.cs-on li.off .cqty{visibility:hidden}"+
  ".cs-toast{position:fixed;z-index:9999;bottom:76px;inset-inline-start:18px;background:#2b2420;color:#fff;padding:10px 16px;border-radius:10px;font:600 .9rem system-ui,Arial}";
  document.head.appendChild(css);

  var fab = document.createElement("button"); fab.className="cs-fab"; fab.setAttribute("aria-label",S.title);
  var dr = document.createElement("div"); dr.className="cs-dr"; dr.dir = EN ? "ltr" : "rtl";
  function ready(f){ if(document.body) f(); else document.addEventListener("DOMContentLoaded",f); }
  ready(function(){ document.body.append(fab, dr); fab.onclick=function(){dr.classList.toggle("open"); paint();}; paint(); });

  function text(){
    return items.filter(function(i){return !i.done;}).map(function(i){return "• "+i.qty+" × "+i.text;}).join("\n");
  }
  function toast(m){
    var t=document.createElement("div");t.className="cs-toast";t.textContent=m;document.body.appendChild(t);setTimeout(function(){t.remove();},2200);
  }
  function paint(){
    if(!fab.isConnected) return;
    fab.innerHTML = "🛒 <b>"+items.filter(function(i){return !i.done;}).length+"</b>";
    if(!dr.classList.contains("open")) return;
    var groups = {}, order = [];
    items.forEach(function(i,ix){ var g=i.dish||"-"; if(!groups[g]){groups[g]={name:i.dishName,url:i.dish,rows:[]};order.push(g);} groups[g].rows.push([i,ix]); });
    var body = !items.length ? '<p style="color:#8a7f74;padding:16px 0">'+S.empty+'</p>' : order.map(function(g){
      var G=groups[g];
      return '<div class="cs-g">'+(G.url&&G.url!=="-"?'<a href="'+esc(G.url)+'">':'')+esc(G.name||"")+(G.url&&G.url!=="-"?'</a>':'')+'</div>'+
        G.rows.map(function(p){var i=p[0];return '<div class="cs-it'+(i.done?' done':'')+'" data-i="'+p[1]+'"><input type="checkbox" '+(i.done?'checked':'')+'><span class="t">'+esc(i.text)+'</span>'+
          '<input type="number" min="1" value="'+i.qty+'" title="'+S.qty+'"><button class="x" title="'+S.rm+'">✕</button></div>';}).join("");
    }).join("");
    dr.innerHTML = '<h3>'+S.title+'<button class="cs-close">'+S.close+'</button></h3><div class="cs-body">'+body+'</div>'+
      '<div class="cs-ft"><div>'+(user?S.saved:S.anon+' <a href="/auth/login?next='+encodeURIComponent(location.pathname+location.hash)+'">'+S.signin+'</a>')+'</div>'+
      (items.length?'<div class="r"><button data-a="copy">'+S.copy+'</button><button data-a="wa">'+S.wa+'</button><button data-a="done">'+S.clearDone+'</button><button data-a="all">'+S.clearAll+'</button></div>':'')+'</div>';
    dr.querySelector(".cs-close").onclick=function(){dr.classList.remove("open");};
    [].forEach.call(dr.querySelectorAll(".cs-it"),function(row){
      var ix=+row.dataset.i, it=items[ix];
      row.querySelector("input[type=checkbox]").onchange=function(e){it.done=e.target.checked;persist();};
      row.querySelector("input[type=number]").onchange=function(e){it.qty=Math.max(1,parseInt(e.target.value,10)||1);persist();};
      row.querySelector(".x").onclick=function(){items.splice(ix,1);persist();};
    });
    [].forEach.call(dr.querySelectorAll(".cs-ft button"),function(b){b.onclick=function(){
      var a=b.dataset.a;
      if(a==="copy"){try{navigator.clipboard.writeText(text());toast(S.copied);}catch(e){}}
      else if(a==="wa"){window.open("https://wa.me/?text="+encodeURIComponent(S.title+"\n"+text()),"_blank","noopener");}
      else if(a==="done"){items=items.filter(function(i){return !i.done;});persist();}
      else if(a==="all"){if(confirm(S.confirmAll)){items=[];persist();}}
    };});
  }

  /* ---------- dish pages: ingredient picker ---------- */
  function dishInfo(){
    var h=document.querySelector(".dhead h1, .dhead h2, h1");
    return {url:location.pathname+location.search+location.hash, name:h?h.textContent.trim():document.title};
  }
  function hook(){
    [].forEach.call(document.querySelectorAll(".ing-list:not([data-cs])"),setup);
  }
  function setup(list){
    list.dataset.cs="1";
    var btn=document.createElement("button");btn.className="cs-btn";btn.textContent=S.add;
    list.after(btn);
    var lis=[].slice.call(list.querySelectorAll("li"));
    if(!lis.length){btn.remove();return;}
    function leave(){
      list.classList.remove("cs-on");
      lis.forEach(function(li){var t=li.querySelector(".ctxt");if(t){li.textContent=t.textContent;li.classList.remove("off");}});
      var b=list.parentNode.querySelector(".cs-bar");if(b)b.remove();btn.style.display="";
    }
    btn.onclick=function(){
      list.classList.add("cs-on");
      lis.forEach(function(li){
        var t=li.textContent;li.textContent="";
        var c=document.createElement("input");c.type="checkbox";c.checked=true;c.className="cchk";
        var s=document.createElement("span");s.className="ctxt";s.textContent=t;
        var q=document.createElement("input");q.type="number";q.min="1";q.value="1";q.className="cqty";q.title=S.qty;
        c.onchange=function(){li.classList.toggle("off",!c.checked);};
        li.append(c,s,q);
      });
      btn.style.display="none";
      var bar=document.createElement("div");bar.className="cs-bar";
      bar.innerHTML='<button class="cs-go">'+S.addSel+'</button><button class="cs-no">'+S.cancel+'</button>';
      bar.querySelector(".cs-no").onclick=leave;
      bar.querySelector(".cs-go").onclick=function(){
        var d=dishInfo(),n=0;
        lis.forEach(function(li){
          var c=li.querySelector(".cchk");if(!c||!c.checked)return;
          var txt=li.querySelector(".ctxt").textContent.trim(),id=d.url+"|"+txt,qty=Math.max(1,parseInt(li.querySelector(".cqty").value,10)||1);
          var ex=items.filter(function(i){return i.id===id;})[0];
          if(ex){ex.qty+=qty;ex.done=false;}else items.push({id:id,dish:d.url,dishName:d.name,text:txt,qty:qty,done:false});
          n++;
        });
        if(!n){toast(S.none);return;}
        leave();persist();toast(S.added(n));
      };
      list.after(bar);
    };
  }
  new MutationObserver(function(){ if(loaded) hook(); }).observe(document.documentElement,{childList:true,subtree:true});
  init();
})();
