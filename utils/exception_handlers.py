from sqlite3 import IntegrityError

from sqlalchemy.exc import SQLAlchemyError

from utils.exception import http_exception_handler,general_exception_handler,integrity_error_handler,sqlalchemy_error_handler
from fastapi import HTTPException


def register_exception_handlers(app):
    """注册全局异常处理：子类在前，父类在后：具体的在前，抽象在后"""
    app.add_exception_handler(HTTPException, http_exception_handler) # 业务
    app.add_exception_handler(IntegrityError, integrity_error_handler) # 数据完整性约束
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler) # 数据库
    app.add_exception_handler(Exception, general_exception_handler) # 兜底
