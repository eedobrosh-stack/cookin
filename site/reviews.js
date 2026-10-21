/* Ratings (1-5) + comments (private/public) for a dish. Mounts into #rv-stars and #reviews (data-dish = dish id).
   Anyone can see them; changing anything needs a Google sign-in (non-members get a "connect" prompt). */
(function(){
  var starsEl = document.getElementById('rv-stars'), boxEl = document.getElementById('reviews');
  var host = starsEl || boxEl; if(!host) return;
  var id = host.getAttribute('data-dish'); if(!id) return;
  var en = (document.documentElement.lang||'he') === 'en';
  var T = en ? {
    avg:'average', none:'No ratings yet', n:'ratings', yours:'Your rating', title:'💬 Comments',
    ph:'Write a comment…', pub:'🌍 Public (everyone sees it)', priv:'🔒 Private (only me)', send:'Post',
    mk_pub:'Make public', mk_priv:'Make private', del:'Delete', none_c:'No comments yet. Be the first!',
    login:'To rate or comment you need to connect with Google.', connect:'Connect with Google', close:'Close',
    err:'Something went wrong, try again', priv_tag:'🔒 private', clear:'remove my rating'
  } : {
    avg:'ממוצע', none:'עוד אין דירוגים', n:'דירוגים', yours:'הדירוג שלך', title:'💬 תגובות',
    ph:'כתבו תגובה…', pub:'🌍 ציבורית (כולם רואים)', priv:'🔒 פרטית (רק אני)', send:'פרסם',
    mk_pub:'הפוך לציבורית', mk_priv:'הפוך לפרטית', del:'מחק', none_c:'עוד אין תגובות. תהיו הראשונים!',
    login:'כדי לדרג או להגיב צריך להתחבר עם גוגל.', connect:'התחברות עם גוגל', close:'סגור',
    err:'משהו השתבש, נסו שוב', priv_tag:'🔒 פרטית', clear:'הסר את הדירוג שלי'
  };
  var css = document.createElement('style');
  css.textContent =
   '.rv-stars{display:flex;flex-direction:column;gap:4px;align-items:flex-start;margin-bottom:6px}'+
   '@media(min-width:700px){.rv-stars{position:absolute;top:18px;inset-inline-end:26px;margin:0}}'+
   '.dhead{position:relative}'+
   '.rv-row{display:flex;align-items:center;gap:8px;direction:ltr}'+
   '.rv-star{font-size:34px;line-height:1;cursor:pointer;color:#e6d9c3;user-select:none;position:relative;transition:transform .1s}'+
   '.rv-star:hover{transform:scale(1.12)}.rv-star.on{color:#f5a623}.rv-star.half{color:#f5a623}'+
   '.rv-star.part{background:linear-gradient(90deg,#f5a623 var(--p),#e6d9c3 var(--p));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}'+
   '.rv-meta{font-size:.82rem;color:var(--muted,#8a7f74);display:flex;gap:10px;flex-wrap:wrap;align-items:center}'+
   '.rv-meta button{background:none;border:0;color:var(--accent-dark,#c05f28);cursor:pointer;font:inherit;text-decoration:underline;padding:0}'+
   '.rv-notice{background:var(--amber-bg,#fdf3e0);color:var(--amber,#b7791f);border:1px solid var(--line,#eee5d8);border-radius:12px;padding:10px 14px;margin:8px 0;font-size:.9rem;display:flex;gap:10px;align-items:center;flex-wrap:wrap}'+
   '.rv-notice a,.rv-notice button{background:var(--accent,#e07a3f);color:#fff;border:0;border-radius:999px;padding:6px 14px;cursor:pointer;text-decoration:none;font:inherit;font-weight:700}'+
   '.rv-notice button.x{background:none;color:var(--muted,#8a7f74);font-weight:400}'+
   '#reviews{margin-top:26px;padding-top:16px;border-top:1px dashed var(--line,#eee5d8)}'+
   '#reviews h3{margin-bottom:10px}'+
   '.rv-form textarea{width:100%;border:1px solid var(--line,#eee5d8);border-radius:12px;padding:10px 12px;font:inherit;resize:vertical;min-height:70px;background:var(--card,#fff);color:inherit}'+
   '.rv-form .bar{display:flex;gap:10px;align-items:center;margin-top:8px;flex-wrap:wrap}'+
   '.rv-form select{border:1px solid var(--line,#eee5d8);border-radius:999px;padding:7px 12px;font:inherit;background:var(--card,#fff);color:inherit}'+
   '.rv-form .send{background:var(--accent,#e07a3f);color:#fff;border:0;border-radius:999px;padding:8px 20px;font:inherit;font-weight:700;cursor:pointer}'+
   '.rv-c{display:flex;gap:10px;padding:12px 0;border-bottom:1px solid var(--line,#eee5d8)}'+
   '.rv-av{width:34px;height:34px;border-radius:50%;background:var(--chip,#f3ece1);flex:0 0 34px;display:flex;align-items:center;justify-content:center;font-weight:700;overflow:hidden}'+
   '.rv-av img{width:100%;height:100%;object-fit:cover}'+
   '.rv-c .who{font-weight:700;font-size:.88rem}.rv-c .when{color:var(--muted,#8a7f74);font-size:.75rem;margin-inline-start:6px;font-weight:400}'+
   '.rv-c .tag{font-size:.72rem;background:var(--chip,#f3ece1);border-radius:999px;padding:1px 8px;margin-inline-start:6px;font-weight:400}'+
   '.rv-c .txt{margin-top:3px;white-space:pre-wrap;word-break:break-word;line-height:1.5}'+
   '.rv-c .acts{margin-top:4px;display:flex;gap:12px}.rv-c .acts button{background:none;border:0;color:var(--muted,#8a7f74);font-size:.78rem;cursor:pointer;padding:0;text-decoration:underline}'+
   '.rv-empty{color:var(--muted,#8a7f74);padding:8px 0}';
  document.head.appendChild(css);

  var state = {avg:0,count:0,mine:null,comments:[],signedIn:false}, hover = 0, noticeAt = null;
  var api = '/api/reviews/' + encodeURIComponent(id);
  var loginUrl = '/auth/login?next=' + encodeURIComponent(location.pathname + location.search);
  function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }

  function noticeHtml(){
    return '<div class="rv-notice">🔐 '+T.login+' <a href="'+loginUrl+'">'+T.connect+'</a><button class="x" data-x="1">'+T.close+'</button></div>';
  }
  function load(){
    fetch(api,{credentials:'same-origin'}).then(function(r){return r.json();}).then(function(j){
      if(j && j.ok){ state = j; render(); }
    }).catch(function(){});
  }
  function send(body){
    return fetch(api,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
      .then(function(r){ return r.json().then(function(j){ return {st:r.status,j:j}; }); })
      .then(function(o){
        if(o.st===401){ state.signedIn=false; noticeAt = body.action==='rate' ? 'stars' : 'form'; render(); return false; }
        if(o.j && o.j.ok){ state=o.j; noticeAt=null; render(); return true; }
        alert(T.err); return false;
      }).catch(function(){ alert(T.err); return false; });
  }
  function starsHtml(){
    var shown = hover || state.mine || 0, h = '<div class="rv-row" role="radiogroup">';
    for(var i=1;i<=5;i++){
      var cls='rv-star', st='';
      if(shown){ if(i<=shown) cls+=' on'; }
      else if(state.avg){ if(i<=Math.floor(state.avg)) cls+=' on'; else if(i===Math.ceil(state.avg)){ cls+=' part'; st=' style="--p:'+Math.round((state.avg-Math.floor(state.avg))*100)+'%"'; } }
      h += '<span class="'+cls+'" data-r="'+i+'"'+st+' role="radio" aria-label="'+i+'">★</span>';
    }
    h += '</div><div class="rv-meta">';
    h += state.count ? '<span>'+state.avg.toFixed(1)+' · '+state.count+' '+T.n+'</span>' : '<span>'+T.none+'</span>';
    if(state.mine) h += '<span>'+T.yours+': '+state.mine+'</span><button data-clear="1">'+T.clear+'</button>';
    h += '</div>';
    if(noticeAt==='stars') h += noticeHtml();
    return h;
  }
  function ago(iso){
    try{ var d=new Date(iso); return d.toLocaleDateString(en?'en-GB':'he-IL'); }catch(e){ return ''; }
  }
  function commentsHtml(){
    var h = '<h3>'+T.title+'</h3><div class="rv-form"><textarea id="rvText" maxlength="1000" placeholder="'+T.ph+'"></textarea>'+
      '<div class="bar"><select id="rvVis"><option value="0">'+T.priv+'</option><option value="1">'+T.pub+'</option></select>'+
      '<button class="send" id="rvSend">'+T.send+'</button></div>'+(noticeAt==='form'?noticeHtml():'')+'</div>';
    if(!state.comments.length) h += '<div class="rv-empty">'+T.none_c+'</div>';
    state.comments.forEach(function(c){
      var av = c.avatar ? '<img src="'+esc(c.avatar)+'" alt="" referrerpolicy="no-referrer">' : esc((c.name||'?').slice(0,2));
      h += '<div class="rv-c"><div class="rv-av">'+av+'</div><div style="flex:1;min-width:0"><div><span class="who">'+esc(c.name)+'</span>'+
        '<span class="when">'+ago(c.created)+'</span>'+(c.public?'':'<span class="tag">'+T.priv_tag+'</span>')+'</div>'+
        '<div class="txt">'+esc(c.text)+'</div>'+
        (c.mine?'<div class="acts"><button data-vis="'+c.id+'" data-to="'+(c.public?0:1)+'">'+(c.public?T.mk_priv:T.mk_pub)+'</button><button data-del="'+c.id+'">'+T.del+'</button></div>':'')+
        '</div></div>';
    });
    return h;
  }
  function render(){
    var keep = boxEl && document.getElementById('rvText') ? document.getElementById('rvText').value : '';
    var keepVis = boxEl && document.getElementById('rvVis') ? document.getElementById('rvVis').value : '0';
    if(starsEl) starsEl.innerHTML = starsHtml();
    if(boxEl){ boxEl.innerHTML = commentsHtml(); var t=document.getElementById('rvText'); if(t){ t.value=keep; document.getElementById('rvVis').value=keepVis; } }
  }
  function onClick(ev){
    var t = ev.target;
    if(t.closest && t.closest('[data-x]')){ noticeAt=null; render(); return; }
    var s = t.closest && t.closest('.rv-star');
    if(s){ send({action:'rate', rating:+s.getAttribute('data-r')}); return; }
    if(t.closest && t.closest('[data-clear]')){ send({action:'rate', rating:0}); return; }
    var d = t.closest && t.closest('[data-del]'); if(d){ send({action:'delete', comment_id:+d.getAttribute('data-del')}); return; }
    var v = t.closest && t.closest('[data-vis]'); if(v){ send({action:'visibility', comment_id:+v.getAttribute('data-vis'), public:v.getAttribute('data-to')==='1'}); return; }
    if(t.id==='rvSend'){
      var txt = document.getElementById('rvText').value.trim(); if(!txt) return;
      if(!state.signedIn){ noticeAt='form'; render(); return; }
      send({action:'comment', text:txt, public:document.getElementById('rvVis').value==='1'}).then(function(ok){ if(ok){ var x=document.getElementById('rvText'); if(x) x.value=''; } });
    }
  }
  [starsEl, boxEl].forEach(function(el){
    if(!el) return;
    el.addEventListener('click', onClick);
    el.addEventListener('mouseover', function(ev){ var s=ev.target.closest&&ev.target.closest('.rv-star'); if(s&&el===starsEl){ hover=+s.getAttribute('data-r'); var r=starsEl.querySelectorAll('.rv-star'); r.forEach(function(x,i){ x.classList.remove('part'); x.classList.toggle('on', i<hover); }); } });
    el.addEventListener('mouseleave', function(){ if(el===starsEl && hover){ hover=0; render(); } });
  });
  render(); load();
})();
