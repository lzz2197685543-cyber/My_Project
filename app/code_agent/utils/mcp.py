from langchain_mcp_adapters.client import MultiServerMCPClient


async def create_mcp_stdio_client(name,params):
    config={
        name:{
            'transport':'stdio',
            **params,
        }
    }
    # 只打印连接方式。params 里现在带了完整 env（为了把 PATHEXT 传给 MCP 服务），
    # 整个打出来会把几 KB 环境变量刷到终端里。
    print({name: {k: v for k, v in config[name].items() if k != 'env'}})
    client=MultiServerMCPClient(config)

    tools=await client.get_tools()

    return client,tools