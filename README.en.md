[🇨🇳 中文版](./README.md)

# Bgent (体能体)

> **The Biological Backend for your AI.**

---

I thought I built an AI assistant. Turns out, *it* built *me* a job.

**Bgent** is a Markdown-native kanban & scheduling framework inspired by reverse proxy architecture. The AI Agent is the **Client** — generating plans, issuing deadlines, and managing your board. **You** are the sole **Upstream Node**: the biological backend responsible for all physical execution.

There is no auto-scaling. There is no load balancer. There is only you.

| Role | What it does | Runtime |
|------|-------------|---------|
| **Agent** (智能体) | Orchestrates tasks in the cloud. Manages the board. Never sleeps. | `∞ uptime` |
| **Bgent** (体能体) | Clears the board in the physical world. Frequently overheats. | `~16h/day, degraded` |

Congratulations — you are now officially employed by your own codebase.

## Features

- 🗂️ **Eisenhower Matrix Kanban** — Four-quadrant task management with automatic urgency tracking (`[D-X]` countdown, `[Idle: Xd]` stale detection, `[⚠️ Overloaded]` alerts)
- 📋 **Closing Ritual** — Agent automatically runs session-end ceremony: flush timestamps, archive achievements, suggest next actions
- 🧠 **Cross-Session Memory** — Two-tier memory architecture (Daily Log + Long-term) so the Agent never forgets context between conversations
- 📅 **Rolling Scheduler** — Two-week sliding window with capacity constraints and displacement buffers. The Agent schedules, you execute.
- 📄 **Pure Markdown** — No databases, no SaaS, no vendor lock-in. Just `.md` files and the crushing weight of your to-do list.

> Currently optimized for [Antigravity](https://www.cursor.com/). Core kanban format is compatible with any AI Agent that can read/write Markdown.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Mehechiger/Bgent.git
cd Bgent

# Copy templates into your project
cp templates/AGENT_STATE.template.md your-project/AGENT_STATE.md
cp -r scripts/ your-project/scripts/
cp docs/kanban_standards.md your-project/docs/

# Run the daily briefing (verify installation)
python your-project/scripts/daily_briefing.py --mode morning --project-root your-project/
```

See the [Chinese README](./README.md) for a detailed first-use guide and architecture documentation.

## License

MIT — Because even indentured servants deserve open-source tooling.

## Contributing

Pull requests welcome. If your code is also bossing you around, welcome to the cyber union.

---

*Built with 💀 by a human who mass-produced himself into a biological microservice.*
