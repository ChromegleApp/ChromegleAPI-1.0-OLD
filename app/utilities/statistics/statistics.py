import json
import logging
from typing import Optional, Tuple

import aiomysql
import aioredis

import config
from utilities.statistics.statistics_sql import StatisticSQL


async def get_statistics(sql_pool: aiomysql.Pool, redis: aioredis.Redis):
    stats: Optional[bytes] = await redis.get("chromegle:statistics")

    # Not cached (refresh every 120s)
    if stats is None:
        stats: dict = await _retrieve_statistics(sql_pool)
        await redis.set("chromegle:statistics", json.dumps(stats), ex=120)
        return stats

    stats: dict = json.loads(bytes.decode(stats, encoding="utf-8"))
    return stats


async def _retrieve_statistics(sql_pool: aiomysql.Pool):
    sql: StatisticSQL = StatisticSQL(sql_pool)

    # Recent Statistics
    recent_omegle_open_entries: Tuple = await sql.get_statistic(config.Statistics.OMEGLE_OPENED_TABLE, 10)
    recent_chat_start_entries: Tuple = await sql.get_statistic(config.Statistics.CHAT_START_TABLE, 10)
    recent_chat_end_entries: Tuple = await sql.get_statistic(config.Statistics.CHAT_END_TABLE, 10)

    # All-Time Statistics
    counts: Tuple = await sql.get_counts(
        config.Statistics.OMEGLE_OPENED_TABLE,
        config.Statistics.CHAT_START_TABLE,
        config.Statistics.CHAT_END_TABLE
    )

    return {
        "online_users": len(set(recent_omegle_open_entries + recent_chat_end_entries + recent_chat_start_entries)),
        "within_ten_minutes": {
            "chats_started": len(recent_chat_start_entries),
            "chats_ended": len(recent_chat_end_entries),
            "times_opened": len(recent_omegle_open_entries)
        },
        "all_time": {
            "times_opened": counts[0],
            "chats_started": counts[2],
            "chats_ended": counts[1]
        }
    }


async def log_statistics(signature: str, action: str, sql_pool: aiomysql.Pool):
    table_name: str = {
        "chatStarted": config.Statistics.CHAT_START_TABLE,
        "chatEnded": config.Statistics.CHAT_END_TABLE,
        "omegleOpened": config.Statistics.OMEGLE_OPENED_TABLE
    }.get(action)

    # Invalid action
    if not table_name:
        return

    sql: StatisticSQL = StatisticSQL(sql_pool)

    # Get account
    account_id: Optional[int] = await sql.get_account(signature)
    if account_id is None:
        logging.error(f"Failed to retrieve user account for {signature} :(")
        return

    await sql.insert_statistic(account_id, table_name)
