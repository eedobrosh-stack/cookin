"""Catalog of every error message Pawed is known to log: what it means, how bad it is, who does what next.
Order matters (first match wins). severity: info (expected, self-heals), warn (watch it), crit (someone must act).
Single source of truth: the /vidsum/logs alerts panel (via health_report) and the ~/.claude/skills/pawed-qa agent both read this file."""
import re

KNOWN = [
    # (regex on the log line / queue error, id, severity, meaning, next step, who)
    (r"caption service QUOTA|quota exhausted", "supadata-quota", "crit",
     "Supadata (YouTube captions) plan is used up. The server pauses it 30 min at a time and the Mac covers, slower.",
     "Upgrade or wait for the reset in the Supadata dashboard; nothing to change in code.", "Eedo"),
    (r"Ran out of memory|out of memory", "oom", "crit",
     "The 512 MB instance was killed. Pawed restarts by itself but anything running was lost.",
     "Look at the memory graph (Render > Metrics, 7 days): a baseline above ~400 MB means a leak or too many parallel jobs. Deploy 8ef37a7 lowered the baseline; if it returns, profile article loading and podcast jobs.", "Claude + Eedo"),
    (r"gemini 403|The caller does not have permission", "gemini-video-403", "info",
     "First attempt through Gemini's video path was refused (podcast audio is not a video). The automatic retry succeeds via Gemini audio.",
     "None. Only act if the same episode keeps failing after 3 retries.", "-"),
    (r"Connection reset by peer|Errno 104", "conn-reset", "info",
     "A network drop to LunaRoute or another provider. The job is retried after an hour.",
     "None unless it exceeds ~10 a day (then check the provider's status).", "-"),
    (r"unavailable on YouTube|video not found or private", "yt-unavailable", "info",
     "The video was deleted or made private. It is marked unavailable and not retried.",
     "None.", "-"),
    (r"too little speech|repeats text already|stopped early|MALFORMED|NO_CANDIDATES|window .* (?:retrying|splitting)", "gemini-window-rejected", "info",
     "A Gemini audio window failed the checks (empty, repeated, wrong language, cut off). The window is retried, split, or the Mac takes the episode.",
     "None. If more than a third of server-transcribed podcasts fall to the Mac, review the audio path.", "-"),
    (r"audio larger than", "audio-too-big", "info", "Episode audio is over the 160 MB server limit; the Mac transcribes it.", "None.", "-"),
    (r"This live event will begin|live event", "yt-live-not-started", "info", "A scheduled live stream that has not started. Retried until it has captions.", "None.", "-"),
    (r"Sign in to confirm you.re not a bot", "yt-bot-check", "info",
     "YouTube blocked yt-dlp on the Render server (datacenter addresses are asked to prove they are not bots). Supadata or the Mac get the captions instead.",
     "None. Only a problem if captions also fail through Supadata and the Mac.", "-"),
    (r"gemini file processing failed", "gemini-file-failed", "warn",
     "Gemini's file service could not process the uploaded podcast audio; the episode falls to the Mac (Whisper).",
     "None for a few; if many episodes a day, check the audio size/format and Gemini's status.", "Claude"),
    (r"HTTP Error 5\d\d|Internal Server Error", "provider-5xx", "info", "A provider (Gemini, LunaRoute, Supadata) answered 5xx. The job is retried.", "None unless it lasts hours.", "-"),
    (r"No module named yt_dlp", "no-yt-dlp", "warn", "yt-dlp is not installed in the server's Python, so the server's own caption fallback cannot run.",
     "Check requirements.txt and the Render build log; the Mac still covers.", "Claude"),
    (r"English-first failed", "en-first-failed", "warn",
     "The English-first article path failed and the Hebrew-only writer was used instead, so this article's English is a Hebrew-to-English translation.",
     "Read the line for the reason (usually a LunaRoute JSON error). If it repeats, check the prompt in vidsum_articles._text_prompt_en.", "Claude"),
    (r"vidsum translate .* failed", "translate-failed", "warn", "An English translation failed (not a network reset). It is retried after an hour.",
     "If the same article fails 3 times, read the error in the logs.", "Claude"),
    (r"luna bad JSON|luna FAILED|luna kept returning", "luna-json", "warn", "LunaRoute returned unusable JSON for an article. The job retries.",
     "None for a single occurrence; if several a day, check LunaRoute and the prompt.", "Claude"),
    (r"LunaRoute unavailable|LunaRoute down|Gemini text cap", "luna-down", "warn", "LunaRoute was down; Gemini text wrote the article (capped per day).",
     "Check LunaRoute's status if it lasts more than an hour.", "Eedo"),
    (r"yt-api list failed|yt-api watcher error", "yt-api", "warn", "The YouTube Data API call failed (key, quota or network).",
     "Check the YouTube API quota in Google Cloud if it repeats.", "Eedo"),
    (r"Python version 3\.9 has been deprecated|no metadata", "mac-ytdlp", "warn",
     "The Mac's yt-dlp could not read the video; the real reason is now printed after 'no metadata:'.", "Read the reason; usually a live stream or a private video.", "-"),
    (r"watcher error|loop error|sweep error", "loop-error", "warn", "A background loop raised an exception and continued.", "Read the line; fix if it repeats.", "Claude"),
]

def classify(text):
    for rx, kid, sev, meaning, step, who in KNOWN:
        if re.search(rx, text, re.I):
            return {"id": kid, "severity": sev, "meaning": meaning, "next": step, "who": who}
    return {"id": "unknown", "severity": "warn", "meaning": "A message that is not in the catalog.", "next": "Read it, decide if it is a problem, then add it to known_errors.py.", "who": "Claude"}


def system_alerts(h):
    """Alerts derived from the health numbers themselves (not from log lines): memory, disk, stalled loops, silent Mac. h = health_report dict + 'relay'."""
    out = []
    def add(sev, id_, title, meaning, step, who):
        out.append({"severity": sev, "id": id_, "title": title, "count": 1, "last": h.get("now"), "meaning": meaning, "next": step, "who": who, "source": "system"})
    rss = h.get("rss_mb")
    if rss and rss > 450:
        add("crit", "memory-high", f"Memory {rss} MB of 512", "The instance is close to being killed (out of memory).", "Restart if it keeps rising; read the Render Metrics 7 day graph and check what grew.", "Claude + Eedo")
    elif rss and rss > 380:
        add("warn", "memory-high", f"Memory {rss} MB of 512", "Higher than the ~300 MB baseline.", "Watch it; if it stays up, profile article loading and podcast jobs.", "Claude")
    if (h.get("disk_free_mb") or 1e9) < 300:
        add("crit", "disk-low", f"Only {h['disk_free_mb']} MB of disk left", "Writes will start failing.", "Clear old data on the Render disk.", "Eedo")
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        import time as _t
        now = _t.mktime(_t.strptime(h["now"], fmt))
        yt = (h.get("last") or {}).get("yt_pass")
        if h.get("uptime_min", 0) > 25 and (not yt or (now - _t.mktime(_t.strptime(yt, fmt))) / 60 > 25):
            add("crit", "watcher-stalled", "The YouTube watcher has not run for over 25 minutes", "New YouTube videos are not being discovered by the server.", "Check the Render logs for 'yt-api'; restart the service if needed.", "Claude")
    except Exception:
        pass
    rl = h.get("relay") or {}
    if rl.get("tick_at") and rl.get("now") and (rl["now"] - rl["tick_at"]) / 60 > 15:
        add("crit", "mac-silent", f"The Mac relay has been silent for {int((rl['now'] - rl['tick_at']) / 60)} min", "Long podcasts and caption fallbacks are not being processed.",
            "On the Mac: launchctl list | grep vidsum-relay; if missing, bootstrap com.eedob.vidsum-relay and -rss.", "Eedo")
    return out
