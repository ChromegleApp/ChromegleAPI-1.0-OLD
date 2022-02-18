from typing import Optional

from aiomysql import Connection, Cursor, Pool

from models.mysql import SQLEntryPoint, StatementEnum


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

    INSERT_STATISTIC: str = (
        """
        INSERT INTO %s (id) 
        VALUES (%s) 
        """
    )

    GET_RECENT_STAT: str = (
        """
        SELECT id
        FROM %s 
        WHERE TIMESTAMP >= TIMESTAMP(date_sub(now(), INTERVAL %s MINUTE))
        """
    )

    GET_ENTRY_COUNT: str = (
        """
        SELECT %s FROM dual
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
        await self.cursor.execute(StatisticStatements.GET_INTERNAL_ID % (address))
        result = await self.cursor.fetchone()
        return result[0] if result is not None else None

    async def __create_account(self, address: str):
        """
        Create the database account for a given address

        """
        await self.cursor.execute(StatisticStatements.CREATE_INTERNAL_ID % (address))

    @SQLEntryPoint
    async def get_statistic(self, table_name: str, within_minutes: int):
        """
        Get a statistic from one of the timestamp tables
        """
        await self.cursor.execute(StatisticStatements.GET_RECENT_STAT % (table_name, min(within_minutes, within_minutes)))
        return await self.cursor.fetchall()

    @SQLEntryPoint
    async def get_counts(self, *table_names: str):
        # If no tables requested
        if len(table_names) < 1:
            return []

        # Retrieve count from tables
        await self.cursor.execute(
            StatisticStatements.GET_ENTRY_COUNT % (','.join([f"(SELECT COUNT(*) FROM {name}) AS {name}" for name in table_names]))
        )

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
    async def insert_statistic(self, account_id: int, table_name: str):
        """
        Insert a statistic into the database

        """
        await self.cursor.execute(StatisticStatements.INSERT_STATISTIC % (table_name, account_id))
