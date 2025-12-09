"""NEXUS AI Agent - SQL Executor"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class DatabaseType(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"


@dataclass
class QueryResult:
    """SQL query result"""
    success: bool
    columns: List[str] = field(default_factory=list)
    rows: List[Tuple] = field(default_factory=list)
    row_count: int = 0
    affected_rows: int = 0
    last_id: Optional[int] = None
    error: Optional[str] = None
    execution_time: float = 0.0


class SQLExecutor:
    """Execute SQL queries"""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        database_type: DatabaseType = DatabaseType.SQLITE
    ):
        self.connection_string = connection_string
        self.database_type = database_type
        self._connection = None

    def connect(self, connection_string: Optional[str] = None) -> bool:
        """Connect to database"""
        conn_str = connection_string or self.connection_string

        try:
            if self.database_type == DatabaseType.SQLITE:
                import sqlite3
                self._connection = sqlite3.connect(conn_str)

            elif self.database_type == DatabaseType.POSTGRESQL:
                import psycopg2
                self._connection = psycopg2.connect(conn_str)

            elif self.database_type == DatabaseType.MYSQL:
                import mysql.connector
                self._connection = mysql.connector.connect(
                    **self._parse_connection_string(conn_str)
                )

            return True

        except Exception as e:
            return False

    def disconnect(self) -> None:
        """Disconnect from database"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def execute(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> QueryResult:
        """
        Execute SQL query

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results

        Returns:
            QueryResult object
        """
        import time
        start_time = time.time()

        if not self._connection:
            return QueryResult(
                success=False,
                error="Not connected to database"
            )

        try:
            cursor = self._connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            result = QueryResult(success=True)

            if fetch and cursor.description:
                result.columns = [desc[0] for desc in cursor.description]
                result.rows = cursor.fetchall()
                result.row_count = len(result.rows)
            else:
                result.affected_rows = cursor.rowcount
                if hasattr(cursor, 'lastrowid'):
                    result.last_id = cursor.lastrowid

            self._connection.commit()
            result.execution_time = time.time() - start_time

            return result

        except Exception as e:
            self._connection.rollback()
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def execute_many(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> QueryResult:
        """Execute query with multiple parameter sets"""
        import time
        start_time = time.time()

        if not self._connection:
            return QueryResult(
                success=False,
                error="Not connected to database"
            )

        try:
            cursor = self._connection.cursor()
            cursor.executemany(query, params_list)
            self._connection.commit()

            return QueryResult(
                success=True,
                affected_rows=cursor.rowcount,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            self._connection.rollback()
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def execute_script(self, script: str) -> QueryResult:
        """Execute SQL script"""
        import time
        start_time = time.time()

        if not self._connection:
            return QueryResult(
                success=False,
                error="Not connected to database"
            )

        try:
            cursor = self._connection.cursor()
            cursor.executescript(script)
            self._connection.commit()

            return QueryResult(
                success=True,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            self._connection.rollback()
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def fetch_one(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> Optional[Tuple]:
        """Fetch single row"""
        result = self.execute(query, params)
        if result.success and result.rows:
            return result.rows[0]
        return None

    def fetch_all(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Tuple]:
        """Fetch all rows"""
        result = self.execute(query, params)
        return result.rows if result.success else []

    def fetch_as_dicts(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Fetch results as dictionaries"""
        result = self.execute(query, params)
        if not result.success:
            return []

        return [
            dict(zip(result.columns, row))
            for row in result.rows
        ]

    def get_tables(self) -> List[str]:
        """Get list of tables"""
        if self.database_type == DatabaseType.SQLITE:
            result = self.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        elif self.database_type == DatabaseType.POSTGRESQL:
            result = self.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            )
        elif self.database_type == DatabaseType.MYSQL:
            result = self.execute("SHOW TABLES")
        else:
            return []

        return [row[0] for row in result.rows] if result.success else []

    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        """Get columns for table"""
        if self.database_type == DatabaseType.SQLITE:
            result = self.execute(f"PRAGMA table_info({table})")
            if result.success:
                return [
                    {"name": row[1], "type": row[2], "nullable": not row[3]}
                    for row in result.rows
                ]

        elif self.database_type == DatabaseType.POSTGRESQL:
            result = self.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
            """)
            if result.success:
                return [
                    {"name": row[0], "type": row[1], "nullable": row[2] == 'YES'}
                    for row in result.rows
                ]

        return []

    def _parse_connection_string(self, conn_str: str) -> Dict[str, str]:
        """Parse connection string to dict"""
        params = {}
        for part in conn_str.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                params[key.strip().lower()] = value.strip()
        return params

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

