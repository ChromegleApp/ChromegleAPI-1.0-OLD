import datetime
import json
from typing import Optional

import aiomysql
import aioredis

import config
from utilities.statistics.statistics_sql import StatisticSQL


async def get_statistics(sql_pool: aiomysql.Pool, redis: aioredis.Redis, use_redis: bool = True):
    stats: Optional[bytes] = None

    if use_redis:
        stats = await redis.get("chromegle:statistics")

    # Not cached (refresh every 120s)
    if stats is None:
        stats: dict = await _retrieve_statistics(sql_pool)
        await redis.set("chromegle:statistics", json.dumps(stats), ex=120)
        return stats

    stats: dict = json.loads(bytes.decode(stats, encoding="utf-8"))
    return stats


async def _retrieve_statistics(sql_pool: aiomysql.Pool):
    _today = datetime.datetime.today().strftime('%Y%m%d')
    _week_ago = (datetime.datetime.today() - datetime.timedelta(days=7)).strftime('%Y%m%d')
    sql: StatisticSQL = StatisticSQL(sql_pool)

    # Recent Statistics
    rec_open_entries = await sql.get_recent_activity(config.Statistics.OMEGLE_OPEN_FIELD, 10)
    rec_end_entries = await sql.get_recent_activity(config.Statistics.CHAT_END_FIELD, 10)
    rec_start_entries = await sql.get_recent_activity(config.Statistics.CHAT_START_FIELD, 10)

    # Since 12:00AM
    today = await sql.get_tracking_count_between_dates(
        config.Statistics.OMEGLE_OPEN_FIELD, config.Statistics.CHAT_START_FIELD, config.Statistics.CHAT_END_FIELD, start=_today, end=_today,
    )

    # Within 1 Week of 12:00
    week = await sql.get_tracking_count_between_dates(
        config.Statistics.OMEGLE_OPEN_FIELD, config.Statistics.CHAT_START_FIELD, config.Statistics.CHAT_END_FIELD, start=_week_ago, end=_today,
    )

    # All-Time Statistics (chat_started, chat_ended, omegle_opened)
    all_time = await sql.get_tracking_count(config.Statistics.OMEGLE_OPEN_FIELD, config.Statistics.CHAT_START_FIELD, config.Statistics.CHAT_END_FIELD)

    return {
        "online_users": len(set(rec_open_entries + rec_end_entries + rec_start_entries)),
        "ten_minutes": {"chats_started": len(rec_start_entries), "chats_ended": len(rec_end_entries), "times_opened": len(rec_open_entries)},
        "today": {"times_opened": today[0], "chats_started": today[2], "chats_ended": today[1]},
        "week": {"times_opened": week[0], "chats_started": week[2], "chats_ended": week[1]},
        "forever": {"times_opened": all_time[0], "chats_started": all_time[2], "chats_ended": all_time[1]}
    }


async def log_statistics(signature: str, action: str, sql_pool: aiomysql.Pool) -> bool:
    """
    Log statistics

    """

    field_name: str = {
        "chatStarted": config.Statistics.CHAT_START_FIELD,
        "chatEnded": config.Statistics.CHAT_END_FIELD,
        "omegleOpened": config.Statistics.OMEGLE_OPEN_FIELD
    }.get(action)

    # Invalid action
    if not field_name:
        return False

    sql: StatisticSQL = StatisticSQL(sql_pool)

    await sql.insert_update_statistic(signature=signature, field_name=field_name)
    await sql.insert_update_tracking(stat_name=field_name)
