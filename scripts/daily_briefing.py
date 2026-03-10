#!/usr/bin/env python3
"""
Daily Briefing Tool — Bgent 框架的 Agent 初始化与结项核心脚本

=== 设计理念 ===
本脚本是 Bgent 框架中 Agent 与项目看板之间的"脱水层"——
Agent 不直接读取 AGENT_STATE.md（太长、太杂），
而是通过本脚本获取精简的结构化摘要。

=== 三大职责 ===
1. 看板解析
   - Morning: 提取截止日期、焦点、A象限待办、约束、被挤出项
   - Closing: 提取待办优先级，建议下一步
   - 来源: AGENT_STATE.md

2. 跨对话记忆加载
   - 读取 .agent/MEMORY.md（长期记忆：用户偏好/事实/教训）
   - 读取 .agent/memory/YYYY-MM-DD.md（今天+昨天的 daily log）
   - 来源: .agent/memory/ + .agent/MEMORY.md

3. 记忆生命周期管理
   - 归档检测: 14 天前的 daily log → 提示调用 archive_memory.py
   - 月度审核提醒: 上次审核超 30 天 → 提示执行 MEMORY.md 审核

用法:
    python daily_briefing.py --mode morning --project-root ./
    python daily_briefing.py --mode closing --project-root ./
"""

import os
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# --- 默认配置 ---
# 记忆路径在运行时基于 project root 动态设置
MEMORY_DIR = None
MEMORY_FILE = None
MEMORY_ARCHIVE_DIR = None
LAST_ARCHIVE_FILE = None
DAILY_LOG_RETENTION_DAYS = 14


def init_memory_paths(project_root: Path):
    """基于项目根目录初始化记忆路径（.agent/ 子目录）"""
    global MEMORY_DIR, MEMORY_FILE, MEMORY_ARCHIVE_DIR, LAST_ARCHIVE_FILE
    bgent_dir = project_root / ".agent"
    MEMORY_DIR = bgent_dir / "memory"
    MEMORY_FILE = bgent_dir / "MEMORY.md"
    MEMORY_ARCHIVE_DIR = MEMORY_DIR / "archive"
    LAST_ARCHIVE_FILE = MEMORY_DIR / ".last_archive"


def archive_old_daily_logs():
    """每 14 天检测一次待归档的 daily log（不执行归档，归档由 archive_memory.py 完成）。

    通过 .last_archive 标记文件判断是否到期：
    - 标记不存在 → 首次，立即检测
    - now - last_archive < 14d → 未到期，跳过
    - now - last_archive >= 14d → 到期，列出所有 > 14 天的文件
    逾期顺延：归档后 archive_memory.py 更新标记，下次从新标记起算 14 天。
    """
    if not MEMORY_DIR.exists():
        return []

    # 检查是否到了归档周期
    if LAST_ARCHIVE_FILE.exists():
        try:
            last_date = datetime.strptime(
                LAST_ARCHIVE_FILE.read_text(encoding='utf-8').strip(), "%Y-%m-%d"
            )
            if (datetime.now() - last_date).days < DAILY_LOG_RETENTION_DAYS:
                return []  # 未到期，跳过
        except (ValueError, OSError):
            pass  # 标记损坏，视为需要检测

    # 列出所有超龄文件
    stale = []
    cutoff = datetime.now() - timedelta(days=DAILY_LOG_RETENTION_DAYS)
    for f in MEMORY_DIR.glob("*.md"):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d")
            if file_date < cutoff:
                stale.append(f.stem)
        except ValueError:
            continue
    return stale


def check_monthly_review():
    """检查是否需要月度 MEMORY.md 审核（滚动 30 天窗口）"""
    if not MEMORY_FILE.exists():
        return None
    content = MEMORY_FILE.read_text(encoding='utf-8')
    review_dates = re.findall(r'\[审核 (\d{4}-\d{2}-\d{2})\]', content)
    if review_dates:
        last_review = max(datetime.strptime(d, "%Y-%m-%d") for d in review_dates)
        if (datetime.now() - last_review).days < 30:
            return None
    entry_count = len([l for l in content.split('\n') if l.strip().startswith('- [')])
    if entry_count == 0:
        return None
    return f"🧠 月度记忆审核提醒：MEMORY.md 有 {entry_count} 条待审条目，请在近期对话中执行审核（删除/提升/保留）。"


def parse_deadlines(content):
    """提取倒计时部分，移除已完成项"""
    deadlines = []
    lines = content.split('\n')
    start_idx = -1
    for i, line in enumerate(lines):
        if "## ⏳ 临近截止与倒计时" in line or "## ⌚ 临近截止与倒计时" in line:
            start_idx = i
            break

    if start_idx == -1:
        return []

    for line in lines[start_idx+1:]:
        if line.startswith('##') or line.startswith('---'):
            break
        if not line.strip() or line.strip().startswith('*'):
            continue

        # 忽略已完成的任务
        if "[DONE]" in line or "[x]" in line.lower() or "~~" in line:
            continue

        # 尝试提取日期和事件
        match = re.search(r'(\d{2}-\d{2}):\s*(.*)', line)
        if match:
            date_str = match.group(1)
            event = match.group(2).strip()

            # 计算 D-X
            try:
                event_date = datetime.strptime(f"{datetime.now().year}-{date_str}", "%Y-%m-%d")
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                delta = (event_date - today).days

                if delta == 0:
                    tag = "[TODAY!]"
                elif delta < 0:
                    tag = f"[OVERDUE {abs(delta)}d]"
                else:
                    tag = f"[D-{delta}]"

                clean_event = re.sub(r'^- \[ \] ', '', event)
                deadlines.append(f"  {tag} {date_str} {clean_event}")
            except ValueError:
                deadlines.append(f"  {line.strip().lstrip('- ')}")
        else:
            deadlines.append(f"  {line.strip().lstrip('- ')}")

    return deadlines[:5]  # 只保留前 5 条最紧急的


def parse_focus(content):
    """提取今日焦点，兼容表格日程或普通列项"""
    focus_items = []
    lines = content.split('\n')
    in_section = False

    today_date = f"{datetime.now().month}/{datetime.now().day:02d}"
    fallback_date = f"{datetime.now().strftime('%m-%d')}"

    capturing_today = False
    fallback_items = []

    for line in lines:
        if "## 🎯 当前焦点" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith('## '):
                break

            line_stripped = line.strip()

            if "|" in line_stripped and "---|---" not in line_stripped:
                # 表格处理逻辑
                parts = [p.strip() for p in line_stripped.split('|') if p.strip()]
                if len(parts) >= 2:
                    col1 = parts[0]
                    if today_date in col1 or fallback_date in col1:
                        capturing_today = True
                        task_desc = " | ".join(parts[1:]).replace("~~", "").replace("✅", "")
                        focus_items.append(f"  📌 {task_desc}")
                    elif capturing_today and not col1:
                        task_desc = " | ".join(parts[1:]).replace("~~", "").replace("✅", "")
                        focus_items.append(f"  📌 {task_desc}")
                    elif capturing_today and col1 and ("周" in col1 or re.search(r'\d{1,2}/\d{1,2}', col1)):
                        capturing_today = False
            elif line_stripped.startswith('-') and not capturing_today:
                if "**" in line_stripped and "[x]" not in line_stripped.lower():
                    fallback_items.append(f"  📌 {line_stripped.lstrip('- ')}")

    if focus_items:
        return focus_items
    return fallback_items[:3]


def parse_pending_a(content):
    """提取 A 象限待办项"""
    pending_a = []
    lines = content.split('\n')
    in_section = False
    for line in lines:
        if "### 🔴 第一象限" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith('###') or line.startswith('##'):
                in_section = False
                continue
            if line.strip().startswith("- [ ]"):
                task = line.replace("- [ ]", "").strip()
                pending_a.append(f"  - {task}")
    return pending_a


def parse_full_focus(content):
    """提取整个 '当前焦点' 板块的文本，用于对齐待办"""
    lines = content.split('\n')
    focus_text = []
    in_section = False
    for line in lines:
        if "## 🎯 当前焦点" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith('## '):
                break
            focus_text.append(line)
    return "\n".join(focus_text)


def parse_constraints(content):
    """提取 📵 当前约束声明 板块中的常规和临时约束"""
    constraints = []
    lines = content.split('\n')
    in_section = False
    sub_label = ""

    for line in lines:
        if '## 📵 当前约束声明' in line:
            in_section = True
            continue
        if in_section:
            if line.startswith('## ') and '📵' not in line:
                break
            if line.startswith('---'):
                break
            if '### 🔁 常规约束' in line:
                sub_label = '🔁'
                continue
            if '### ⏳ 临时约束' in line:
                sub_label = '⏳'
                continue
            line_stripped = line.strip()
            if line_stripped.startswith('-') and sub_label:
                content_part = line_stripped.lstrip('- ').replace('**', '')
                constraints.append(f"  {sub_label} {content_part}")

    return constraints


def parse_displaced(content):
    """提取 🗃️ 被挤出项 板块中的任务信息"""
    displaced = []
    lines = content.split('\n')
    in_section = False
    for line in lines:
        if "### 🗃️ 被挤出项" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith('###') or line.startswith('##'):
                in_section = False
                continue
            line_stripped = line.strip()
            if line_stripped.startswith("- [ ]"):
                task = line_stripped.replace("- [ ]", "").strip()
                displaced.append(f"  📦 {task}")
            elif line_stripped.startswith("-") and "[无" not in line_stripped:
                displaced.append(f"  📦 {line_stripped.lstrip('- ')}")
    return displaced


def parse_memory():
    """读取记忆文件：MEMORY.md（长期）+ 今天/昨天的 daily log"""
    memory_items = []

    # 1. 读取长期记忆
    if MEMORY_FILE.exists():
        content = MEMORY_FILE.read_text(encoding='utf-8').strip()
        lines = [l for l in content.split('\n') if l.strip() and not l.startswith('# 长期记忆')]
        if lines:
            memory_items.append("🧠 长期记忆:")
            for line in lines:
                if line.startswith('## '):
                    memory_items.append(f"  {line.strip('#').strip()}")
                elif line.startswith('- '):
                    memory_items.append(f"  {line}")

    # 2. 读取今天和昨天的 daily log
    if MEMORY_DIR.exists():
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        for day, label in [(today, "今天"), (yesterday, "昨天")]:
            day_file = MEMORY_DIR / f"{day.strftime('%Y-%m-%d')}.md"
            if day_file.exists():
                content = day_file.read_text(encoding='utf-8').strip()
                lines = [l for l in content.split('\n')
                         if l.strip() and not l.startswith('# 20')]
                if lines:
                    memory_items.append(f"🗓️ {label}的对话记忆 ({day.strftime('%m-%d')}):")
                    for line in lines:
                        memory_items.append(f"  {line}")

    return memory_items


def get_morning_briefing(content):
    deadlines = parse_deadlines(content)
    focus = parse_focus(content)
    pending_a = parse_pending_a(content)
    constraints = parse_constraints(content)
    displaced = parse_displaced(content)
    full_focus = parse_full_focus(content).lower()

    # 检查 A 象限待办是否已排产
    unscheduled = []
    clean_focus = re.sub(r'\[.*?\]', '', full_focus)
    clean_focus = clean_focus.replace('**', '').replace('~~', '').replace('`', '')

    for task in pending_a:
        t = task.strip().lstrip('-').strip()
        t = re.sub(r'\[.*?\]', '', t)
        t = t.replace('**', '').replace('~~', '').replace('`', '')
        clean_item = re.sub(r'[^\w\u4e00-\u9fff]', '', t.lower())
        clean_focus_lite = re.sub(r'[^\w\u4e00-\u9fff]', '', full_focus)
        match_key = clean_item[:8]
        if not match_key or match_key not in clean_focus_lite:
            unscheduled.append(task)

    date_now = datetime.now().strftime("%Y-%m-%d")

    briefing = [
        f"📋 晨间简报 ({date_now})",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]

    if constraints:
        briefing.append("📵 约束预警:")
        briefing.extend(constraints)

    if displaced:
        briefing.append("🗃️ 弹性置换缓冲区 (请优先处理):")
        briefing.extend(displaced)

    if deadlines:
        briefing.append("🔥 紧急倒计时:")
        briefing.extend(deadlines)

    if unscheduled:
        briefing.append("⚠️ 排产缺失预警 (A象限项未进入 Focus):")
        for task in unscheduled:
            briefing.append(f"  [⚠️ UNSCHEDULED]{task}")

    if focus:
        briefing.append("📌 今日焦点 (P0/P1):")
        briefing.extend(focus)

    briefing.append(f"❓ 其他 A象限待办: {len(pending_a)}+ 项")
    briefing.extend(pending_a)

    memory = parse_memory()
    if memory:
        briefing.append("")
        briefing.extend(memory)

    # 检测待归档的旧 daily log
    stale = archive_old_daily_logs()
    if stale:
        briefing.append(f"📦 待归档 {len(stale)} 个过期 daily log: {', '.join(sorted(stale))}")
        briefing.append(f"   → 请执行: python scripts/archive_memory.py")

    # 月度审核提醒
    review_reminder = check_monthly_review()
    if review_reminder:
        briefing.append("")
        briefing.append(review_reminder)

    return "\n".join(briefing)


def get_closing_briefing(content):
    pending_a = parse_pending_a(content)
    deadlines = parse_deadlines(content)
    constraints = parse_constraints(content)

    time_now = datetime.now().strftime("%Y-%m-%d %H:%M")

    briefing = [
        f"📊 结项简报 ({time_now})",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "✅ 看板已刷新",
        "🔜 建议下一步 (按优先级):"
    ]

    if pending_a:
        for i, item in enumerate(pending_a, 1):
            briefing.append(f"  {i}. {item.strip('- ')}")
    else:
        briefing.append("  [无紧急待办，请检阅 B 象限]")

    if deadlines:
        briefing.append("⏰ 近期预警:")
        briefing.extend(deadlines[:2])

    if constraints:
        briefing.append("📵 近期约束提醒:")
        briefing.extend(constraints)

    return "\n".join(briefing)


def main():
    parser = argparse.ArgumentParser(description="Bgent Daily Briefing Tool")
    parser.add_argument("--mode", choices=["morning", "closing"], required=True,
                        help="morning = 会话启动简报, closing = 结项仪式简报")
    parser.add_argument("--project-root", type=str, default=None,
                        help="项目根目录路径（AGENT_STATE.md 所在目录）。"
                             "默认使用脚本所在目录的上一级。")
    args = parser.parse_args()

    # 确定项目根目录
    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = Path(__file__).resolve().parent.parent

    # 初始化记忆路径
    init_memory_paths(project_root)

    agent_state_file = project_root / "AGENT_STATE.md"

    if not agent_state_file.exists():
        print(f"Error: {agent_state_file} not found.")
        print(f"Hint: Use --project-root to specify where AGENT_STATE.md lives.")
        return

    with open(agent_state_file, "r", encoding="utf-8") as f:
        content = f.read()

    if args.mode == "morning":
        print(get_morning_briefing(content))
    else:
        print(get_closing_briefing(content))


if __name__ == "__main__":
    main()
