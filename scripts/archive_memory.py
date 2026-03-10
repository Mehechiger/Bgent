#!/usr/bin/env python3
"""归档超过 14 天的 daily log 到 archive/YYYY/MM/。

归档完成后更新 .last_archive 标记，重置 14 天检测周期（逾期顺延）。

协议依赖:
- daily_briefing.py archive_old_daily_logs()（检测待归档文件）

用法:
    python scripts/archive_memory.py           # 归档所有超龄文件
    python scripts/archive_memory.py --dry-run  # 仅预览，不执行
"""

from datetime import datetime, timedelta
from pathlib import Path

MEMORY_DIR = Path.home() / ".gemini" / "memory"
ARCHIVE_DIR = MEMORY_DIR / "archive"
LAST_ARCHIVE_FILE = MEMORY_DIR / ".last_archive"
RETENTION_DAYS = 14


def main():
    import argparse
    parser = argparse.ArgumentParser(description="归档超过 14 天的 daily log")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不执行移动")
    args = parser.parse_args()

    if not MEMORY_DIR.exists():
        print("ℹ️ 记忆目录不存在，无需归档")
        return

    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    targets = []

    for f in sorted(MEMORY_DIR.glob("*.md")):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d")
            if file_date < cutoff:
                dest_dir = ARCHIVE_DIR / f"{file_date.year}" / f"{file_date.month:02d}"
                targets.append((f, dest_dir / f.name))
        except ValueError:
            continue

    if not targets:
        print("ℹ️ 无需归档的文件")
        return

    for src, dest in targets:
        if args.dry_run:
            print(f"  [DRY-RUN] {src.name} → {dest}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dest)
            print(f"  ✅ {src.name} → {dest}")

    action = "预览" if args.dry_run else "已归档"
    print(f"\n{action} {len(targets)} 个文件")

    # 更新归档标记（完成本次周期检查，重置 14 天倒计时）
    if not args.dry_run:
        today = datetime.now().strftime("%Y-%m-%d")
        LAST_ARCHIVE_FILE.write_text(today, encoding="utf-8")
        print(f"📌 归档周期标记已更新: {today}（下个检测周期: 14 天后）")


if __name__ == "__main__":
    main()
