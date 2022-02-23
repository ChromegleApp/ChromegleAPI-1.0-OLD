import datetime
from typing import Optional, List

from aiomysql import Connection, Cursor, Pool

from models.mysql import SQLEntryPoint, StatementEnum


# noinspection SqlNoDataSourceInspection
class StatisticStatements(StatementEnum):
    GET_INTERNAL_ID: str = (
        """
        SELECT id 
        FROM registry 
        WHERE address='%s';
        """
    )

    CREATE_INTERNAL_ID: str = (
        """
        INSERT INTO registry (address) 
        VALUES ('%s')
        """
    )

    INSERT_UPDATE_STATISTIC: str = (
        """
        INSERT INTO %s (id) 
        VALUES(%s) 
        ON DUPLICATE KEY 
        UPDATE last_active=CURRENT_TIMESTAMP()
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
        SELECT id
        FROM %s 
        WHERE last_active >= TIMESTAMP(date_sub(now(), INTERVAL %s MINUTE))
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

    async def __get_account(self, address: str):
        """
        Get the database account for a given address

        """
        await self.cursor.execute(StatisticStatements.GET_INTERNAL_ID % address)
        result = await self.cursor.fetchone()
        return result[0] if result is not None else None

    async def __create_account(self, address: str):
        """
        Create the database account for a given address

        """
        await self.cursor.execute(StatisticStatements.CREATE_INTERNAL_ID % address)

    @SQLEntryPoint
    async def get_recent_activity(self, table_name: str, within_minutes: int):
        """
        Get a statistic from one of the timestamp tables
        """
        await self.cursor.execute(StatisticStatements.GET_RECENT_STAT % (table_name, min(within_minutes, within_minutes)))
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
    async def get_account(self, address: str):
        """
        Get an account from an address

        """

        account_id: Optional[int] = await self.__get_account(address)

        # Did not exist
        if account_id is None:
            await self.__create_account(address)
            account_id: Optional[int] = await self.__get_account(address)

        return account_id

    @SQLEntryPoint
    async def insert_update_statistic(self, account_id: int, table_name: str):
        """
        Insert a statistic into the database

        """
        await self.cursor.execute(StatisticStatements.INSERT_UPDATE_STATISTIC % (table_name, account_id))

    @SQLEntryPoint
    async def insert_update_tracking(self, stat_name: str):
        time: str = datetime.datetime.today().strftime('%Y%m%d')
        c = (StatisticStatements.INSERT_UPDATE_TRACKING % (
            time,
            stat_name,
            stat_name
        ))

        await self.cursor.execute(c)
