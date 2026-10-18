/* "Add an episode" pop-up shared by every Pawed page: submits one YouTube URL as a standalone episode to the signed-in user's (or admin's) queue. */
(function(){
  var css=document.createElement('style');
  css.textContent='#aep-ov{position:fixed;inset:0;background:rgba(20,15,10,.55);z-index:300;display:flex;align-items:center;justify-content:center;padding:16px}'
   +'#aep{background:#fff;color:#17171a;border-radius:14px;max-width:460px;width:100%;padding:22px 22px 18px;box-shadow:0 18px 60px rgba(0,0,0,.35);font-family:inherit;direction:rtl;text-align:right;position:relative}'
   +'#aep h3{margin:0 0 4px;font-size:21px;color:#17171a}#aep p{margin:0 0 14px;color:#666;font-size:14px;line-height:1.45}'
   +'#aep input{width:100%;box-sizing:border-box;font:inherit;font-size:15px;padding:11px 12px;border:1px solid #cfcfcf;border-radius:8px;direction:ltr;text-align:left}'
   +'#aep input:focus{outline:2px solid #e3222b;border-color:#e3222b}'
   +'#aep .row{display:flex;gap:10px;margin-top:12px;align-items:center}'
   +'#aep button.go{background:#e3222b;color:#fff;border:0;border-radius:999px;padding:10px 22px;font-weight:800;font-size:15px;cursor:pointer}#aep button.go:disabled{opacity:.5;cursor:default}'
   +'#aep .x{position:absolute;top:8px;left:12px;border:0;background:none;font-size:24px;color:#888;cursor:pointer}'
   +'#aep .msg{margin-top:12px;font-size:14px;line-height:1.45;min-height:20px}#aep .msg.ok{color:#18723a}#aep .msg.err{color:#b9141c}#aep .msg a{color:#1556d6;text-decoration:underline}';
  document.head.appendChild(css);
  function close(){ var o=document.getElementById('aep-ov'); if(o) o.remove(); }
  function open(e){
    if(e) e.preventDefault();
    close();
    var o=document.createElement('div'); o.id='aep-ov';
    o.innerHTML='<div id="aep" role="dialog" aria-modal="true"><button class="x" aria-label="close">×</button>'
      +'<h3>הוספת פרק · Add an episode</h3>'
      +'<p>הדביקו קישור YouTube לפרק בודד והוא יתווסף לתור הסיכומים שלכם.<br><span dir="ltr">Paste a YouTube link to a single episode and it joins your queue.</span></p>'
      +'<input type="text" id="aep-url" dir="ltr" placeholder="https://www.youtube.com/watch?v=..." autocomplete="off">'
      +'<div class="row"><button class="go" id="aep-go">הוספה לתור · Add to queue</button></div><div class="msg" id="aep-msg"></div></div>';
    document.body.appendChild(o);
    var inp=document.getElementById('aep-url'), go=document.getElementById('aep-go'), msg=document.getElementById('aep-msg');
    inp.focus();
    o.addEventListener('click',function(ev){ if(ev.target===o||ev.target.className==='x') close(); });
    document.addEventListener('keydown',function esc(ev){ if(ev.key==='Escape'){ close(); document.removeEventListener('keydown',esc); } });
    function say(t,c,html){ msg.className='msg '+(c||''); if(html) msg.innerHTML=t; else msg.textContent=t; }
    async function submit(){
      var url=inp.value.trim(); if(!url){ say('יש להדביק קישור YouTube · Paste a YouTube link','err'); return; }
      go.disabled=true; say('שולח… · Sending…');
      try{
        var r=await fetch('/api/vidsum/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:url})});
        var j=await r.json().catch(function(){return {ok:false,error:'error'};});
        if(r.status===401){ say('יש להתחבר קודם · Please sign in first','err'); }
        else if(!j.ok){ say(({'not a YouTube link':'זה לא קישור YouTube · That is not a YouTube link'})[j.error]||j.error||'שגיאה · Error','err'); }
        else if(j.existing){ say('הפרק כבר קיים ב-Pawed · Already on Pawed: <a href="/vidsum/article/'+encodeURIComponent(j.slug)+'">open the article</a>','ok',true); }
        else if(j.status==='done'){ say('הפרק כבר מסוכם · Already summarized','ok'); }
        else { say('✓ נוסף לתור! הכתבה תופיע בפורטל ברגע שתהיה מוכנה. · Added to the queue! The article appears on the portal when it is ready.','ok'); inp.value=''; }
      }catch(e){ say('שגיאת רשת · Network error','err'); }
      go.disabled=false;
    }
    go.onclick=submit; inp.addEventListener('keydown',function(ev){ if(ev.key==='Enter') submit(); });
  }
  document.addEventListener('click',function(e){ var a=e.target.closest&&e.target.closest('#addep'); if(a) open(e); });
})();
