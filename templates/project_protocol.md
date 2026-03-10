# Bgent Project Protocol — 状态驱动工作流模板

<!--
  本文件定义项目级的状态驱动工作流。
  将它整合进你的项目 README.md，或作为独立协议文件引用。
  
  核心理念：项目协作不绑定单一会话，而是通过持久化文档实现跨会话上下文重建。
-->

---

## 工作模式：状态驱动 (State-Driven Workflow)

> [!IMPORTANT]
> **Agent 初始化协议**：所有新会话 Agent 必须执行 **README → 脚本简报** 的加载顺序。
> `AGENT_STATE.md` 的状态获取**默认通过脚本**（`scripts/daily_briefing.py`）完成。
> 直接 `view_file` 读取全文仅限：(a) 结项仪式需要回写时、(b) 脚本执行失败时、(c) 主动检索特定信息时。

### A. 会话初始化 (Session Start)

1. **加载 README.md**：理解项目背景、目标和规则
2. **运行自动简报 (MANDATORY)**：
   ```bash
   python scripts/daily_briefing.py --mode morning --project-root ./
   ```
   脚本输出完全替代对 `AGENT_STATE.md` 的直接读取；脚本失败时回退至手动扫描看板。
3. **记忆加载**：读取 `~/.gemini/memory/` 下今天和昨天的日志（由脚本纳入简报）

### B. 任务执行中 (During Task) — 上下文重建

<!-- [CUSTOMIZE] 定义你项目特有的上下文路由表。
     格式：当进入特定任务时，Agent 按路由表加载对应文件。 -->

```markdown
| 场景 | 触发关键词 | 加载文件 |
|------|-----------|---------|
| 看板/排产 | 结项、排产、看板 | → docs/kanban_standards.md |
| 技术开发 | 开发、重构、部署 | → docs/architecture.md |
```

> 各协议文件内部包含进入该场景后的**详细文件加载清单**。
> Agent 按路由表找到协议文件后，读取该文件获取完整指令。

### C. 结项仪式 (Closing Ritual)

1. **记忆写入**：追加结构化摘要到 `~/.gemini/memory/YYYY-MM-DD.md`
2. **运行结项脚本**：`scripts/daily_briefing.py --mode closing`
3. **时效性标记更新**：按看板管理规范更新所有 `[D-X]` 倒计时
4. **结项回写**：刷新看板中的时间戳，同步成就记录
5. **排产重排**：逐项确认未完成任务的去向

### D. 跨对话记忆 (Cross-Conversation Memory)

本框架使用三层记忆架构实现跨对话上下文持久化：

| 层 | 文件 | 生命周期 | 内容 |
|---|------|---------|------|
| **Daily Log** | `~/.gemini/memory/YYYY-MM-DD.md` | 短期（天） | 对话上下文、决策、新事实 |
| **Long-term** | `~/.gemini/MEMORY.md` | 持久 | 用户显式要求记住的偏好/事实/教训 |
| **Achievements** | `AGENT_STATE.md` | 滚动 7 天 | 任务完成结果 |

**生命周期管理**：
- **Daily Log**：14 天后归档到 `~/.gemini/memory/archive/YYYY/MM/`，不删除
- **MEMORY.md**：每月审核一次（删除过时 / 提升至协议 / 保留观察）
