from mcp.server.fastmcp import FastMCP

# 创建 MCP 服务器实例
mcp = FastMCP('Math Tools - SSE')

# ============ 注册工具方法 ============

@mcp.tool()
def add(a: int, b: int) -> int:
    """
    计算两个整数的和
    """
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """
    计算两个整数的乘积
    """
    return a * b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """
    计算两个整数的差 (a - b)
    """
    return a - b

@mcp.tool()
def divide(a: int, b: int) -> float:
    """
    计算两个整数的商 (a / b)
    """
    if b == 0:
        raise ValueError("除数不能为0")
    return a / b

@mcp.tool()
def power(base: int, exponent: int) -> int:
    """
    计算幂运算 (base ^ exponent)
    """
    return base ** exponent

# ============ 启动服务 ============
if __name__ == '__main__':
    mcp.run(transport='sse')