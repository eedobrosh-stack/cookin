"""Catalog of every error message Pawed is known to log: what it means, how bad it is, who does what next.
Order matters (first match wins). severity: info (expected, self-heals), warn (watch it), crit (someone must act).
Single source of truth: the /vidsum/logs alerts panel (via health_report) and the ~/.claude/skills/pawed-qa agent both read this file."""
import re

KNOWN = [
    # (regex on the log line / queue error, id, severity, meaning, next step, who)
    (r"caption service QUOTA|quota exhausted", "supadata-quota", "crit",
     "Supadata (YouTube captions) plan is used up. The server pauses it 30 min at a time and the Mac covers, slower.",
     "Upgrade or wait for the reset in the Supadata dashboard; nothing to change in code.", "Eedo"),
    (r"vidsum rss: .+ -> ", "rss-new-episode", "info", "Log line, not an error: a new podcast episode was found on its feed and queued.", "None.", "-"),
    (r" DONE slug=", "article-done", "info", "Log line, not an error: an article finished.", "None.", "-"),
    (r"podcast stt .* failed, leaving it to the Mac", "stt-to-mac", "info",
     "Server transcription of a podcast failed (usually the audio URL returned 404 or timed out); the Mac relay takes the episode.",
     "None unless more than a third of server-transcribed podcasts fall to the Mac, then review the audio path.", "-"),
    (r"Ran out of memory|out of memory", "oom", "crit",
     "The instance ran out of memory and was killed. Pawed restarts by itself but anything running was lost.",
     "Look at the memory graph (Render > Metrics, 7 days): a baseline above ~65% of the cap means a leak or too many parallel jobs. Deploy 8ef37a7 lowered the baseline; if it returns, profile article loading and podcast jobs.", "Claude + Eedo"),
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
     "Only surfaced at 10 or more fallbacks in the log window (or when the daily Gemini cap is used up); check LunaRoute's status then.", "Eedo"),
    (r"yt-api list failed|yt-api watcher error", "yt-api", "warn", "The YouTube Data API call failed (key, quota or network).",
     "Check the YouTube API quota in Google Cloud if it repeats.", "Eedo"),
    (r"Python version 3\.9 has been deprecated|no metadata", "mac-ytdlp", "warn",
     "The Mac's yt-dlp could not read the video; the real reason is now printed after 'no metadata:'.", "Read the reason; usually a live stream or a private video.", "-"),
    (r"watcher error|loop error|sweep error", "loop-error", "warn", "A background loop raised an exception and continued.", "Read the line; fix if it repeats.", "Claude"),
]

# Three tiers. decision = only Eedo can change it, and there is a real tradeoff (options below);
# handled = Claude investigates and fixes, Eedo only gets a one-line note; auto = expected, self-heals, counted not listed.
# Options are [what you would do, what it costs / what you give up].
DECISIONS = {
    "supadata-quota": [["Upgrade the Supadata plan", "Costs money per month; server fetches YouTube captions fast again."],
                       ["Wait for the quota reset", "Free; the Mac relay covers captions, slower and only while the Mac is awake."],
                       ["Reduce YouTube sources", "Free; fewer new articles but the quota lasts longer."]],
    "oom": [["Raise the Render plan again", "Costs money; the cleanest cure if the baseline keeps growing."],
            ["Cap parallel podcast and translation jobs", "Free; slower throughput, fewer articles per hour."],
            ["Have Claude profile article loading", "Free; takes a session and may find nothing."]],
    "memory-high": [["Raise the Render plan", "Costs money; removes the pressure at once."],
                    ["Cap parallel jobs", "Free; slower throughput."],
                    ["Have Claude profile what grew", "Free; takes a session."]],
    "disk-low": [["Enlarge the Render disk", "Costs money; keeps everything."],
                 ["Let Claude prune old data (logs, caches, old audio)", "Free; old material is gone for good."]],
    "mac-silent": [["Restart the relay on the Mac (launchctl bootstrap com.eedob.vidsum-relay and -rss)", "Free, one minute; long podcasts resume."],
                   ["Leave it", "Free; the server only handles short videos and podcast summaries stall."]],
    "watcher-stalled": [["Restart the Render service", "Free, one minute; running jobs are lost and retried."],
                        ["Wait one more cycle", "Free; new YouTube videos are delayed meanwhile."]],
    "luna-down": [["Wait for LunaRoute", "Free; articles are delayed."],
                  ["Let Gemini text cover (capped per day)", "Costs a little Gemini spend; articles keep flowing, slightly different style."]],
    "yt-api": [["Raise the YouTube Data API quota or replace the key in Google Cloud", "Free to small cost; new videos are found again."],
               ["Leave it", "Free; discovery falls back to slower paths."]],
}


LUNA_DOWN_MIN = 10   # LunaRoute fallbacks in the log window before it is worth a decision


def tier_of(kid, severity):
    if severity == "info":
        return "auto"
    if kid == "memory-high" and severity == "warn":
        return "handled"                  # a slow rise is Claude's to profile; only a critical level needs a spending decision
    return "decision" if kid in DECISIONS else "handled"


def decorate(a):
    """Add tier and options to an alert dict that has id + severity."""
    a["tier"] = tier_of(a["id"], a["severity"])
    if a["id"] == "luna-down" and a["tier"] == "decision" and (a.get("count") or 0) < LUNA_DOWN_MIN and "cap" not in (a.get("title") or ""):
        a["tier"] = "auto"                # a few drops fall back to Gemini on their own; only a sustained outage or an exhausted cap needs a decision
    a["options"] = DECISIONS.get(a["id"], []) if a["tier"] == "decision" else []
    return a


def classify(text):
    for rx, kid, sev, meaning, step, who in KNOWN:
        if re.search(rx, text, re.I):
            return {"id": kid, "severity": sev, "meaning": meaning, "next": step, "who": who}
    return {"id": "unknown", "severity": "warn", "meaning": "A message that is not in the catalog.", "next": "Read it, decide if it is a problem, then add it to known_errors.py.", "who": "Claude"}


def mem_limit_mb():
    """The instance's real memory cap: the container's cgroup limit (v2, then v1), else PAWED_MEM_MB, else 2048 (the plan since 2026-11)."""
    import os
    for f in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            v = open(f).read().strip()
            if v.isdigit() and 256 * 2**20 <= int(v) < 2**40:
                return int(v) // 2**20
        except OSError:
            pass
    try:
        return int(os.environ.get("PAWED_MEM_MB") or 2048)
    except ValueError:
        return 2048


def system_alerts(h):
    """Alerts derived from the health numbers themselves (not from log lines): memory, disk, stalled loops, silent Mac. h = health_report dict + 'relay'."""
    out = []
    def add(sev, id_, title, meaning, step, who):
        out.append({"severity": sev, "id": id_, "title": title, "count": 1, "last": h.get("now"), "meaning": meaning, "next": step, "who": who, "source": "system"})
    rss = h.get("rss_mb")
    cap = mem_limit_mb()
    if rss and rss > cap * 0.85:
        add("crit", "memory-high", f"Memory {rss} MB of {cap}", "The instance is close to being killed (out of memory).", "Restart if it keeps rising; read the Render Metrics 7 day graph and check what grew.", "Claude + Eedo")
    elif rss and rss > cap * 0.65:
        add("warn", "memory-high", f"Memory {rss} MB of {cap}", "Well above the ~300 MB baseline, so something is growing.", "Watch it; if it stays up, profile article loading and podcast jobs.", "Claude")
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
