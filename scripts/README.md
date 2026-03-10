# Bgent Scripts

Core tooling for the Bgent framework.

## Files

- [`daily_briefing.py`](daily_briefing.py) — Morning standup & closing ceremony script. Parses `AGENT_STATE.md` into a concise briefing, loads cross-session memory, and manages memory lifecycle alerts.
  ```bash
  python daily_briefing.py --mode morning --project-root ./
  python daily_briefing.py --mode closing --project-root ./
  ```
- [`archive_memory.py`](archive_memory.py) — Archives daily logs older than 14 days to `~/.gemini/memory/archive/YYYY/MM/`.
  ```bash
  python archive_memory.py           # Archive all stale files
  python archive_memory.py --dry-run # Preview only
  ```
