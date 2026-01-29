import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sse-mcp-client")


class SSEMCPClient:
    """SSE MCP客户端"""

    def __init__(self, base_url: str = "http://localhost:8500"):
        self.base_url = base_url
        self.session_id = None
        self.sse_task = None
        self.message_handlers = {}
        self.session = None

    async def connect(self, client_info: Dict[str, Any] = None) -> bool:
        """连接到MCP服务器并创建会话"""
        try:
            self.session = aiohttp.ClientSession()

            # 创建会话
            async with self.session.post(f"{self.base_url}/sessions",
                                         json={"client_info": client_info or {}}) as response:
                if response.status == 200:
                    data = await response.json()
                    self.session_id = data["session_id"]
                    logger.info(f"✅ 会话创建成功: {self.session_id}")
                    return True
                else:
                    logger.error(f"❌ 会话创建失败: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ 连接失败: {str(e)}")
            return False

    async def listen_for_events(self, message_handler: Callable[[Dict[str, Any]], None]):
        """监听服务器推送的事件"""
        if not self.session_id:
            raise Exception("未创建会话，请先调用connect()")

        self.message_handlers["default"] = message_handler

        try:
            async with self.session.get(f"{self.base_url}/sse/{self.session_id}") as response:
                if response.status == 200:
                    logger.info("✅ 开始监听SSE事件流")

                    # 处理SSE流
                    async for line in response.content:
                        line = line.decode('utf-8').strip()

                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                                await self._handle_message(data)
                            except json.JSONDecodeError:
                                logger.warning(f"无法解析SSE数据: {line}")

                else:
                    logger.error(f"❌ SSE连接失败: {response.status}")

        except Exception as e:
            logger.error(f"❌ SSE监听错误: {str(e)}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具"""
        if not self.session_id:
            raise Exception("未创建会话，请先调用connect()")

        try:
            async with self.session.post(f"{self.base_url}/tools/call", json={
                "name": tool_name,
                "arguments": arguments,
                "session_id": self.session_id
            }) as response:

                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            return {"error": str(e)}

    async def _handle_message(self, message: Dict[str, Any]):
        """处理收到的消息"""
        message_type = message.get("type")

        # 调用对应的处理器
        for handler in self.message_handlers.values():
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"消息处理错误: {str(e)}")

        # 特定类型的日志
        if message_type == "session_connected":
            logger.info("🔗 SSE连接已建立")
        elif message_type == "heartbeat":
            logger.debug("💓 收到心跳")
        elif message_type == "tool_result":
            logger.info(f"🛠️ 收到工具结果: {message.get('tool')}")
        elif message_type == "tool_error":
            logger.error(f"❌ 工具执行错误: {message.get('error')}")

    def add_message_handler(self, name: str, handler: Callable[[Dict[str, Any]], None]):
        """添加消息处理器"""
        self.message_handlers[name] = handler

    def remove_message_handler(self, name: str):
        """移除消息处理器"""
        if name in self.message_handlers:
            del self.message_handlers[name]

    async def list_tools(self) -> Dict[str, Any]:
        """列出可用工具"""
        try:
            async with self.session.get(f"{self.base_url}/tools") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        if not self.session_id:
            return {"error": "未创建会话"}

        try:
            async with self.session.get(f"{self.base_url}/sessions/{self.session_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def close(self):
        """关闭连接"""
        if self.session_id:
            try:
                async with self.session.delete(f"{self.base_url}/sessions/{self.session_id}") as response:
                    if response.status == 200:
                        logger.info(f"✅ 会话已关闭: {self.session_id}")
            except Exception as e:
                logger.error(f"关闭会话错误: {str(e)}")

        if self.session:
            await self.session.close()
            logger.info("✅ 客户端连接已关闭")


async def interactive_demo():
    """交互式演示"""
    client = SSEMCPClient()

    # 定义消息处理器
    async def handle_message(message: Dict[str, Any]):
        message_type = message.get("type")

        if message_type == "tool_result":
            print(f"\n🎉 工具调用结果:")
            print(f"   工具: {message.get('tool')}")
            print(f"   结果: {json.dumps(message.get('result'), indent=2, ensure_ascii=False)}")

        elif message_type == "tool_error":
            print(f"\n❌ 工具调用错误:")
            print(f"   错误: {message.get('error')}")

        elif message_type == "session_connected":
            print(f"\n🔗 服务器连接成功")

        elif message_type == "heartbeat":
            print(f"💓 心跳接收时间: {message.get('timestamp')}")

    # 连接服务器
    if not await client.connect({"name": "Demo Client", "version": "1.0.0"}):
        return

    # 启动SSE监听（在后台运行）
    listen_task = asyncio.create_task(client.listen_for_events(handle_message))

    try:
        # 等待连接建立
        await asyncio.sleep(1)

        # 列出可用工具
        print("🛠️  获取可用工具...")
        tools_result = await client.list_tools()
        if "tools" in tools_result:
            print("可用工具:")
            for tool_name, tool_info in tools_result["tools"].items():
                print(f"  - {tool_name}: {tool_info['description']}")

        while True:
            print("\n" + "=" * 50)
            print("SSE MCP客户端 - 交互模式")
            print("1. 查询健康数据")
            print("2. 分析健康风险")
            print("3. NRS2002营养评估")
            print("4. 查看会话信息")
            print("5. 退出")

            choice = input("请选择操作 (1-5): ").strip()

            if choice == "1":
                user_id = input("用户ID: ").strip() or "demo_user"
                metric = input("指标 (默认all): ").strip() or "all"

                print("🔍 查询健康数据...")
                result = await client.call_tool("query_health_data", {
                    "user_id": user_id,
                    "metric": metric
                })
                print(f"调用状态: {result.get('status', 'unknown')}")

            elif choice == "2":
                try:
                    age = int(input("年龄: ").strip())
                    bmi = float(input("BMI: ").strip())
                    conditions_input = input("健康状况 (逗号分隔): ").strip()
                    conditions = [c.strip() for c in conditions_input.split(",")] if conditions_input else []

                    print("📊 分析健康风险...")
                    result = await client.call_tool("analyze_health_risk", {
                        "age": age,
                        "bmi": bmi,
                        "conditions": conditions
                    })
                    print(f"调用状态: {result.get('status', 'unknown')}")

                except ValueError:
                    print("❌ 输入格式错误")

            elif choice == "3":
                try:
                    age = int(input("年龄: ").strip())
                    bmi = float(input("BMI: ").strip())
                    weight_change = input("体重变化: ").strip() or "近3个月体重下降5%"
                    disease_condition = input("疾病状况: ").strip() or "2型糖尿病"

                    print("🍎 NRS2002营养评估...")
                    result = await client.call_tool("nrs2002_assessment", {
                        "age": age,
                        "bmi": bmi,
                        "weight_change": weight_change,
                        "disease_condition": disease_condition
                    })
                    print(f"调用状态: {result.get('status', 'unknown')}")

                except ValueError:
                    print("❌ 输入格式错误")

            elif choice == "4":
                session_info = await client.get_session_info()
                print("📋 会话信息:")
                print(json.dumps(session_info, indent=2, ensure_ascii=False))

            elif choice == "5":
                break
            else:
                print("❌ 无效选择")

            # 等待结果返回
            await asyncio.sleep(2)

    except KeyboardInterrupt:
        print("\n退出交互模式")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
    finally:
        listen_task.cancel()
        await client.close()


async def automated_demo():
    """自动化演示"""
    client = SSEMCPClient()

    # 消息收集器
    messages = []

    async def collect_messages(message: Dict[str, Any]):
        messages.append(message)
        if message.get("type") == "tool_result":
            print(f"✅ 收到 {message.get('tool')} 的结果")

    # 连接服务器
    if not await client.connect():
        return

    # 启动监听
    listen_task = asyncio.create_task(client.listen_for_events(collect_messages))

    try:
        print("🚀 开始自动化演示")

        # 等待连接建立
        await asyncio.sleep(1)

        # 1. 查询健康数据
        print("\n1. 查询健康数据...")
        await client.call_tool("query_health_data", {
            "user_id": "test_patient_001",
            "metric": "bmi"
        })
        await asyncio.sleep(2)

        # 2. 分析健康风险
        print("2. 分析健康风险...")
        await client.call_tool("analyze_health_risk", {
            "age": 65,
            "bmi": 19.2,
            "conditions": ["diabetes", "hypertension"]
        })
        await asyncio.sleep(2)

        # 3. NRS2002评估
        print("3. NRS2002营养评估...")
        await client.call_tool("nrs2002_assessment", {
            "age": 72,
            "bmi": 17.8,
            "weight_change": "近2个月体重下降12%",
            "disease_condition": "急性脑中风"
        })
        await asyncio.sleep(2)

        # 显示收集到的结果
        print("\n📊 演示结果汇总:")
        for msg in messages:
            if msg.get("type") == "tool_result":
                result = msg.get("result", {})
                print(f"- {msg.get('tool')}: {result.get('risk_level', 'N/A') if 'risk_level' in result else '成功'}")

        print("\n🎉 演示完成")

    except Exception as e:
        print(f"❌ 演示错误: {str(e)}")
    finally:
        listen_task.cancel()
        await client.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        asyncio.run(automated_demo())
    else:
        print("🚀 启动SSE MCP客户端 - 交互模式")
        asyncio.run(interactive_demo())