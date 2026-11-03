"""Pawed short links and bookmarks: the 8-character article id (same hash on the server and in the browser) and the browser script."""
import struct

_M = 0xFFFFFFFF
_B36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def short_id(slug):
    """cyrb53 of the slug (UTF-16 code units, exactly like the JS twin below), folded to 8 base-36 characters."""
    h1, h2 = 0xdeadbeef, 0x41c6ce57
    for ch in struct.unpack("<%dH" % (len(slug.encode("utf-16-le")) // 2), slug.encode("utf-16-le")):
        h1 = ((h1 ^ ch) * 2654435761) & _M
        h2 = ((h2 ^ ch) * 1597334677) & _M
    h1 = ((h1 ^ (h1 >> 16)) * 2246822507) & _M
    h1 ^= ((h2 ^ (h2 >> 13)) * 3266489909) & _M
    h2 = ((h2 ^ (h2 >> 16)) * 2246822507) & _M
    h2 ^= ((h1 ^ (h1 >> 13)) * 3266489909) & _M
    n = (4294967296 * (h2 & 2097151) + h1) % (36 ** 8)
    out = ""
    for _ in range(8):
        n, r = divmod(n, 36)
        out = _B36[r] + out
    return out


BM_JS = r"""(function(){
var RE=/^[0-9a-z]{8}$/,ids=[],signed=false,tmr=null,L={
he:['הוספה לסימניות','הסרה מהסימניות','נוסף לסימניות','הוסר מהסימניות','נשמר במכשיר הזה. התחברו כדי לשמור את הסימניות בחשבון.','הסימניות שלי'],
en:['Bookmark','Remove bookmark','Bookmarked','Bookmark removed','Saved on this device. Sign in to keep your bookmarks in your account.','My Bookmarks']},
lang=window.LANG||document.documentElement.lang||'en',T=L[lang]||L.en;
function sid(s){var h1=0xdeadbeef,h2=0x41c6ce57,i,c;for(i=0;i<s.length;i++){c=s.charCodeAt(i);h1=Math.imul(h1^c,2654435761);h2=Math.imul(h2^c,1597334677);}
h1=Math.imul(h1^(h1>>>16),2246822507);h1^=Math.imul(h2^(h2>>>13),3266489909);h2=Math.imul(h2^(h2>>>16),2246822507);h2^=Math.imul(h1^(h1>>>13),3266489909);
var n=(4294967296*(2097151&h2)+(h1>>>0))%2821109907456;return n.toString(36).padStart(8,'0');}
function ck(){var m=document.cookie.match(/(?:^|;\s*)pawed_bm=([^;]*)/);return m?m[1].split(',').filter(function(x){return RE.test(x)}):[]}
function wck(a){document.cookie='pawed_bm='+a.join(',')+';path=/;max-age=31536000;SameSite=Lax'+(location.protocol==='https:'?';Secure':'')}
function union(a,b){var s={},o=[];a.concat(b).forEach(function(x){if(RE.test(x)&&!s[x]){s[x]=1;o.push(x)}});return o}
function persist(){if(signed){clearTimeout(tmr);tmr=setTimeout(function(){fetch('/api/vidsum/bookmarks',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify({ids:ids})}).catch(function(){})},300)}else wck(ids.slice(-600))}
var st=document.createElement('style');st.textContent='.bmb{position:absolute;top:8px;inset-inline-end:8px;width:32px;height:32px;border-radius:50%;border:0;background:rgba(20,20,20,.55);color:#fff;cursor:pointer;display:grid;place-items:center;padding:0;z-index:3}.bmb:hover{background:rgba(20,20,20,.8)}.bmb.on{background:#e3222b}.bmb svg{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:2;stroke-linejoin:round}.bmb.on svg{fill:currentColor}.bmb.inl{position:static;width:30px;height:30px;background:#fff;color:#555;border:1px solid #d8d8d8}.bmb.inl:hover{color:#e3222b;border-color:#e3222b;background:#fff}.bmb.inl.on{background:#e3222b;color:#fff;border-color:#e3222b}.bmf{display:inline-flex;align-items:center;gap:6px;margin-inline-start:auto;flex:none;align-self:center;background:#e3222b;color:#fff;border-radius:6px 6px 14px 14px;padding:7px 12px 9px;font:700 13px system-ui,sans-serif;text-decoration:none;white-space:nowrap}.bmf svg{width:14px;height:14px;fill:currentColor;stroke:currentColor;stroke-width:2;stroke-linejoin:round}.bmf b{background:#fff;color:#b9141c;border-radius:999px;min-width:20px;padding:0 6px;text-align:center;font-size:12px}.bmf:hover{background:#b9141c}#bmtoast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#222;color:#fff;padding:10px 16px;border-radius:10px;font:14px/1.4 system-ui,sans-serif;max-width:92vw;z-index:99999;display:none;text-align:center}';
document.head.appendChild(st);
var ICON='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4.5L5 21V4a1 1 0 0 1 1-1z"/></svg>';
function toast(m){var t=document.getElementById('bmtoast');if(!t){t=document.createElement('div');t.id='bmtoast';document.body.appendChild(t)}t.textContent=m;t.style.display='block';clearTimeout(t._h);t._h=setTimeout(function(){t.style.display='none'},2600)}
function slugOf(a){var m=(a.getAttribute('href')||'').match(/^\/vidsum\/article\/([^?#]+)/);if(!m)return null;try{return decodeURIComponent(m[1])}catch(e){return m[1]}}
function toggle(id){var i=ids.indexOf(id),on=i<0;if(on)ids.push(id);else ids.splice(i,1);persist();paint();toast(on?T[2]:T[3]);if(on&&!signed&&ids.length===1)setTimeout(function(){toast(T[4])},2800);document.dispatchEvent(new CustomEvent('pawed-bm',{detail:{id:id,on:on}}))}
function mk(id,cls){var b=document.createElement('button');b.type='button';b.className='bmb'+(cls?' '+cls:'');b.setAttribute('data-bm',id);b.innerHTML=ICON;b.onclick=function(e){e.preventDefault();e.stopPropagation();toggle(id)};return b}
function decorate(){
 [].forEach.call(document.querySelectorAll('a.bt,a.cd,a.sm,a.hero2-i,a.rel-card'),function(a){if(a.querySelector(':scope>.bmb'))return;var s=slugOf(a);if(!s)return;if(getComputedStyle(a).position==='static')a.style.position='relative';a.appendChild(mk(sid(s)))});
 var sh=document.querySelector('.share');if(sh&&!sh.querySelector('.bmb')&&/^\/vidsum\/article\//.test(location.pathname)){var s2=decodeURIComponent(location.pathname.split('/').pop());sh.insertBefore(mk(sid(s2),'inl'),sh.firstChild)}
 var nv=document.querySelector('.nav-wrap .nav');if(nv&&!nv.querySelector('.bmf')){var f=document.createElement('a');f.className='bmf';f.href='/vidsum/bookmarks';f.innerHTML=ICON+'<span>'+T[5]+'</span><b>0</b>';nv.appendChild(f)}
 [].forEach.call(document.querySelectorAll('[data-bm-slug]:not([data-bmr])'),function(el){el.setAttribute('data-bmr','1');el.appendChild(mk(sid(el.getAttribute('data-bm-slug')),'inl'))});
}
function paint(){decorate();[].forEach.call(document.querySelectorAll('.bmf b'),function(b){b.textContent=ids.length});[].forEach.call(document.querySelectorAll('.bmb'),function(b){var on=ids.indexOf(b.getAttribute('data-bm'))>=0;b.classList.toggle('on',on);b.title=on?T[1]:T[0];b.setAttribute('aria-label',b.title);b.setAttribute('aria-pressed',String(on))})}
var pend=null;function later(){clearTimeout(pend);pend=setTimeout(paint,80)}
window.pawedBM={sid:sid,ids:function(){return ids.slice()},has:function(id){return ids.indexOf(id)>=0},toggle:toggle,ready:null};
ids=ck();
window.pawedBM.ready=fetch('/api/vidsum/bookmarks',{credentials:'same-origin'}).then(function(r){return r.json()}).then(function(j){
 if(j&&j.signed){signed=true;var c=ck(),m=union(j.ids||[],c);if(c.length||m.length!==(j.ids||[]).length){ids=m;persist();}else ids=m;if(c.length)document.cookie='pawed_bm=;path=/;max-age=0;SameSite=Lax'}
 paint();document.dispatchEvent(new CustomEvent('pawed-bm-ready'))}).catch(function(){paint()});
function start(){paint();new MutationObserver(later).observe(document.body,{childList:true,subtree:true})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
"""
