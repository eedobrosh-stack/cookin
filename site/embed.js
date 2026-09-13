/* Cookin — official-player fallback for dishes without a rehosted mp4 (2026-09-13).
   Shared by index.html, en.html and the generated dish pages (../embed.js).
   embedHero(url, poster) → click-to-load box (our thumbnail + ▶). One tap swaps in the
   platform's own iframe player (Facebook video plugin / Instagram / TikTok / YouTube).
   Nothing from Facebook loads until the visitor taps, so the gallery stays fast. */
(function(){
  function embedUrl(u){
    if(!u) return null;
    try{
      const a = new URL(u), h = a.hostname.toLowerCase(), p = a.pathname;
      if(/facebook\.com$|fb\.watch$/.test(h) || h.endsWith(".facebook.com"))
        return "https://www.facebook.com/plugins/video.php?href=" + encodeURIComponent(u) + "&show_text=false&autoplay=true&width=560";
      let m;
      if(h.endsWith("instagram.com") && (m = p.match(/^\/(p|reel|reels|tv)\/([A-Za-z0-9_-]+)/)))
        return "https://www.instagram.com/" + (m[1] === "reels" ? "reel" : m[1]) + "/" + m[2] + "/embed/";
      if(h.endsWith("tiktok.com") && (m = p.match(/\/video\/(\d+)/)))
        return "https://www.tiktok.com/embed/v2/" + m[1];
      if(h === "youtu.be") return "https://www.youtube.com/embed/" + p.split("/")[1] + "?autoplay=1";
      if(h.endsWith("youtube.com")){
        let v = a.searchParams.get("v"); m = p.match(/^\/(shorts|embed|live)\/([A-Za-z0-9_-]{6,})/); if(m) v = m[2];
        if(v) return "https://www.youtube.com/embed/" + v + "?autoplay=1";
      }
    }catch(e){}
    return null;
  }
  function embedHero(url, poster){
    const src = embedUrl(url);
    if(!src) return null;
    return '<div class="embedbox" data-embed="' + src.replace(/"/g, "&quot;") + '" style="background-image:url(\'' + poster + '\')">' +
           '<button type="button" class="embedplay" aria-label="play">▶</button></div>';
  }
  document.addEventListener("click", function(e){
    const box = e.target.closest && e.target.closest(".embedbox");
    if(!box || box.dataset.loaded) return;
    box.dataset.loaded = "1";
    const f = document.createElement("iframe");
    f.src = box.dataset.embed; f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
    f.setAttribute("allowfullscreen", ""); f.setAttribute("scrolling", "no");
    box.innerHTML = ""; box.appendChild(f); box.classList.add("loaded");
  });
  const css = document.createElement("style");
  css.textContent =
    ".embedbox{position:relative;width:100%;aspect-ratio:9/16;max-height:560px;background:#111 center/contain no-repeat;display:flex;align-items:center;justify-content:center;cursor:pointer;overflow:hidden}" +
    ".embedbox.loaded{cursor:default}" +
    ".embedbox iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:#111}" +
    ".embedplay{width:74px;height:74px;border-radius:50%;border:0;background:rgba(224,122,63,.94);color:#fff;font-size:30px;padding-inline-start:6px;box-shadow:0 6px 24px rgba(0,0,0,.35);cursor:pointer;transition:transform .15s}" +
    ".embedbox:hover .embedplay{transform:scale(1.08)}" +
    "body.dishmode .embedbox{height:100%;max-height:none;aspect-ratio:auto}";
  document.head.appendChild(css);
  window.embedUrl = embedUrl; window.embedHero = embedHero;
})();
