from typing import Optional, List, Dict, Any
import pymysql
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel


mcp = FastMCP()

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'root',
    'port': 3306,
    'charset': 'utf8mb4',
}


class Response(BaseModel):
    success: bool
    database: str
    table: str
    data: Optional[dict] | Optional[list]


def get_connection(db=None):
    config = MYSQL_CONFIG.copy()
    if db:
        config['database'] = db
    try:
        connection = pymysql.connect(**config)
        return connection
    except Exception as e:
        msg = f'mysql connect error: {e}'
        return msg


def execute_query(command, params=None, db=None, fetch=True):
    """执行 SQL。fetch=True 时返回查询结果（list），否则返回受影响行数。"""
    connection = get_connection(db)
    if not isinstance(connection, pymysql.Connection):
        return connection  # 连接错误信息
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # PyMySQL 要求 params 必须是 tuple / dict，传 list 会触发奇怪错误
            if params:
                cursor.execute(command, tuple(params))
            else:
                cursor.execute(command)

            if fetch:
                result = cursor.fetchall()
                # DictCursor.fetchall() 返回 tuple，空结果是 ()，
                # 统一转成 list，空结果就是 []，避免被误判为错误
                if isinstance(result, tuple):
                    result = list(result)
            else:
                connection.commit()
                result = cursor.rowcount
            return result
    except Exception as e:
        connection.rollback()
        return f'mysql execute error: {e}'
    finally:
        connection.close()


# ------------------- 元数据工具 -------------------

@mcp.tool(name='mysql_list_databases', description='列举MySQL中包含哪些数据库')
def mysql_list_databases():
    try:
        result = execute_query('show databases')
        if not isinstance(result, list):
            return result
        databases = [row['Database'] for row in result]
        return Response(success=True, database='', table='', data=databases)
    except Exception as e:
        return f'list database error: {e}'


@mcp.tool(name='mysql_list_tables', description='列举指定数据库中的所有表')
def mysql_list_tables(database: str):
    try:
        result = execute_query('show tables', db=database)
        if not isinstance(result, list):
            return result
        tables = [list(row.values())[0] for row in result]
        return Response(success=True, database=database, table='', data=tables)
    except Exception as e:
        return f'list table error: {e}'


@mcp.tool(name='mysql_describe_columns', description='获取表结构信息')
def mysql_describe_table(database: str, table: str):
    try:
        result = execute_query(f'describe `{table}`', db=database)
        return Response(
            success=True, database=database, table=table, data=result
        )
    except Exception as e:
        return f'mysql describe table error: {e}'


# ------------------- 查询工具 -------------------

@mcp.tool(
    name='mysql_select',
    description='执行 SELECT 查询。传入完整 SQL 语句（可含 %s 占位符）和参数列表，返回查询结果。'
)
def mysql_select(
    database: str,
    sql: str,
    params: Optional[List[Any]] = None,
    limit: int = 100,
):
    """
    :param database: 数据库名
    :param sql: SELECT 语句，例如 "select * from users where age > %s"
    :param params: 参数列表，例如 [18]
    :param limit: 最大返回条数（默认 100）
    """
    try:
        # 1. 安全检查：只允许 SELECT
        if not sql.strip().lower().startswith('select'):
            return Response(
                success=False,
                database=database,
                table='',
                data={'error': 'only SELECT is allowed'},
            )

        # 2. 参数占位符数量校验
        placeholder_count = sql.count('%s')
        param_count = len(params) if params else 0
        if placeholder_count != param_count:
            return Response(
                success=False,
                database=database,
                table='',
                data={
                    'error': (
                        f'parameter mismatch: SQL 里有 {placeholder_count} 个 %s 占位符，'
                        f'但 params 提供了 {param_count} 个参数'
                    )
                },
            )

        # 3. 自动追加 limit（如果没写）
        if 'limit' not in sql.lower():
            sql = f'{sql.rstrip(";")} limit {int(limit)}'

        # 4. 执行查询（params 传 list，execute_query 内部会转 tuple）
        result = execute_query(sql, params=params, db=database, fetch=True)

        # 5. 错误处理：execute_query 现在保证查询成功时返回 list（空结果也是 []）
        if not isinstance(result, list):
            return Response(
                success=False,
                database=database,
                table='',
                data={'error': str(result)},
            )

        # 6. 成功返回（空结果就是 data=[]）
        return Response(
            success=True,
            database=database,
            table='',
            data=result,
        )

    except Exception as e:
        return Response(
            success=False,
            database=database,
            table='',
            data={'error': f'select error: {e}'},
        )


# ------------------- 写操作工具 -------------------

@mcp.tool(
    name='mysql_insert',
    description='向指定表插入一行数据。传入表名和字段字典，自动生成 INSERT 语句。'
)
def mysql_insert(
    database: str,
    table: str,
    values: Dict[str, Any],
):
    try:
        if not values:
            return Response(
                success=False, database=database, table=table,
                data={'error': 'values is empty'},
            )
        columns = ', '.join(f'`{k}`' for k in values.keys())
        placeholders = ', '.join(['%s'] * len(values))
        sql = f'INSERT INTO `{table}` ({columns}) VALUES ({placeholders})'

        rowcount = execute_query(
            sql, params=list(values.values()), db=database, fetch=False
        )
        if not isinstance(rowcount, int):
            return Response(
                success=False, database=database, table=table,
                data={'error': str(rowcount)},
            )
        return Response(
            success=True, database=database, table=table,
            data={'affected_rows': rowcount},
        )
    except Exception as e:
        return Response(
            success=False, database=database, table=table,
            data={'error': f'insert error: {e}'},
        )


@mcp.tool(
    name='mysql_update',
    description='更新指定表中符合条件的行。传入表名、更新字段字典和 WHERE 条件。'
)
def mysql_update(
    database: str,
    table: str,
    values: Dict[str, Any],
    where: str,
    where_params: Optional[List[Any]] = None,
):
    try:
        if not values:
            return Response(
                success=False, database=database, table=table,
                data={'error': 'values is empty'},
            )
        if not where or not where.strip():
            return Response(
                success=False, database=database, table=table,
                data={'error': 'where is required to avoid full-table update'},
            )

        set_clause = ', '.join(f'`{k}` = %s' for k in values.keys())
        sql = f'UPDATE `{table}` SET {set_clause} WHERE {where}'
        params = list(values.values()) + list(where_params or [])

        rowcount = execute_query(sql, params=params, db=database, fetch=False)
        if not isinstance(rowcount, int):
            return Response(
                success=False, database=database, table=table,
                data={'error': str(rowcount)},
            )
        return Response(
            success=True, database=database, table=table,
            data={'affected_rows': rowcount},
        )
    except Exception as e:
        return Response(
            success=False, database=database, table=table,
            data={'error': f'update error: {e}'},
        )


@mcp.tool(
    name='mysql_delete',
    description='删除指定表中符合条件的行。传入表名和 WHERE 条件（必须提供，防止误删全表）。'
)
def mysql_delete(
    database: str,
    table: str,
    where: str,
    where_params: Optional[List[Any]] = None,
):
    try:
        if not where or not where.strip():
            return Response(
                success=False, database=database, table=table,
                data={'error': 'where is required to avoid full-table delete'},
            )
        sql = f'DELETE FROM `{table}` WHERE {where}'
        rowcount = execute_query(
            sql, params=list(where_params or []), db=database, fetch=False
        )
        if not isinstance(rowcount, int):
            return Response(
                success=False, database=database, table=table,
                data={'error': str(rowcount)},
            )
        return Response(
            success=True, database=database, table=table,
            data={'affected_rows': rowcount},
        )
    except Exception as e:
        return Response(
            success=False, database=database, table=table,
            data={'error': f'delete error: {e}'},
        )

@mcp.tool(
    name='mysql_create_database',
    description='创建新数据库'
)
def mysql_create_database(database_name:str,charset:str='utf8mb4'):
    command=f'CREATE DATABASE {database_name} CHARACTER SET {charset}'

    try:
        result = execute_query(command)
        return Response(
            success=True, database=database_name,
            table='',
            data=result
        )
    except Exception as e:
        msg=f'create database error: {e}'
        return msg


@mcp.tool(
    name='mysql_create_table',
    description='在指定数据库中创建新表。传入数据库名、表名和表结构定义（列定义部分）。'
)
def mysql_create_table(
    database: str,
    table_name: str,
    table_schema: str,
    if_not_exists: bool = False,
):
    """
    :param database: 数据库名
    :param table_name: 表名
    :param table_schema: 列定义，例如 "(id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(50) NOT NULL)"
    :param if_not_exists: 是否添加 IF NOT EXISTS，默认 False
    """
    try:
        if not table_name or not table_name.strip():
            return Response(
                success=False, database=database, table=table_name,
                data={'error': 'table_name is required'},
            )
        if not table_schema or not table_schema.strip():
            return Response(
                success=False, database=database, table=table_name,
                data={'error': 'table_schema is required'},
            )

        schema = table_schema.strip()
        # 兼容用户是否已带括号
        if not schema.startswith('('):
            schema = f'({schema})'

        exists_clause = 'IF NOT EXISTS ' if if_not_exists else ''
        sql = f'CREATE TABLE {exists_clause}`{table_name}` {schema}'

        result = execute_query(sql, db=database, fetch=False)
        if not isinstance(result, int):
            return Response(
                success=False, database=database, table=table_name,
                data={'error': str(result)},
            )
        return Response(
            success=True, database=database, table=table_name,
            data={'affected_rows': result},
        )
    except Exception as e:
        return Response(
            success=False, database=database, table=table_name,
            data={'error': f'create table error: {e}'},
        )

@mcp.tool(
    name='mysql_execute_command',
    description='执行特定的SQL语句，如：变更表结构、增减字段'
)
def mysql_execute_command(database: str, command: str):
    try:
        result = execute_query(command, db=database, fetch=False)
        if not isinstance(result, int):
            return Response(
                success=False, database=database, table='',
                data={'error': str(result)},
            )
        return Response(
            success=True, database=database, table='',
            data={'affected_rows': result},
        )
    except Exception as e:
        return f'mysql_execute_command error: {e}'



if __name__ == '__main__':
    mcp.run(transport='stdio')
    # print(mysql_create_database('test', 'utf8mb4'))
    # print(mysql_list_databases())
    # print(mysql_list_tables(database='lima_ai'))
    # print(mysql_describe_table(database='lima_ai',table='users'))

    # ========== 测试查询 ==========
    # print('--- select ---')
    # print(mysql_select(
    #     database='lima_ai',
    #     sql='select * from users where age = %s',
    #     params=[18],
    #     limit=50,
    # ))

    # ========== 测试插入 ==========
    # print('\n--- insert ---')
    # print(mysql_insert(
    #     database='lima_ai',
    #     table='users',
    #     values={
    #         'username': 'test_user',
    #         'age': 18,
    #         'email': 'test_user@example.com',
    #     },
    # ))
    #
    # # ========== 测试更新 ==========
    # print('\n--- update ---')
    # print(mysql_update(
    #     database='lima_ai',
    #     table='users',
    #     values={'age': 20, 'email': 'updated@example.com'},
    #     where='username = %s',
    #     where_params=['test_user'],
    # ))
    #
    # # ========== 测试删除 ==========
    # print('\n--- delete ---')
    # print(mysql_delete(
    #     database='lima_ai',
    #     table='users',
    #     where='username = %s',
    #     where_params=['test_user'],
    # ))

    # print(mysql_create_table(
    #     database='test',
    #     table_name='users',
    #     table_schema='''
    #         id INT PRIMARY KEY AUTO_INCREMENT,
    #         username VARCHAR(50) NOT NULL UNIQUE,
    #         age INT DEFAULT 0,
    #         email VARCHAR(100),
    #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     ''',
    #     if_not_exists=True,
    # ))

