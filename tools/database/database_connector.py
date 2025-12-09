"""NEXUS AI Agent - Database Connector"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import asyncio


class DatabaseType(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"


@dataclass
class ConnectionConfig:
    """Database connection configuration"""
    database_type: DatabaseType
    host: str = "localhost"
    port: int = 0
    database: str = ""
    username: str = ""
    password: str = ""
    options: Dict[str, Any] = None

    def __post_init__(self):
        if self.options is None:
            self.options = {}

        # Set default ports
        if self.port == 0:
            default_ports = {
                DatabaseType.POSTGRESQL: 5432,
                DatabaseType.MYSQL: 3306,
                DatabaseType.MONGODB: 27017,
                DatabaseType.REDIS: 6379,
            }
            self.port = default_ports.get(self.database_type, 0)


class DatabaseConnector:
    """Unified database connector"""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._connection = None
        self._pool = None

    async def connect(self) -> bool:
        """Connect to database"""
        try:
            if self.config.database_type == DatabaseType.SQLITE:
                import aiosqlite
                self._connection = await aiosqlite.connect(self.config.database)

            elif self.config.database_type == DatabaseType.POSTGRESQL:
                import asyncpg
                self._connection = await asyncpg.connect(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.username,
                    password=self.config.password
                )

            elif self.config.database_type == DatabaseType.MYSQL:
                import aiomysql
                self._connection = await aiomysql.connect(
                    host=self.config.host,
                    port=self.config.port,
                    db=self.config.database,
                    user=self.config.username,
                    password=self.config.password
                )

            elif self.config.database_type == DatabaseType.MONGODB:
                from motor.motor_asyncio import AsyncIOMotorClient
                url = f"mongodb://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}"
                self._connection = AsyncIOMotorClient(url)

            elif self.config.database_type == DatabaseType.REDIS:
                import aioredis
                self._connection = await aioredis.from_url(
                    f"redis://{self.config.host}:{self.config.port}",
                    password=self.config.password or None
                )

            return True

        except Exception as e:
            return False

    async def disconnect(self) -> None:
        """Disconnect from database"""
        if self._connection:
            if hasattr(self._connection, 'close'):
                result = self._connection.close()
                if asyncio.iscoroutine(result):
                    await result

            self._connection = None

    async def execute(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute query"""
        if not self._connection:
            return []

        try:
            if self.config.database_type == DatabaseType.SQLITE:
                async with self._connection.execute(query, params or ()) as cursor:
                    rows = await cursor.fetchall()
                    if cursor.description:
                        columns = [d[0] for d in cursor.description]
                        return [dict(zip(columns, row)) for row in rows]
                    return []

            elif self.config.database_type == DatabaseType.POSTGRESQL:
                rows = await self._connection.fetch(query, *(params or ()))
                return [dict(row) for row in rows]

            elif self.config.database_type == DatabaseType.MYSQL:
                async with self._connection.cursor() as cursor:
                    await cursor.execute(query, params)
                    rows = await cursor.fetchall()
                    if cursor.description:
                        columns = [d[0] for d in cursor.description]
                        return [dict(zip(columns, row)) for row in rows]
                    return []

        except Exception:
            return []

        return []

    async def execute_many(
        self,
        query: str,
        params_list: List[tuple]
    ) -> int:
        """Execute query with multiple parameters"""
        if not self._connection:
            return 0

        count = 0
        try:
            if self.config.database_type == DatabaseType.SQLITE:
                await self._connection.executemany(query, params_list)
                await self._connection.commit()
                count = len(params_list)

            elif self.config.database_type == DatabaseType.POSTGRESQL:
                await self._connection.executemany(query, params_list)
                count = len(params_list)

            elif self.config.database_type == DatabaseType.MYSQL:
                async with self._connection.cursor() as cursor:
                    await cursor.executemany(query, params_list)
                    await self._connection.commit()
                    count = cursor.rowcount

        except Exception:
            pass

        return count

    async def fetch_one(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        results = await self.execute(query, params)
        return results[0] if results else None

    async def insert(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Optional[int]:
        """Insert row"""
        columns = list(data.keys())
        values = list(data.values())

        if self.config.database_type == DatabaseType.SQLITE:
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            await self.execute(query, tuple(values))

        elif self.config.database_type == DatabaseType.POSTGRESQL:
            placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) RETURNING id"
            result = await self.fetch_one(query, tuple(values))
            return result.get('id') if result else None

        elif self.config.database_type == DatabaseType.MYSQL:
            placeholders = ', '.join(['%s' for _ in columns])
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            await self.execute(query, tuple(values))

        return None

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: str,
        where_params: tuple = ()
    ) -> int:
        """Update rows"""
        if self.config.database_type == DatabaseType.SQLITE:
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where}"
            params = tuple(data.values()) + where_params

        elif self.config.database_type == DatabaseType.POSTGRESQL:
            set_clause = ', '.join([f"{k} = ${i+1}" for i, k in enumerate(data.keys())])
            query = f"UPDATE {table} SET {set_clause} WHERE {where}"
            params = tuple(data.values()) + where_params

        elif self.config.database_type == DatabaseType.MYSQL:
            set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where}"
            params = tuple(data.values()) + where_params

        else:
            return 0

        await self.execute(query, params)
        return 1  # Simplified

    async def delete(
        self,
        table: str,
        where: str,
        where_params: tuple = ()
    ) -> int:
        """Delete rows"""
        query = f"DELETE FROM {table} WHERE {where}"
        await self.execute(query, where_params)
        return 1  # Simplified

    def get_connection(self):
        """Get raw connection"""
        return self._connection

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

