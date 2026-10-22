"""Podcast transcription on the server: Gemini listens to the episode audio (no Mac needed).

A podcast episode waiting for a transcript (job status needs_transcript, kind rss) is downloaded from its public RSS enclosure, sent to
Gemini (Files API) and the timed text goes to the article writer exactly like the Mac's Whisper output would. The Mac stays as the
fallback for what this path skips or cannot do: episodes over MAX_MIN, the daily cap, any Gemini error.
"""
import os, re, tempfile, threading, time

import multiuser
import stt_test as st
import vidsum_articles as va

MAX_MIN = int(os.environ.get("VIDSUM_PODCAST_MAX_MIN", "60"))              # longer episodes stay with the Mac (one Gemini answer must fit)
DAILY_CAP = int(os.environ.get("VIDSUM_GEMINI_PODCAST_DAILY_CAP", "20"))   # episodes per day
_ONE = threading.Semaphore(1)


def _today_count():
    today = time.strftime("%Y-%m-%d")
    return sum(1 for j in va._load_jobs().values() if (j.get("gemini_stt") or "").startswith(today))


def hebrew_share(s):
    letters = [c for c in (s or "") if c.isalpha()]
    return sum(1 for c in letters if "֐" <= c <= "׿") / len(letters) if letters else 0


def episode_language(job):
    """what the episode is spoken in: the title/description say it better than the feed's language tag (which can be wrong)"""
    he = hebrew_share((job.get("title") or "") + " " + (job.get("description") or "")[:400])
    return "Hebrew" if he > 0.3 else ("English" if job.get("language") in ("en", "other") or he < 0.05 else "Hebrew")


def _prompt(lang):
    return (f"Transcribe this {lang} podcast episode word for word, in {lang}, with nothing summarised and nothing left out. Start a new line "
            "every ~30 seconds with the elapsed time in the form [m:ss] (or [h:mm:ss] after an hour), then the speech of that stretch. "
            "No speaker names, no comments, no music or sound notes.")


def _normalise(text):
    """Gemini's '[00:24] ...' lines -> the '[m:ss] ...' blocks the article writer expects; blocks with no speech are dropped"""
    out = []
    for sec, t in st._blocks(text):
        t = re.sub(r"\[[^\]]{0,40}\]", " ", t).strip()                    # [מוזיקה] / [music] markers
        if len(t) >= 20:
            out.append(f"[{_fmt(sec)}] {t}")
    return "\n".join(out)


def _fmt(sec):
    h, r = divmod(int(sec), 3600)
    return f"{h}:{r // 60:02d}:{r % 60:02d}" if h else f"{r // 60}:{r % 60:02d}"


def transcribe(vid, job):
    """-> dict for relay_transcript. Raises on any failure (the caller leaves the job to the Mac)."""
    key = (multiuser.secret("GEMINI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")
    lang = episode_language(job)
    tmp = tempfile.mkdtemp(prefix="pstt_")
    path = os.path.join(tmp, "a.mp3")
    try:
        _size, mime = st._download(job["audio"], path)
        info = st._with_retry(st._upload, path, mime, key)
        with va.tok_ctx("podcast-stt", vid, va._job_owner(vid)):
            text, um, fin = st._with_retry(st._generate, info, key, _prompt(lang))
        va._tok_log(multiuser.GEMINI_MODEL, um.get("promptTokenCount", 0), (um.get("candidatesTokenCount") or 0) + (um.get("thoughtsTokenCount") or 0))
        if fin not in ("STOP", None):
            raise RuntimeError(f"Gemini stopped early ({fin})")
        transcript = _normalise(text)
        dur_min = (job.get("duration") or 0) / 60
        if len(transcript) < max(400, int(250 * dur_min)) or len(transcript.splitlines()) < 3:      # real speech runs ~500-900 characters a minute
            raise RuntimeError("Gemini returned too little speech")
        if lang == "Hebrew" and hebrew_share(transcript) < 0.5:
            raise RuntimeError("Gemini transcript is not Hebrew")
        last = st._blocks(transcript)[-1][0] if st._blocks(transcript) else 0
        return {"transcript": transcript, "duration": job.get("duration") or last, "published_at": job.get("published_at"),
                "published": (job.get("published_at") or "")[:10] or None, "title": job.get("title") or "", "channel": job.get("channel") or "",
                "description": (job.get("description") or "")[:3000], "source": "gemini-audio"}
    finally:
        try:
            os.remove(path)
            os.rmdir(tmp)
        except OSError:
            pass


def once():
    """Take at most one waiting podcast episode, newest-added sources first. Returns True if one was attempted."""
    if not (multiuser.secret("GEMINI_API_KEY") or "").strip() or _today_count() >= DAILY_CAP:
        return False
    pick = None
    with va.LOCK:
        jobs = va._load_jobs()
        for vid, _row in [(r["vid"], r) for r in va.relay_queue(40, for_mac=False) if r.get("kind") == "rss"]:
            j = jobs.get(vid) or {}
            if not j.get("audio"):
                continue
            d = j.get("duration") or 0
            if d and d > MAX_MIN * 60:
                continue
            if time.time() < j.get("gstt_next", 0):
                continue
            j["srv_claim"] = time.time() + 480           # keeps the Mac away for ~12 minutes (relay_queue hides claims younger than 240 s)
            j["gemini_stt"] = time.strftime("%Y-%m-%d %H:%M:%S")
            pick = (vid, dict(j))
            break
        if pick:
            va._save_jobs(jobs)
    if not pick:
        return False
    vid, job = pick
    with _ONE:
        try:
            va._event(vid, "fetching", "Gemini audio transcription", job)
            req = transcribe(vid, job)
            va.relay_transcript({"vid": vid, **req})
        except Exception as e:
            va.log(f"vidsum podcast stt {vid} failed, leaving it to the Mac: {va._scrub(str(e))[:200]}")
            va._set_job(vid, srv_claim=0, gemini_stt="", gstt_next=time.time() + 1800)
    return True


def loop():
    time.sleep(120)
    while True:
        busy = False
        try:
            busy = once()
        except Exception as e:
            va.log(f"vidsum podcast stt loop error: {str(e)[:200]}")
        time.sleep(15 if busy else 60)
