import aiohttp
import asyncio
from typing import Dict, Any


class HTTPMCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None

    async def connect(self):
        self.session = aiohttp.ClientSession()

    async def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        async with self.session.post(f"{self.base_url}/mcp", json={
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }) as response:
            return await response.json()

    async def list_tools(self) -> Dict:
        async with self.session.post(f"{self.base_url}/mcp", json={
            "method": "tools/list",
            "params": {}
        }) as response:
            return await response.json()

    async def close(self):
        if self.session:
            await self.session.close()


# 使用示例
async def main():
    client = HTTPMCPClient("http://localhost:7000")
    await client.connect()

    try:
        # 列出可用工具
        tools = await client.list_tools()
        print("可用工具:", tools)

        # 调用工具
        result = await client.call_tool("analyze_health_risk", {
            "age": 65,
            "bmi": 19.2,
            "conditions": ["diabetes"]
        })
        print("分析结果:", result)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())