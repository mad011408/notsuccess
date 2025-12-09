"""NEXUS AI Agent - Query Builder"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class JoinType(str, Enum):
    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"
    CROSS = "CROSS"


class OrderDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


@dataclass
class QueryBuilder:
    """SQL Query Builder"""

    _select: List[str] = field(default_factory=list)
    _from: str = ""
    _joins: List[str] = field(default_factory=list)
    _where: List[str] = field(default_factory=list)
    _group_by: List[str] = field(default_factory=list)
    _having: List[str] = field(default_factory=list)
    _order_by: List[str] = field(default_factory=list)
    _limit: Optional[int] = None
    _offset: Optional[int] = None
    _params: List[Any] = field(default_factory=list)
    _distinct: bool = False

    def select(self, *columns: str) -> "QueryBuilder":
        """Add SELECT columns"""
        self._select.extend(columns)
        return self

    def distinct(self) -> "QueryBuilder":
        """Add DISTINCT"""
        self._distinct = True
        return self

    def from_table(self, table: str, alias: Optional[str] = None) -> "QueryBuilder":
        """Set FROM table"""
        self._from = f"{table} AS {alias}" if alias else table
        return self

    def join(
        self,
        table: str,
        condition: str,
        join_type: JoinType = JoinType.INNER,
        alias: Optional[str] = None
    ) -> "QueryBuilder":
        """Add JOIN clause"""
        table_str = f"{table} AS {alias}" if alias else table
        self._joins.append(f"{join_type.value} JOIN {table_str} ON {condition}")
        return self

    def left_join(self, table: str, condition: str, alias: Optional[str] = None) -> "QueryBuilder":
        """Add LEFT JOIN"""
        return self.join(table, condition, JoinType.LEFT, alias)

    def right_join(self, table: str, condition: str, alias: Optional[str] = None) -> "QueryBuilder":
        """Add RIGHT JOIN"""
        return self.join(table, condition, JoinType.RIGHT, alias)

    def where(self, condition: str, *params) -> "QueryBuilder":
        """Add WHERE condition"""
        self._where.append(condition)
        self._params.extend(params)
        return self

    def where_eq(self, column: str, value: Any) -> "QueryBuilder":
        """Add equality condition"""
        self._where.append(f"{column} = ?")
        self._params.append(value)
        return self

    def where_ne(self, column: str, value: Any) -> "QueryBuilder":
        """Add not equal condition"""
        self._where.append(f"{column} != ?")
        self._params.append(value)
        return self

    def where_gt(self, column: str, value: Any) -> "QueryBuilder":
        """Add greater than condition"""
        self._where.append(f"{column} > ?")
        self._params.append(value)
        return self

    def where_gte(self, column: str, value: Any) -> "QueryBuilder":
        """Add greater than or equal condition"""
        self._where.append(f"{column} >= ?")
        self._params.append(value)
        return self

    def where_lt(self, column: str, value: Any) -> "QueryBuilder":
        """Add less than condition"""
        self._where.append(f"{column} < ?")
        self._params.append(value)
        return self

    def where_lte(self, column: str, value: Any) -> "QueryBuilder":
        """Add less than or equal condition"""
        self._where.append(f"{column} <= ?")
        self._params.append(value)
        return self

    def where_in(self, column: str, values: List[Any]) -> "QueryBuilder":
        """Add IN condition"""
        placeholders = ', '.join(['?' for _ in values])
        self._where.append(f"{column} IN ({placeholders})")
        self._params.extend(values)
        return self

    def where_not_in(self, column: str, values: List[Any]) -> "QueryBuilder":
        """Add NOT IN condition"""
        placeholders = ', '.join(['?' for _ in values])
        self._where.append(f"{column} NOT IN ({placeholders})")
        self._params.extend(values)
        return self

    def where_like(self, column: str, pattern: str) -> "QueryBuilder":
        """Add LIKE condition"""
        self._where.append(f"{column} LIKE ?")
        self._params.append(pattern)
        return self

    def where_between(self, column: str, start: Any, end: Any) -> "QueryBuilder":
        """Add BETWEEN condition"""
        self._where.append(f"{column} BETWEEN ? AND ?")
        self._params.extend([start, end])
        return self

    def where_null(self, column: str) -> "QueryBuilder":
        """Add IS NULL condition"""
        self._where.append(f"{column} IS NULL")
        return self

    def where_not_null(self, column: str) -> "QueryBuilder":
        """Add IS NOT NULL condition"""
        self._where.append(f"{column} IS NOT NULL")
        return self

    def or_where(self, condition: str, *params) -> "QueryBuilder":
        """Add OR WHERE condition"""
        if self._where:
            self._where[-1] = f"({self._where[-1]} OR {condition})"
        else:
            self._where.append(condition)
        self._params.extend(params)
        return self

    def group_by(self, *columns: str) -> "QueryBuilder":
        """Add GROUP BY"""
        self._group_by.extend(columns)
        return self

    def having(self, condition: str, *params) -> "QueryBuilder":
        """Add HAVING clause"""
        self._having.append(condition)
        self._params.extend(params)
        return self

    def order_by(
        self,
        column: str,
        direction: OrderDirection = OrderDirection.ASC
    ) -> "QueryBuilder":
        """Add ORDER BY"""
        self._order_by.append(f"{column} {direction.value}")
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """Set LIMIT"""
        self._limit = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        """Set OFFSET"""
        self._offset = count
        return self

    def build(self) -> tuple:
        """
        Build the query

        Returns:
            Tuple of (query_string, parameters)
        """
        parts = []

        # SELECT
        select_cols = self._select or ['*']
        distinct = "DISTINCT " if self._distinct else ""
        parts.append(f"SELECT {distinct}{', '.join(select_cols)}")

        # FROM
        if self._from:
            parts.append(f"FROM {self._from}")

        # JOINs
        parts.extend(self._joins)

        # WHERE
        if self._where:
            parts.append(f"WHERE {' AND '.join(self._where)}")

        # GROUP BY
        if self._group_by:
            parts.append(f"GROUP BY {', '.join(self._group_by)}")

        # HAVING
        if self._having:
            parts.append(f"HAVING {' AND '.join(self._having)}")

        # ORDER BY
        if self._order_by:
            parts.append(f"ORDER BY {', '.join(self._order_by)}")

        # LIMIT
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")

        # OFFSET
        if self._offset is not None:
            parts.append(f"OFFSET {self._offset}")

        return ' '.join(parts), tuple(self._params)

    def to_sql(self) -> str:
        """Get SQL string only"""
        sql, _ = self.build()
        return sql

    def get_params(self) -> tuple:
        """Get parameters only"""
        return tuple(self._params)

    def reset(self) -> "QueryBuilder":
        """Reset builder"""
        self._select = []
        self._from = ""
        self._joins = []
        self._where = []
        self._group_by = []
        self._having = []
        self._order_by = []
        self._limit = None
        self._offset = None
        self._params = []
        self._distinct = False
        return self


class InsertBuilder:
    """INSERT query builder"""

    def __init__(self, table: str):
        self.table = table
        self._columns: List[str] = []
        self._values: List[List[Any]] = []

    def columns(self, *columns: str) -> "InsertBuilder":
        """Set columns"""
        self._columns = list(columns)
        return self

    def values(self, *values) -> "InsertBuilder":
        """Add values"""
        self._values.append(list(values))
        return self

    def from_dict(self, data: Dict[str, Any]) -> "InsertBuilder":
        """Add from dictionary"""
        self._columns = list(data.keys())
        self._values.append(list(data.values()))
        return self

    def from_dicts(self, data_list: List[Dict[str, Any]]) -> "InsertBuilder":
        """Add from list of dictionaries"""
        if data_list:
            self._columns = list(data_list[0].keys())
            for data in data_list:
                self._values.append([data.get(c) for c in self._columns])
        return self

    def build(self) -> tuple:
        """Build INSERT query"""
        placeholders = ', '.join(['?' for _ in self._columns])
        sql = f"INSERT INTO {self.table} ({', '.join(self._columns)}) VALUES ({placeholders})"

        if len(self._values) == 1:
            return sql, tuple(self._values[0])
        return sql, [tuple(v) for v in self._values]


class UpdateBuilder:
    """UPDATE query builder"""

    def __init__(self, table: str):
        self.table = table
        self._set: Dict[str, Any] = {}
        self._where: List[str] = []
        self._params: List[Any] = []

    def set(self, column: str, value: Any) -> "UpdateBuilder":
        """Set column value"""
        self._set[column] = value
        return self

    def set_dict(self, data: Dict[str, Any]) -> "UpdateBuilder":
        """Set from dictionary"""
        self._set.update(data)
        return self

    def where(self, condition: str, *params) -> "UpdateBuilder":
        """Add WHERE condition"""
        self._where.append(condition)
        self._params.extend(params)
        return self

    def build(self) -> tuple:
        """Build UPDATE query"""
        set_parts = [f"{k} = ?" for k in self._set.keys()]
        sql = f"UPDATE {self.table} SET {', '.join(set_parts)}"

        if self._where:
            sql += f" WHERE {' AND '.join(self._where)}"

        params = list(self._set.values()) + self._params
        return sql, tuple(params)


class DeleteBuilder:
    """DELETE query builder"""

    def __init__(self, table: str):
        self.table = table
        self._where: List[str] = []
        self._params: List[Any] = []

    def where(self, condition: str, *params) -> "DeleteBuilder":
        """Add WHERE condition"""
        self._where.append(condition)
        self._params.extend(params)
        return self

    def build(self) -> tuple:
        """Build DELETE query"""
        sql = f"DELETE FROM {self.table}"

        if self._where:
            sql += f" WHERE {' AND '.join(self._where)}"

        return sql, tuple(self._params)

