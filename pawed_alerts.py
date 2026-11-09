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
    (r"gemini 402|HTTP Error 402|Payment Required|\b402\b.{0,40}(?:billing|payment)", "provider-402", "crit",
     "A paid provider (Gemini, or LunaRoute) answered 402 Payment Required: the account has no credit or hit its spending cap, so every call to it fails.",
     "Top up or raise the cap on the provider's billing page; then retry the stuck jobs.", "Eedo"),
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
    (r"index (?:entities|keywords|process)", "index-extract-failed", "warn",
     "The Index could not extract people / companies from an article (LunaRoute busy with 429, or an empty / invalid reply). The article is retried in 20 minutes.",
     "None for a few; if it stays at hundreds for hours, check LunaRoute and the extraction prompt in pawed_index.py.", "Claude"),
    (r"vidsum headlines batch failed", "headlines-failed", "warn",
     "A batch of headline translations (titles + leads in all languages) failed (LunaRoute busy or an invalid reply). Its articles are retried in an hour.",
     "None for a few; a long streak means non-Hebrew users keep seeing English headlines on older articles.", "Claude"),
    (r"vidsum_channels\.json|refusing to treat it as empty", "registry-error", "crit",
     "The source registry file (vidsum_channels.json) could not be written or read. If it was saved empty, nothing new is discovered and the site looks fine because old articles stay (this is how 2026-11-07 15:44 UTC silently stopped Pawed).",
     "Check the source count in health (sources); if it is 0 or dropped, restore from the rebuild roster via POST /api/vidsum/channels/restore.", "Claude"),
    (r"watcher error|loop error|sweep error", "loop-error", "warn", "A background loop raised an exception and continued.", "Read the line; fix if it repeats.", "Claude"),
]

# Three tiers. decision = only Eedo can change it, and there is a real tradeoff (options below);
# handled = Claude investigates and fixes, Eedo only gets a one-line note; auto = expected, self-heals, counted not listed.
# Options are [what you would do, what it costs / what you give up].
DECISIONS = {
    "provider-402": [["Top up / raise the spending cap on the Gemini (and LunaRoute) billing page", "Costs money (Gemini audio is roughly 740K input + 170K output tokens per 99-minute episode); transcription, scoring and fallbacks work again within minutes."],
                     ["Leave it unpaid", "Free; podcast transcription, candidate scoring and Gemini fallbacks stay down, and the Mac relay is the only transcript path (slow, only while the Mac is awake)."]],
    "no-sources": [["Restore the roster now (Claude runs the restore endpoint)", "Free; discovery resumes in minutes, per-source settings that were lost stay lost."],
                   ["Restore from a Render disk snapshot", "Free but you do it in the dashboard; exact registry, but articles written since the snapshot are lost."]],
    "sources-dropped": [["Have Claude find and re-add the missing sources", "Free; takes a session, exact settings may be lost."],
                        ["Accept the smaller roster", "Free; fewer new episodes per day (see the gauge's expected rate)."]],
    "no-new-articles": [["Have Claude trace the stall (sources, watchers, billing, queue)", "Free; takes a session."],
                        ["Wait one more cycle", "Free; articles stay delayed meanwhile and the backlog grows."]],
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


IMPACT = {
    "headlines-failed": "Older articles keep English (or Hebrew) titles in the other six languages until a batch succeeds; the full text is still written when someone opens the article.",
    "index-extract-failed": "Those articles stay out of the Index's people and companies lists (their keywords, podcast and episode entries still work). A long streak means the Index stays thin and LunaRoute capacity is wasted on retries.",
    "provider-402": "Every Gemini call fails: podcast transcription (up to 600 audio minutes a day normally), YouTube video fallback (10/day), candidate scoring and the Gemini article fallback stop. Episodes pile up in 'needs transcript' and the gauge's actual needle falls toward 0; nothing is billed while it is down, but backlog and delay grow every hour.",
    "supadata-quota": "YouTube videos cannot get captions from the server, so they wait in 'needs transcript' (the Mac relay covers only while it is awake). Expect a growing YouTube backlog and fewer articles per day.",
    "oom": "The server was killed and restarted: every running job (article writing, translation, uploads) is lost and retried, and pawed.io, Cookin and Jarcud are down for a minute or more. Repeats mean a leak and a restart loop.",
    "memory-high": "Memory near the cap risks an out-of-memory kill (see oom): lost running jobs and short downtime for all sites on this service.",
    "disk-low": "When the disk fills, writes fail: new articles, the source registry, logs and uploads stop saving, and data can be corrupted.",
    "mac-silent": "Long podcasts and caption fallbacks that need the Mac stop, so those episodes sit in the queue until the Mac is back. Short YouTube videos still work.",
    "watcher-stalled": "No new YouTube videos are discovered by the server; the feed goes stale without any error being shown.",
    "no-sources": "The watchers have nothing to watch, so no new episode will ever arrive. The site still looks alive because old articles stay, which is exactly how the 7 Nov outage went unnoticed.",
    "sources-dropped": "Part of the roster is gone, so the expected episodes per day fall and whole shows silently stop appearing.",
    "no-new-articles": "Nothing has been published for many hours: a stalled pipeline (empty roster, blocked billing, a dead watcher) that raises no error of its own. Readers see a frozen homepage.",
    "registry-error": "The source list (vidsum_channels.json) failed to save or load. If it was saved empty, all discovery stops silently (see no-sources); if only logged, the risk is a lost source edit.",
    "loop-error": "One background loop hit an exception and carried on. A single occurrence is harmless; a repeating one means that job (discovery, translation, RSS) is quietly not doing its work.",
    "luna-down": "Articles are written by the Gemini text fallback instead of LunaRoute: extra Gemini spend (up to the 30/day cap) and a slightly different writing style; if the cap runs out, articles queue up.",
    "luna-json": "LunaRoute returned unusable output, so that article retries later: a delayed article, and repeated failures add LunaRoute and Gemini cost for the same episode.",
    "translate-failed": "That article stays Hebrew-only (no English or other-language edition) until the hourly retry works; many failures mean non-Hebrew visitors see a thinner site.",
    "en-first-failed": "The English edition of that article is a translation from Hebrew, not written from the original, so it reads worse; no outage.",
    "yt-api": "The server cannot list new videos through the YouTube Data API, so YouTube discovery degrades to slower paths and new videos appear late.",
    "gemini-file-failed": "That podcast falls to the Mac (Whisper) instead of Gemini: slower, and only while the Mac is awake. A few a day is normal; many means Gemini audio is broken.",
    "gemini-window-rejected": "A transcript window was rejected and retried or split: extra Gemini audio tokens (cost) for the same episode; many of them push episodes to the Mac.",
    "stt-to-mac": "Server transcription failed and the Mac takes the episode: slower, and it waits if the Mac is asleep.",
    "audio-too-big": "Episodes over 160 MB are never transcribed by the server, so they wait for the Mac.",
    "yt-bot-check": "YouTube blocked the server's own downloader; captions come from Supadata or the Mac instead, so only a problem if both fail too.",
    "yt-unavailable": "A deleted or private video; it is marked unavailable and dropped. No effect.",
    "yt-live-not-started": "A scheduled live stream with no captions yet; retried until it has them. No effect.",
    "mac-ytdlp": "The Mac's caption fallback could not read one video; that episode waits or fails.",
    "gemini-video-403": "The first Gemini attempt on a podcast was refused and the automatic audio retry succeeds: one wasted call, no lasting effect.",
    "conn-reset": "A network drop to a provider; the job retries in an hour. Only a delay, unless it happens constantly.",
    "provider-5xx": "A provider had a temporary server error; the job retries. Only a delay, unless it lasts hours.",
    "no-yt-dlp": "The server cannot run its own caption fallback, so those videos fall to Supadata or the Mac.",
    "rss-new-episode": "Not an error: a new podcast episode was found and queued.",
    "article-done": "Not an error: an article was published.",
    "unknown": "Unknown. This message is not in the catalog, so its effect on episodes, queue or cost is not known until someone reads it.",
}
PROMPT_HINT = {
    "provider-402": "Check which provider returns 402 (Gemini API key vs LunaRoute) from the log lines, how many jobs and how many Gemini minutes/tokens are stuck, and tell me exactly which billing page to open and what to top up.",
    "no-sources": "Check /api/vidsum/channels, restore the roster from the rebuild roster (POST /api/vidsum/channels/restore, scratchpad roster.json or rebuild it from articles), then explain what wiped it.",
    "sources-dropped": "Compare the current roster with the high-water mark and the articles' source_ids, find which sources vanished and why, and propose how to restore them.",
    "no-new-articles": "Trace the stall in order: source count, YouTube and RSS watchers (health last.*), queue states in /api/vidsum/logs, billing (402s), LunaRoute. Say which link is broken.",
    "registry-error": "Check whether vidsum_channels.json is intact now (source count) and whether the save/load race fix is live; say if anything is still unsafe.",
    "memory-high": "Profile what grew (article index, podcast jobs, translation) from health and the Render metrics, and propose the cheapest cure.",
}


def impact_of(a):
    return IMPACT.get(a.get("id")) or IMPACT["unknown"]


def prompt_of(a):
    """The text to paste back to Claude to start working on this alert."""
    hint = PROMPT_HINT.get(a.get("id"), "Investigate the cause in the code and logs, tell me what it affects (queue, cost, missing articles), and propose options with their costs.")
    ex = (a.get("example") or "").strip()
    return ("Investigate this Pawed alert (admin ERR page).\n"
            f"Alert: {a.get('title')}\nId: {a.get('id')} | severity: {a.get('severity')} | seen: {a.get('count') or 1}x, first {a.get('first') or a.get('last') or '?'}, last {a.get('last') or '?'}\n"
            + (f"Example log line: {ex[:400]}\n" if ex else "")
            + f"What it means: {a.get('meaning')}\nWhat it could imply: {impact_of(a)}\n"
            f"Task: {hint} Use the /pawed-qa skill for the live health and logs (read-only first). Do not deploy, push or spend money without asking me.")


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
    a["impact"] = impact_of(a)
    a["prompt"] = prompt_of(a)
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
    n_src, hwm = h.get("sources"), h.get("sources_hwm") or 0
    if n_src is not None and h.get("uptime_min", 0) > 2:
        if n_src == 0:
            add("crit", "no-sources", "The source registry is EMPTY", "No shows are being watched, so no new episodes will ever arrive. Old articles still show, so the site looks alive.",
                "Restore the roster (POST /api/vidsum/channels/restore with the rebuild roster) and fix whatever wiped vidsum_channels.json.", "Claude")
        elif hwm >= 10 and n_src < hwm * 0.7:
            add("crit", "sources-dropped", f"Sources dropped from {hwm} to {n_src}", "A large part of the roster disappeared (file race, bad edit or mass removal).",
                "Check the Events log for 'restore' and recent source removals; restore the missing sources.", "Claude")
    hrs = h.get("hours_since_article")
    if hrs is not None and h.get("uptime_min", 0) > 60 and hrs >= 14:
        add("crit" if hrs >= 24 else "warn", "no-new-articles", f"No new article for {int(hrs)} hours",
            "Nothing was published for a long stretch. Shows publish daily, so this is silence from a stalled pipeline, not a quiet day (errors may be absent).",
            "Check sources (count), the YouTube watcher, the RSS watcher, and Gemini/LunaRoute billing (402s).", "Claude")
    rl = h.get("relay") or {}
    if rl.get("tick_at") and rl.get("now") and (rl["now"] - rl["tick_at"]) / 60 > 15:
        add("crit", "mac-silent", f"The Mac relay has been silent for {int((rl['now'] - rl['tick_at']) / 60)} min", "Long podcasts and caption fallbacks are not being processed.",
            "On the Mac: launchctl list | grep vidsum-relay; if missing, bootstrap com.eedob.vidsum-relay and -rss.", "Eedo")
    return out
