/* Structured ingredient lines: {text, qty, unit, name, prep?, qtyText?}. Shared by dish pages (build-dish-pages.js requires it),
   index.html / en.html and shopping.js. `text` stays as the original line (fallback + search); the rest is the split form.
   unit codes: "" (plain count) g kg ml l tbsp tsp cup can pack bunch clove pinch handful slice sprig */
(function(root){
  var U={
    he:{g:["גרם","גרם"],kg:['ק"ג','ק"ג'],ml:['מ"ל','מ"ל'],l:["ליטר","ליטרים"],tbsp:["כף","כפות"],tsp:["כפית","כפיות"],cup:["כוס","כוסות"],
        can:["פחית","פחיות"],pack:["חבילה","חבילות"],bunch:["צרור","צרורות"],clove:["שן","שיני"],pinch:["קורט","קורט"],
        handful:["חופן","חופנים"],slice:["פרוסה","פרוסות"],sprig:["ענף","ענפים"]},
    en:{g:["g","g"],kg:["kg","kg"],ml:["ml","ml"],l:["l","l"],tbsp:["tbsp","tbsp"],tsp:["tsp","tsp"],cup:["cup","cups"],can:["can","cans"],
        pack:["pack","packs"],bunch:["bunch","bunches"],clove:["clove","cloves"],pinch:["pinch","pinches"],handful:["handful","handfuls"],
        slice:["slice","slices"],sprig:["sprig","sprigs"]}
  };
  var FR={0.25:"¼",0.5:"½",0.75:"¾"};
  function num(q){
    if(q==null) return "";
    var w=Math.floor(q+1e-9), f=Math.round((q-w)*100)/100;
    if(!f) return String(w);
    var g=FR[f]||(Math.abs(f-0.33)<.011?"⅓":Math.abs(f-0.67)<.011?"⅔":null);
    return g ? (w?w:"")+g : String(Math.round(q*100)/100);
  }
  function unitLabel(unit,qty,lang){
    var e=(U[lang]||U.he)[unit]; if(!e) return "";
    return (qty!=null && qty>1) ? e[1] : e[0];
  }
  function amount(l,lang){           // "2", "10 גרם", "2-3 כפות", "" (no amount)
    if(!l || (l.qty==null && !l.qtyText)) return "";
    var q=l.qtyText||num(l.qty), u=unitLabel(l.unit,l.qty,lang);
    return u ? q+" "+u : q;
  }
  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
  function html(l,lang){             // <li> inner HTML; falls back to the original text for unstructured lines
    if(!l || !l.name) return esc(l&&l.text||"");
    var a=amount(l,lang), clove=(l.unit==="clove");
    var name=clove ? esc(unitLabel("clove",l.qty,lang)+" "+l.name) : esc(l.name);
    if(clove) a=a.replace(/\s*\S+$/,"");   // "2 שיני" is carried by the name for clove ("שיני שום")
    return '<span class="iq" data-q="'+(l.qty==null?"":l.qty)+'" data-u="'+esc(l.unit||"")+'">'+esc(a)+'</span><span class="in" data-n="'+esc(l.name)+'">'+name+(l.prep?' <i class="ip">'+esc(l.prep)+'</i>':'')+'</span>';
  }
  var api={units:U,num:num,unitLabel:unitLabel,amount:amount,html:html};
  if(typeof module!=="undefined"&&module.exports) module.exports=api; else root.cookinIng=api;
})(typeof window!=="undefined"?window:this);
