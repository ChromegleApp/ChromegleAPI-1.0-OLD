import datetime
import json
import logging
import traceback
from typing import Optional, List

import aiohttp
import aiomysql
import aioredis

import config
from utilities.statistics.statistics_sql import StatisticSQL


async def user_exists(signature: str, sql_pool: aiomysql.Pool, redis: aioredis.Redis, use_redis: bool = True) -> bool:
    existence: Optional[bytes] = None

    if use_redis:
        existence = await redis.get(f"chromegle:user:{signature}")

    # Not cached (refresh every 120s)
    if existence is None:
        existence: int = await _user_exists(signature, sql_pool)
        await redis.set(f"chromegle:user:{signature}", str(existence), ex=3600)
        return bool(existence)

    # Decode & return cached value
    return bool(int(bytes.decode(existence, encoding="utf-8")))


async def _user_exists(signature: str, sql_pool: aiomysql.Pool) -> int:
    sql: StatisticSQL = StatisticSQL(sql_pool)
    return await sql.chromegle_user_exists(signature)


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


async def get_chrome_statistics(redis: aioredis.Redis, use_redis: bool = True):
    stats: Optional[bytes] = None

    if use_redis:
        stats = await redis.get("chromegle:chrome:statistics")

    # Not cached (refresh every 120s)
    if stats is None:
        stats: dict = await _retrieve_web_stats()
        await redis.set("chromegle:chrome:statistics", json.dumps(stats), ex=120)
        return stats

    stats: dict = json.loads(bytes.decode(stats, encoding="utf-8"))
    return stats


async def _retrieve_web_stats():
    """
    https://img.shields.io/chrome-web-store/users/gcbbaikjfjmidabapdnebofcmconhdbn.json
    https://img.shields.io/chrome-web-store/rating/gcbbaikjfjmidabapdnebofcmconhdbn.json
    https://img.shields.io/chrome-web-store/rating-count/gcbbaikjfjmidabapdnebofcmconhdbn.json
    https://img.shields.io/chrome-web-store/v/gcbbaikjfjmidabapdnebofcmconhdbn.json
    """

    stats: dict = {
        "users": {
            "source": "https://img.shields.io/chrome-web-store/users/gcbbaikjfjmidabapdnebofcmconhdbn.json",
            "value": None
        },
        "rating": {
            "source": "https://img.shields.io/chrome-web-store/rating/gcbbaikjfjmidabapdnebofcmconhdbn.json",
            "value": None
        },
        "rating-count": {
            "source": "https://img.shields.io/chrome-web-store/rating-count/gcbbaikjfjmidabapdnebofcmconhdbn.json",
            "value": None
        },
        "version": {
            "source": "https://img.shields.io/chrome-web-store/v/gcbbaikjfjmidabapdnebofcmconhdbn.json",
            "value": None
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(stats["users"]["source"]) as request:
                stats["users"]["value"] = (await request.json())["value"]

            async with session.get(stats["rating"]["source"]) as request:
                stats["rating"]["value"] = (await request.json())["value"]

            async with session.get(stats["rating-count"]["source"]) as request:
                stats["rating-count"]["value"] = (await request.json())["value"]

            async with session.get(stats["version"]["source"]) as request:
                stats["version"]["value"] = (await request.json())["value"]

    except:
        logging.error(traceback.format_exc())

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


async def log_statistics(signature: str, action: str, sql_pool: aiomysql.Pool, timestamp: Optional[int] = None) -> bool:
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

    await sql.insert_update_statistic(signature=signature, field_name=field_name, timestamp=timestamp)
    await sql.insert_update_tracking(stat_name=field_name)


async def log_statistics_bulk(signature: str, actions: List[list], sql_pool: aiomysql.Pool) -> bool:
    """
    Log statistics

    """

    for action, timestamp in actions:
        await log_statistics(signature=signature, action=action, sql_pool=sql_pool, timestamp=timestamp)

    return True
