from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from .._optional import require


@dataclass(frozen=True)
class MySQLConfig:
    host: str
    user: str
    password: str = field(repr=False)
    database: str
    port: int = 3306
    max_connections: int = 5
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30

    def __post_init__(self):
        if not self.host or not self.user or not self.database:
            raise ValueError("MySQL host/user/database are required")
        if not 1 <= self.port <= 65535 or self.max_connections < 1:
            raise ValueError("Invalid MySQL port/max_connections")


class MySQLPool:
    """Each instance owns one pool. No process-wide singleton or implicit credentials."""

    def __init__(self, config: MySQLConfig):
        pymysql = require("pymysql", "mysql")
        pooled = require("dbutils.pooled_db", "mysql")
        self._pool = pooled.PooledDB(
            creator=pymysql, mincached=0, maxcached=config.max_connections,
            maxconnections=config.max_connections, blocking=False, ping=1,
            host=config.host, port=config.port, user=config.user, password=config.password,
            database=config.database, charset="utf8mb4", autocommit=False,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=config.connect_timeout, read_timeout=config.read_timeout,
            write_timeout=config.write_timeout,
        )

    def connection(self):
        return self._pool.connection()

    def close(self):
        self._pool.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class BaseDAO:
    def __init__(self, pool: Any):
        self.pool = pool

    @contextmanager
    def transaction(self):
        connection = self.pool.connection()
        try:
            connection.begin()
            with connection.cursor() as cursor:
                yield cursor
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def execute(self, sql: str, params: tuple | None = None) -> int:
        with self.transaction() as cursor:
            return cursor.execute(sql, params)

    def executemany(self, sql: str, rows) -> int:
        with self.transaction() as cursor:
            return cursor.executemany(sql, rows)

    def fetchone(self, sql: str, params: tuple | None = None):
        with self.transaction() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def fetchall(self, sql: str, params: tuple | None = None):
        with self.transaction() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
