import datetime
from typing import Optional, List

from aiomysql import Connection, Cursor, Pool

from models.mysql import SQLEntryPoint, StatementEnum


# noinspection SqlNoDataSourceInspection
class StatisticStatements(StatementEnum):
    CHROMEGLE_USER_EXISTS: str = (
        """
        SELECT
        CASE WHEN EXISTS 
        (
            SELECT * FROM user_tracking WHERE address='%s'
        )
        THEN 1
        ELSE 0
        END
        """
    )

    INSERT_UPDATE_STATISTIC: str = (
        """
        INSERT INTO user_tracking (address) 
        VALUES('%s') 
        ON DUPLICATE KEY 
        UPDATE %s=%s
        """
    )

    INSERT_UPDATE_TRACKING: str = (
        """
        INSERT INTO stat_tracking (date, chat_started, chat_ended, omegle_opened) 
        VALUES(%s, 0, 0, 0) 
        ON DUPLICATE KEY 
        UPDATE %s=%s+1
        """
    )

    GET_RECENT_STAT: str = (
        """
        SELECT address
        FROM user_tracking
        WHERE %s >= TIMESTAMP(date_sub(UTC_TIMESTAMP(), INTERVAL %s MINUTE))
        """
    )

    GET_ALL_TIME_COUNT: str = (
        """
        SELECT %s
        FROM stat_tracking
        """
    )

    GET_DATE_STAT: str = (
        """
        SELECT %s FROM stat_tracking WHERE date=%s
        """
    )

    GET_BETWEEN_DATE_STAT: str = (
        """
        SELECT %s FROM stat_tracking WHERE date BETWEEN %s AND %s
        """

    )

    CLEAR_TABLE: str = (
        """
        DELETE FROM %s
        """
    )


class StatisticSQL:

    def __init__(self, pool: Pool):
        self.pool: Pool = pool
        self.connection: Optional[Connection] = None
        self.cursor: Optional[Cursor] = None

    @SQLEntryPoint
    async def get_recent_activity(self, field_name: str, within_minutes: int):
        """
        Get a statistic from one of the timestamp tables
        """
        await self.cursor.execute(StatisticStatements.GET_RECENT_STAT % (field_name, min(within_minutes, within_minutes)))
        return await self.cursor.fetchall()

    @SQLEntryPoint
    async def get_tracking_count(self, *stat_name):
        built: List[str] = [f"CAST(SUM({stat}) AS SIGNED)" for stat in stat_name]
        await self.cursor.execute(StatisticStatements.GET_ALL_TIME_COUNT % ','.join(built))
        return await self.cursor.fetchone()

    @SQLEntryPoint
    async def get_tracking_count_between_dates(self, *stat_name, start: str, end: str):
        built: List[str] = [f"CAST(SUM({stat}) AS SIGNED)" for stat in stat_name]
        await self.cursor.execute(StatisticStatements.GET_BETWEEN_DATE_STAT % (','.join(built), start, end))
        return await self.cursor.fetchone()

    @SQLEntryPoint
    async def insert_update_statistic(self, signature: str, field_name: str, timestamp: Optional[int] = None):
        """
        Insert a statistic into the database

        """

        await self.cursor.execute(StatisticStatements.INSERT_UPDATE_STATISTIC % (
            signature,
            field_name,
            "UTC_TIMESTAMP()" if timestamp is None else "'" + datetime.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") + "'"
        ))

    @SQLEntryPoint
    async def chromegle_user_exists(self, signature: str) -> int:
        """
        Check if a user is saved in chromegle

        """

        await self.cursor.execute(StatisticStatements.CHROMEGLE_USER_EXISTS % signature)
        return (await self.cursor.fetchone())[0]

    @SQLEntryPoint
    async def insert_update_tracking(self, stat_name: str):
        time: str = datetime.datetime.today().strftime('%Y%m%d')
        c = (StatisticStatements.INSERT_UPDATE_TRACKING % (
            time,
            stat_name,
            stat_name
        ))

        await self.cursor.execute(c)
