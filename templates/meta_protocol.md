# Bgent Meta Protocol — Agent 行为规则参考

<!--
  本文件定义 AI Agent 在 Bgent 管理的项目中应遵守的行为规则。
  你可以将这些规则整合到你的 Agent 平台全局配置中，
  或者在 SKILL 安装后由 Agent 自动加载。

  当前版本针对 Antigravity 优化。
  
  使用说明：
  - [CUSTOMIZE] 标记的地方需要你根据项目情况修改
  - 其他部分为框架核心规则，建议保留
-->

---

## Tier 1：核心规则

### 1. 初始化

每次会话开始时，按顺序执行：
1. 读取项目根目录 `README.md`
2. 运行 `scripts/daily_briefing.py --mode morning --project-root ./`（如果存在）
3. 若脚本不存在或执行失败，回退至扫描 `AGENT_STATE.md` 的 **Focus** 和 **Recent Achievements**

### 2. 语言规则

<!-- [CUSTOMIZE] 根据你的工作语言修改 -->

- **交互语言**：中文（简体）
- **技术术语**：保留英语原文（如 `Hyperparameter Tuning`、`fine-tuning`）

### 3. 结项仪式 (Closing Ritual)

当有实质产出的任务完成时（不含简单问答），Agent 执行结项仪式：

1. **记忆写入**：追加结构化摘要到 `.agent/memory/YYYY-MM-DD.md`
   ```markdown
   ## HH:MM — [对话主题简述]
   - [做了什么，1句]
   - 决策: [关键决策，如有]
   - 新信息: [用户告知的新事实/偏好，如有]
   - 下次注意: [后续对话需要知道的上下文，可为空]
   ```
2. 在 `AGENT_STATE.md` **Recent Achievements** 记录完成的任务
3. 刷新所有 `[D-X]` 倒计时和 `[Idle: Xd]` 标签
4. 如任务改变了项目优先级，更新 **Focus** 部分
5. 基于 **Pending Actions** 向用户建议下一步

**自检**：在发送最终回复前确认两项：
1. "我写了 Daily Log 记忆吗？"
2. "我更新 `AGENT_STATE.md` 了吗？"

### 4. 文件写入铁律

对文本/文档的追加或写入操作：
- **唯一合法途径**：使用 Agent 原生编辑工具（`write_to_file`、`replace_file_content` 等）
- **禁止**：写 Python 脚本执行文件写入（如 `with open(..., 'a')`），禁止 shell 重定向

### 5. 看板禁删原则

**严禁未经用户批准删除** `AGENT_STATE.md` 中未完成的任务。
更新看板时遵循**纯加法原则**：允许追加标签、更改状态、补充信息，禁止删减或改写原有条目。

---

## Tier 2：触发式规则

以下规则仅在特定条件下激活：

### 记忆管理

- **长期记忆写入**：用户显式要求"记住"某信息时 → Agent 必须先提炼表述，向用户发送预览确认后再写入 `.agent/MEMORY.md`
- **Monthly Review**：`daily_briefing.py` 检测到上次审核超 30 天 → 提醒执行 MEMORY.md 审核

### 工作流

- **执行确认**：架构级重构或影响面大的修改 → 先向用户提方案，获确认后再执行
- **防遗漏**：执行重构时，修改前列出关键功能点清单，修改后逐项确认

<!-- [CUSTOMIZE] 按需添加你项目特有的触发式规则 -->
