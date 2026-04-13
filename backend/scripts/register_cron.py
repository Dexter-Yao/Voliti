# ABOUTME: 为每个活跃用户注册日终 Pipeline Cron
# ABOUTME: 使用 LangGraph SDK Cron API，每日 UTC 17:00（北京凌晨 01:00）触发

"""
用法：
  cd backend && uv run python scripts/register_cron.py --user-id <user_id>
  cd backend && uv run python scripts/register_cron.py --list
  cd backend && uv run python scripts/register_cron.py --delete <cron_id>
"""

from __future__ import annotations

import argparse
import asyncio
import os

from langgraph_sdk import get_client


API_URL = os.environ.get("LANGGRAPH_API_URL", "http://127.0.0.1:2025")
PIPELINE_ASSISTANT_ID = "day_end_pipeline"
DEFAULT_SCHEDULE = "0 17 * * *"  # UTC 17:00 = 北京 01:00


async def register(user_id: str, schedule: str = DEFAULT_SCHEDULE) -> None:
    client = get_client(url=API_URL)
    cron = await client.crons.create(
        assistant_id=PIPELINE_ASSISTANT_ID,
        schedule=schedule,
        input={"user_id": user_id},
        on_run_completed="delete",
        metadata={"user_id": user_id, "type": "day_end_pipeline"},
    )
    print(f"Cron registered: {cron['cron_id']} for user {user_id} @ {schedule}")


async def list_crons() -> None:
    client = get_client(url=API_URL)
    crons = await client.crons.search(assistant_id=PIPELINE_ASSISTANT_ID, limit=100)
    if not crons:
        print("No crons registered.")
        return
    for c in crons:
        meta = c.get("metadata", {})
        print(f"  {c['cron_id']}  user={meta.get('user_id', '?')}  schedule={c.get('schedule', '?')}")


async def delete(cron_id: str) -> None:
    client = get_client(url=API_URL)
    await client.crons.delete(cron_id)
    print(f"Cron deleted: {cron_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="管理日终 Pipeline Cron")
    parser.add_argument("--user-id", help="注册 cron 的用户 ID")
    parser.add_argument("--schedule", default=DEFAULT_SCHEDULE, help="Cron 表达式（默认 UTC 17:00）")
    parser.add_argument("--list", action="store_true", help="列出所有已注册的 cron")
    parser.add_argument("--delete", metavar="CRON_ID", help="删除指定 cron")
    args = parser.parse_args()

    if args.list:
        asyncio.run(list_crons())
    elif args.delete:
        asyncio.run(delete(args.delete))
    elif args.user_id:
        asyncio.run(register(args.user_id, args.schedule))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
