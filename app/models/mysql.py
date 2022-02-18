import enum
from typing import Any

from aiomysql import Pool


class StatementEnum(enum.Enum):

    def __add__(self, other):
        return str(self) + other

    def __mod__(self, other):
        return str.__mod__(str(self.value), other)

    def __str__(self):
        return str(self.value)

    def __bool__(self):
        return bool(self.value)


class DefaultsEnum(StatementEnum):

    @staticmethod
    def parse_null(value):
        return value if str(value) != 'null' else None

    @staticmethod
    def create_null(value):
        return 'null' if value is None else value


def SQLEntryPoint(function):
    """
    Decorator to wrap methods with an SQL connection

    :param function: SQL function to decorate
    :return: Result of interior function

    """

    async def wrapper(self, *args, **kwargs):
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                # Pre-Commit to solve REPEATABLE READ
                # https://stackoverflow.com/questions/9318347/why-are-some-mysql-connections-selecting-old-data-the-mysql-database-after-a-del
                await connection.commit()
                self.connection, self.cursor = connection, cursor
                result: Any = await function(self, *args, **kwargs)
                self.connection, self.cursor = None, None
                await connection.commit()

                return result

    return wrapper


async def create_template(pool: Pool, file_path: str) -> None:
    """
    Initialize a database template from a file

    :param pool: Pool to use to create the connection
    :param file_path: Path for the .SQL file
    :return: None

    """
    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(open(file_path, encoding='utf-8').read())
            await connection.commit()

