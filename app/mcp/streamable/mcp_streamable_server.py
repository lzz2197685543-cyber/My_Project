from mcp.server.fastmcp import FastMCP

# 创建 MCP 服务器实例
mcp = FastMCP('Math Tools - Streamable HTTP')

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

@mcp.tool()
def factorial(n: int) -> int:
    """
    计算阶乘 (n!)
    """
    if n < 0:
        raise ValueError("阶乘只支持非负整数")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

@mcp.tool()
def fibonacci(n: int) -> list:
    """
    生成前 n 个斐波那契数列
    """
    if n <= 0:
        return []
    if n == 1:
        return [0]
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# ============ 启动服务 ============
if __name__ == '__main__':
    mcp.run(transport='streamable-http')
