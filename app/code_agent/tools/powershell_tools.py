from app.code_agent.utils.mcp import create_mcp_stdio_client

async def get_stdio_powershell_tools():
    params={
        'command':'python',
        'args':[
            # "rD:\\sd14\\ai-agent\\app\\code_agent\\mcp\\powershell_tools.py"
            r"E:\\Ai_Agent\\app\\code_agent\\mcp\\powershell_tools.py"
        ]
    }

    client,tools=await create_mcp_stdio_client('powershell_tools',params)

    return tools