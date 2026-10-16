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

  var I = window.cookinIng || {unitLabel:function(){return "";}, num:function(q){return String(q);}};
  function ul(it){ return it.unit ? I.unitLabel(it.unit,it.qty,EN?"en":"he") : ""; }
  function amt(it){ var u=ul(it); return I.num(it.qty)+(u?" "+u:""); }
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
  ".cs-body{flex:1;overflow-y:auto;padding:10px 18px}.cs-g{font-weight:700;color:#6b5d4f;margin:16px 0 4px;font-size:.92rem;background:#f3ece1;border-radius:8px;padding:5px 10px}.cs-g .n{float:inline-end;color:#8a7f74;font-weight:600}.cs-it small{display:block;color:#8a7f74;font-size:.75rem}.cs-it .tot{font-size:.9rem;white-space:nowrap}"+
  ".cs-it{display:flex;gap:10px;align-items:center;padding:6px 0;border-bottom:1px dashed #eee5d8;font-size:.95rem}.cs-it .t{flex:1;line-height:1.35}"+
  ".cs-it.done .t{text-decoration:line-through;opacity:.45}.cs-it input[type=number]{width:62px;padding:3px 5px;border:1px solid #eee5d8;border-radius:7px;text-align:center}"+
  ".cs-it input[type=checkbox]{width:18px;height:18px;accent-color:#e07a3f}.cs-it .u{min-width:2.4em;font-size:.82rem;color:#8a7f74}.cs-it .x{border:0;background:none;cursor:pointer;color:#a53a2c;font-size:1rem}"+
  ".cs-ft{padding:12px 18px;border-top:1px solid #eee5d8;font-size:.85rem;color:#8a7f74}.cs-ft .r{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}"+
  ".cs-ft .r button{border:0;border-radius:9px;padding:8px 11px;background:#f3ece1;font-weight:700;cursor:pointer;color:#2b2420}"+
  ".cs-btn{margin-top:16px;width:100%;background:#e07a3f;color:#fff;border:0;border-radius:12px;padding:12px;font-size:1rem;font-weight:700;cursor:pointer}"+
  ".cs-bar{display:flex;gap:8px;margin-top:14px}.cs-bar button{flex:1;border:0;border-radius:10px;padding:10px;font-weight:700;cursor:pointer}"+
  ".cs-go{background:#e07a3f;color:#fff}.cs-no{background:#f3ece1;color:#2b2420}"+
  ".ing-list.cs-on li{align-items:center}.ing-list.cs-on li::before{content:none!important}.ing-list.cs-on .cchk{flex:0 0 auto;width:18px;height:18px;accent-color:#e07a3f}"+
  ".ing-list.cs-on .ctxt{flex:1}.ing-list.cs-on .cunit{flex:0 0 3em;font-size:.82rem;color:#8a7f74}.ing-list.cs-on .cqty{flex:0 0 auto;width:56px;padding:4px 6px;border:1px solid #eee5d8;border-radius:8px;text-align:center}"+
  ".ing-list.cs-on li.off .ctxt{opacity:.4;text-decoration:line-through}.ing-list.cs-on li.off .cqty{visibility:hidden}"+
  ".cs-toast{position:fixed;z-index:9999;bottom:76px;inset-inline-start:18px;background:#2b2420;color:#fff;padding:10px 16px;border-radius:10px;font:600 .9rem system-ui,Arial}";
  document.head.appendChild(css);

  var fab = document.createElement("button"); fab.className="cs-fab"; fab.setAttribute("aria-label",S.title);
  var dr = document.createElement("div"); dr.className="cs-dr"; dr.dir = EN ? "ltr" : "rtl";
  function ready(f){ if(document.body) f(); else document.addEventListener("DOMContentLoaded",f); }
  ready(function(){ document.body.append(fab, dr); fab.onclick=function(){dr.classList.toggle("open"); paint();}; paint(); });

  /* ---------- sections (shopping aisles) ---------- */
  var SEC = [
    ["produce","🥬",EN?"Produce":"ירקות ופירות"],["herbs","🌿",EN?"Herbs":"עשבי תיבול"],["meatfish","🥩",EN?"Meat & fish":"בשר ודגים"],
    ["dairy","🧀",EN?"Dairy & eggs":"חלב וביצים"],["frozen","🧊",EN?"Frozen":"קפואים"],["canned","🥫",EN?"Canned & jarred":"שימורים וצנצנות"],["dry","🍝",EN?"Dry goods & grains":"יבשים ודגנים"],
    ["oils","🫒",EN?"Oils & sauces":"שמנים ורטבים"],["spices","🧂",EN?"Spices":"תבלינים"],["other","🛒",EN?"Other":"אחר"]];
  var KW = EN ? [
    ["herbs",/\b(parsley|cilantro|coriander|basil|mint|dill|chives|thyme|rosemary|sage|tarragon|oregano leaves|herbs?)\b/],
    ["meatfish",/\b(chicken|beef|lamb|pork|turkey|steak|ribs?|brisket|sausage|bacon|ham|meat|salmon|tuna fillet|fish|cod|tilapia|sea bass|shrimp|prawns?|squid|fillet|mince|ground (beef|meat))\b/],
    ["dairy",/\b(milk|cream|butter|cheese|yogh?urt|labneh|eggs?|tofu|parmesan|mozzarella|feta|ricotta|margarine)\b/],
    ["frozen",/\b(frozen)\b/],
    ["canned",/\b(canned|tinned|tomato paste|coconut (milk|cream)|olives?|pickles?|capers?|tahini|jam)\b/],
    ["oils",/\b(oil|vinegar|sauce|mustard|ketchup|mayo|honey|wine|beer|stock|broth|water)\b/],
    ["spices",/\b(salt|pepper|paprika|cumin|turmeric|cinnamon|spice|seasoning|chili flakes|curry powder|za'?atar|nutmeg)\b/],
    ["dry",/\b(pasta|spaghetti|rice|noodles?|flour|bread|breadcrumbs|sugar|oats|couscous|lentils?|beans|nuts?|almonds?|walnuts?|seeds?|cornstarch|cornflour|baking|chocolate|pita|tortilla|baguette)\b/],
    ["produce",/\b(onion|garlic|ginger|tomato|potato|carrot|cucumber|lemon|lime|pepper|cabbage|lettuce|spinach|mushroom|zucchini|eggplant|avocado|apple|banana|orange|chili|corn|celery|broccoli|cauliflower|scallion|vegetable|fruit)/]
  ] : [
    ["herbs",/(פטרוזיליה|כוסברה|בזיליקום|נענע|שמיר|עירית|טימין|רוזמרין|מרווה|עשבי|אזוב)/],
    ["meatfish",/(עוף|חזה|שוק|כנפיים|בקר|בשר|כבש|הודו|סטייק|צלע|אנטריקוט|נקניק|בייקון|דג|סלמון|טונה טרייה|פילה|שרימפס|סרטנ|קלמרי|טחון|בריסקט|מושט|דניס|לברק)/],
    ["dairy",/(חלב|שמנת|חמאה|גבינ|יוגורט|לאבנה|ביצ|טופו|פרמזן|מוצרלה|פטה|ריקוטה|מרגרינה|קשקבל|קוטג)/],
    ["frozen",/(קפוא)/],
    ["canned",/(שימורי|משומר|רסק עגבניות|קרם קוקוס|חלב קוקוס|זיתים|מלפפונים חמוצים|חמוצים|צלפים|טחינה|ריבה|במבוק|קופסת)/],
    ["oils",/(שמן|חומץ|רוטב|חרדל|קטשופ|מיונז|דבש|סילאן|יין|בירה|ציר|מים|סויה)/],
    ["spices",/(מלח|פלפל שחור|פלפל לבן|פפריקה|כמון|כורכום|קינמון|תבלין|פתיתי צ'ילי|קארי אבקה|זעתר|אגוז מוסקט|אורגנו|קורט)/],
    ["dry",/(פסטה|ספגטי|אורז|אטריות|קמח|לחם|פירורי|סוכר|שיבולת|קוסקוס|עדשים|שעועית|אגוז|שקד|שומשום|גרעינ|קורנפלור|אבקת אפייה|שוקולד|פיתה|טורטייה|באגט|בגט)/],
    ["produce",/(בצל|שום|ג'ינג'ר|עגבני|תפוח אדמה|גזר|מלפפון|לימון|ליים|גמבה|פלפל|כרוב|חסה|תרד|פטריות|קישוא|חציל|אבוקדו|תפוח|בננה|תפוז|צ'ילי|תירס|סלרי|ברוקולי|כרובית|ירק|פרי)/]
  ];
  var TBL = window.cookinSections || {};
  function sectionOf(name){
    var n=String(name||"").trim(), t=(TBL[EN?"en":"he"]||{})[EN?n.toLowerCase():n];
    if(t) return t;
    var l=EN?n.toLowerCase():n;
    for(var i=0;i<KW.length;i++) if(KW[i][1].test(l)) return KW[i][0];
    return "other";
  }
  /* rows: one per (section, name, unit); several dishes asking for the same thing are summed */
  function rows(){
    var map={}, order=[];
    items.forEach(function(it,ix){
      var sec=sectionOf(it.text), k=sec+"|"+it.text.toLowerCase()+"|"+(it.unit||"");
      if(!map[k]){map[k]={sec:sec,name:it.text,unit:it.unit||"",ix:[],dishes:[]};order.push(k);}
      var r=map[k]; r.ix.push(ix); if(it.dishName&&r.dishes.indexOf(it.dishName)<0) r.dishes.push(it.dishName);
    });
    return order.map(function(k){return map[k];});
  }
  function rowTotal(r){return Math.round(r.ix.reduce(function(a,i){return a+items[i].qty;},0)*100)/100;}
  function rowAmt(r){var q=rowTotal(r), u=r.unit?I.unitLabel(r.unit,q,EN?"en":"he"):"";return I.num(q)+(u?" "+u:"");}
  function text(){
    var all=rows().filter(function(r){return !r.ix.every(function(i){return items[i].done;});}), out=[];
    SEC.forEach(function(s){
      var rs=all.filter(function(r){return r.sec===s[0];}); if(!rs.length) return;
      out.push(s[1]+" "+s[2]); rs.forEach(function(r){out.push("• "+rowAmt(r)+" "+r.name);});
    });
    return out.join("\n");
  }
  function toast(m){
    var t=document.createElement("div");t.className="cs-toast";t.textContent=m;document.body.appendChild(t);setTimeout(function(){t.remove();},2200);
  }
  function paint(){
    if(!fab.isConnected) return;
    fab.innerHTML = "🛒 <b>"+items.filter(function(i){return !i.done;}).length+"</b>";
    if(!dr.classList.contains("open")) return;
    var all=rows(), body="";
    if(!items.length) body='<p style="color:#8a7f74;padding:16px 0">'+S.empty+'</p>';
    SEC.forEach(function(s){
      var rs=all.filter(function(r){return r.sec===s[0];}); if(!rs.length) return;
      body+='<div class="cs-g">'+s[1]+' '+esc(s[2])+' <span class="n">'+rs.length+'</span></div>';
      rs.forEach(function(r){
        var done=r.ix.every(function(i){return items[i].done;}), multi=r.ix.length>1, k=all.indexOf(r);
        body+='<div class="cs-it'+(done?' done':'')+'" data-r="'+k+'"><input type="checkbox" '+(done?'checked':'')+'>'+
          '<span class="t">'+esc(r.name)+(r.dishes.length?'<small>'+r.dishes.map(esc).join(" · ")+'</small>':'')+'</span>'+
          (multi?'<b class="tot">'+esc(rowAmt(r))+'</b>':'<input type="number" min="0" step="any" value="'+items[r.ix[0]].qty+'" title="'+S.qty+'"><span class="u">'+esc(r.unit?I.unitLabel(r.unit,items[r.ix[0]].qty,EN?"en":"he"):"")+'</span>')+
          '<button class="x" title="'+S.rm+'">✕</button></div>';
      });
    });
    dr.innerHTML = '<h3>'+S.title+'<button class="cs-close">'+S.close+'</button></h3><div class="cs-body">'+body+'</div>'+
      '<div class="cs-ft"><div>'+(user?S.saved:S.anon+' <a href="/auth/login?next='+encodeURIComponent(location.pathname+location.hash)+'">'+S.signin+'</a>')+'</div>'+
      (items.length?'<div class="r"><button data-a="copy">'+S.copy+'</button><button data-a="wa">'+S.wa+'</button><button data-a="done">'+S.clearDone+'</button><button data-a="all">'+S.clearAll+'</button></div>':'')+'</div>';
    dr.querySelector(".cs-close").onclick=function(){dr.classList.remove("open");};
    [].forEach.call(dr.querySelectorAll(".cs-it"),function(row){
      var r=all[+row.dataset.r];
      row.querySelector("input[type=checkbox]").onchange=function(e){r.ix.forEach(function(i){items[i].done=e.target.checked;});persist();};
      var q=row.querySelector("input[type=number]");
      if(q) q.onchange=function(e){items[r.ix[0]].qty=Math.max(0.01,parseFloat(e.target.value)||1);persist();};
      row.querySelector(".x").onclick=function(){var drop={};r.ix.forEach(function(i){drop[i]=1;});items=items.filter(function(_,i){return !drop[i];});persist();};
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
      lis.forEach(function(li){if(li._orig!=null){li.innerHTML=li._orig;li._orig=null;li.classList.remove("off");}});
      var b=list.parentNode.querySelector(".cs-bar");if(b)b.remove();btn.style.display="";
    }
    btn.onclick=function(){
      list.classList.add("cs-on");
      lis.forEach(function(li){
        var iq=li.querySelector(".iq"), inn=li.querySelector(".in[data-n]");
        li._orig=li.innerHTML;
        var name=inn?inn.dataset.n:li.textContent.trim(), unit=iq?iq.dataset.u||"":"", q0=iq&&iq.dataset.q!==""&&iq.dataset.q!=null?parseFloat(iq.dataset.q):1;
        li._cs={name:name,unit:unit};
        li.textContent="";
        var c=document.createElement("input");c.type="checkbox";c.checked=true;c.className="cchk";
        var s=document.createElement("span");s.className="ctxt";s.textContent=name;
        var q=document.createElement("input");q.type="number";q.min="0";q.step="any";q.value=q0;q.className="cqty";q.title=S.qty;
        var u=document.createElement("span");u.className="cunit";u.textContent=unit?I.unitLabel(unit,q0,EN?"en":"he"):"";
        q.oninput=function(){u.textContent=unit?I.unitLabel(unit,parseFloat(q.value)||0,EN?"en":"he"):"";};
        c.onchange=function(){li.classList.toggle("off",!c.checked);};
        li.append(c,s,q,u);
      });
      btn.style.display="none";
      var bar=document.createElement("div");bar.className="cs-bar";
      bar.innerHTML='<button class="cs-go">'+S.addSel+'</button><button class="cs-no">'+S.cancel+'</button>';
      bar.querySelector(".cs-no").onclick=leave;
      bar.querySelector(".cs-go").onclick=function(){
        var d=dishInfo(),n=0;
        lis.forEach(function(li){
          var c=li.querySelector(".cchk");if(!c||!c.checked)return;
          var txt=li._cs.name,unit=li._cs.unit,id=d.url+"|"+txt,qty=Math.max(0.01,parseFloat(li.querySelector(".cqty").value)||1);
          var ex=items.filter(function(i){return i.id===id;})[0];
          if(ex){ex.qty=Math.round((ex.qty+qty)*100)/100;ex.done=false;}else items.push({id:id,dish:d.url,dishName:d.name,text:txt,qty:qty,unit:unit,done:false});
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
