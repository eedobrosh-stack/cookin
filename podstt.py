"""Podcast transcription on the server: Gemini listens to the episode audio (no Mac needed).

A podcast episode waiting for a transcript (job status needs_transcript, kind rss) is downloaded from its public RSS enclosure, sent to
Gemini (Files API) and the timed text goes to the article writer exactly like the Mac's Whisper output would. The Mac stays as the
fallback for what this path skips or cannot do: episodes over MAX_MIN, the daily cap, any Gemini error.
"""
import os, re, tempfile, threading, time

import multiuser
import stt_test as st
import vidsum_articles as va

MAX_MIN = va.SERVER_PODCAST_MAX_MIN                                        # episodes longer than this stay with the Mac (Gemini audio proved unreliable on long files)
REPEAT_MAX = 0.10                                                          # more of a window than this repeating earlier windows = Gemini re-told an old stretch
WINDOW_MIN = 30                                                            # one Gemini answer covers ~30 minutes of speech; longer episodes are done in windows
DAILY_MINUTES = int(os.environ.get("VIDSUM_PODCAST_MIN_PER_DAY", "600"))   # audio minutes sent to Gemini per day (about 10 hours)
_ONE = threading.Semaphore(1)


def _today_minutes():
    today = time.strftime("%Y-%m-%d")
    return sum((j.get("duration") or 2400) / 60 for j in va._load_jobs().values() if (j.get("gemini_stt") or "").startswith(today))


def hebrew_share(s):
    letters = [c for c in (s or "") if c.isalpha()]
    return sum(1 for c in letters if "֐" <= c <= "׿") / len(letters) if letters else 0


def episode_language(job):
    """what the episode is spoken in: the title/description say it better than the feed's language tag (which can be wrong)"""
    he = hebrew_share((job.get("title") or "") + " " + (job.get("description") or "")[:400])
    return "Hebrew" if he > 0.3 else ("English" if job.get("language") in ("en", "other") or he < 0.05 else "Hebrew")


def _prompt(lang, a=None, b=None):
    part = (f" Transcribe ONLY the part from {_fmt(a)} to {_fmt(b)} of the recording (elapsed time from the very start of the file; start exactly "
            f"at {_fmt(a)}, stop at {_fmt(b)}, and keep the original elapsed times in the timestamps)." if a is not None else "")
    return (f"Transcribe this {lang} podcast episode word for word, in {lang}, with nothing summarised and nothing left out.{part} Start a new line "
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


DEBUG_PARTS = []                                                           # (from, to, verdict, text) of every window answer of the last transcribe() call, for stt-compare


def _shingles(text, n=6):
    w = re.findall(r"[\w']+", re.sub(r"\[[^\]]{0,12}\]", " ", text or ""))
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def _repeat_share(piece, prior):
    """share of this window's 6-word runs that already appear in the windows accepted before it (a real conversation barely repeats
    itself; a Gemini answer that re-tells an earlier stretch does)"""
    mine = _shingles(piece)
    if not mine or not prior:
        return 0.0
    old = set()
    for x in prior:
        old |= _shingles(x)
    return len(mine & old) / len(mine)


def _check_window(piece, lang, a, b, prior=None):
    """content check of one window's answer -> None if it looks like the right stretch, else the reason. Gemini can answer STOP with
    text from the wrong part of the file (or invented text), so the finish reason alone is not proof."""
    if a is None:
        return None
    blocks = st._blocks(piece)
    if not blocks:
        return "no timestamped blocks"
    if lang == "Hebrew" and hebrew_share(piece) < 0.5:
        return "not Hebrew"
    inside = sum(1 for sec, _t in blocks if a - 60 <= sec <= b + 60)
    if inside < 0.8 * len(blocks):
        return f"timestamps outside the window ({inside}/{len(blocks)} inside)"
    if blocks[-1][0] < a + 0.6 * (b - a):
        return f"speech ends at {_fmt(blocks[-1][0])}, well before {_fmt(b)}"
    rep = _repeat_share(piece, prior)
    if rep > REPEAT_MAX:
        return f"{int(rep * 100)}% of it repeats text already transcribed"
    return None


def _window(info, key, lang, a, b, dur, depth=0, retried=False, prior=None):
    prior = [] if prior is None else prior                                 # pieces accepted so far, in order (filled by the call that accepts them)
    """one window of the episode -> list of normalised pieces. A window that stops early (output limit, malformed or empty answer), returns too
    little speech or fails the content check is asked once more, then split in half and both halves are done separately."""
    if a is None and dur:
        a, b = 0, dur
    text, um, fin = st._with_retry(st._generate, info, key, _prompt(lang, a, b))
    va._tok_log(multiuser.GEMINI_MODEL, um.get("promptTokenCount", 0), (um.get("candidatesTokenCount") or 0) + (um.get("thoughtsTokenCount") or 0))
    piece = _normalise(text)
    span_min = ((b - a) / 60) if a is not None else (dur / 60)
    bad = None
    if fin not in ("STOP", None):
        bad = f"stopped early ({fin})"
    elif len(piece) < max(300, int(200 * span_min)) or len(piece.splitlines()) < 2:                  # real speech runs ~500-900 characters a minute
        bad = "too little speech"
    else:
        bad = _check_window(piece, lang, a, b, prior)
    DEBUG_PARTS.append((a, b, bad or "ok", piece or text))
    if not bad:
        prior.append(piece)
        return [piece]
    where = f"{_fmt(a or 0)}-{_fmt(b or dur)}"
    if not retried:
        va.log(f"vidsum podcast stt: window {where} {bad}, retrying")
        return _window(info, key, lang, a, b, dur, depth, True, prior)
    if a is not None and (b - a) > 600 and depth < 3:
        mid = (a + b) // 2
        va.log(f"vidsum podcast stt: window {where} {bad} again, splitting")
        return (_window(info, key, lang, a, mid, dur, depth + 1, False, prior)
                + _window(info, key, lang, mid, b, dur, depth + 1, False, prior))
    raise RuntimeError(f"Gemini window {where}: {bad}")


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
        dur = int(job.get("duration") or 0)
        windows = [(None, None)] if dur <= (WINDOW_MIN + 10) * 60 else [(a, min(dur, a + WINDOW_MIN * 60)) for a in range(0, dur, WINDOW_MIN * 60)]
        parts = []
        del DEBUG_PARTS[:]
        prior = []
        with va.tok_ctx("podcast-stt", vid, va._job_owner(vid)):
            for a, b in windows:
                parts += _window(info, key, lang, a, b, dur, prior=prior)
        transcript = "\n".join(parts)
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
    if not (multiuser.secret("GEMINI_API_KEY") or "").strip() or _today_minutes() >= DAILY_MINUTES:
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
