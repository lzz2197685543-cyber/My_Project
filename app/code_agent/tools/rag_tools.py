from app.code_agent.utils.mcp import create_mcp_stdio_client

async def get_rag_tools():
    params={
        'command':'python',
        'args':[
            r"D:\\sd14\\ai-agent\\app\\code_agent\\rag\\rag.py"
            # r"E:\\Ai_Agent\\app\\code_agent\\rag\\rag.py"
        ]
    }

    client,tools=await create_mcp_stdio_client('powershell_tools',params)

    return tools