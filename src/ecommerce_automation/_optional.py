from importlib import import_module

from .errors import MissingDependencyError

"""
这是库开发中处理可选依赖的常见模式，核心价值：

延迟导入，不强制用户装全部依赖

错误信息友好，直接告诉用户装什么

精确区分"真缺目标模块"和"目标模块内部缺依赖"，避免误报
"""

def require(module: str, extra: str):
    try:
        return import_module(module)
    except ModuleNotFoundError as error:
        if error.name != module.split(".")[0] and error.name != module:
            raise
        raise MissingDependencyError(
            f"Install the '{extra}' extra: pip install 'ecommerce-automation[{extra}]'"
        ) from error
