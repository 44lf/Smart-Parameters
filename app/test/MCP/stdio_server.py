import asyncio
import json
import sys
import io
from typing import Dict, Any


class StdioMCPServer:
    def __init__(self):
        # 定义支持的工具（此处示例实现 query_health_data）
        self.supported_tools = {
            "query_health_data": self._query_health_data
        }
        # 可选：将stderr强制设置为UTF-8编码（避免Windows GBK默认编码）
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    async def _query_health_data(self, arguments: Dict) -> Dict:
        """实现健康数据查询工具（示例逻辑）"""
        user_id = arguments.get("user_id")
        metric = arguments.get("metric")

        # 模拟业务逻辑：根据user_id和metric返回数据
        if not user_id or not metric:
            return {
                "success": False,
                "error": "缺少必填参数（user_id 或 metric）"
            }

        # 模拟数据库查询结果
        mock_data = {
            "user123": {"bmi": 22.5, "weight": 65.0, "height": 1.70},
            "user456": {"bmi": 24.1, "weight": 70.0, "height": 1.71}
        }

        if user_id not in mock_data:
            return {"success": False, "error": f"用户 {user_id} 不存在"}
        if metric not in mock_data[user_id]:
            return {"success": False, "error": f"不支持的指标 {metric}"}

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "metric": metric,
                "value": mock_data[user_id][metric],
                "timestamp": "2025-09-28 15:30:00"
            }
        }

    async def _read_request(self) -> Dict:
        """从stdin读取客户端请求（按行读取，JSON格式）"""
        while True:
            # 读取客户端发送的一行数据（strip() 去除换行符）
            line = await asyncio.to_thread(sys.stdin.readline)
            if not line:
                continue  # 忽略空行
            try:
                return json.loads(line.strip())
            except json.JSONDecodeError:
                # 返回格式错误响应
                await self._send_response(
                    id=None,
                    error={"code": -32700, "message": "无效的JSON格式"}
                )

    async def _send_response(self, id: Any, result: Dict = None, error: Dict = None):
        """向stdout发送JSON响应（必须带换行符，客户端用readline读取）"""
        response = {"jsonrpc": "2.0", "id": id}
        if result is not None:
            response["result"] = result
        if error is not None:
            response["error"] = error

        # 序列化为JSON字符串，末尾加换行符（关键：客户端readline依赖换行分隔）
        response_str = json.dumps(response, ensure_ascii=False) + "\n"
        # 写入stdout并强制刷新（避免缓冲区滞留，客户端读不到数据）
        sys.stdout.write(response_str)
        sys.stdout.flush()  # 核心：强制刷新缓冲区

    async def run(self):
        """启动服务端，持续处理客户端请求"""
        print("Stdio MCP 服务端已启动，等待请求...", file=sys.stderr)  # 错误流输出日志，不干扰响应
        try:
            while True:
                # 1. 读取客户端请求
                request = await self._read_request()
                request_id = request.get("id")
                method = request.get("method")
                params = request.get("params", {})

                # 2. 验证请求格式
                if method != "tools/call":
                    await self._send_response(
                        id=request_id,
                        error={"code": -32601, "message": f"不支持的方法：{method}"}
                    )
                    continue
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                if not tool_name:
                    await self._send_response(
                        id=request_id,
                        error={"code": -32602, "message": "缺少工具名称（name）"}
                    )
                    continue

                # 3. 调用工具并返回结果
                if tool_name not in self.supported_tools:
                    await self._send_response(
                        id=request_id,
                        error={"code": -32602, "message": f"不支持的工具：{tool_name}"}
                    )
                    continue
                # 调用工具逻辑
                tool_result = await self.supported_tools[tool_name](tool_args)
                # 发送成功响应
                await self._send_response(id=request_id, result=tool_result)

        except KeyboardInterrupt:
            print("\n服务端收到停止信号，正在退出...", file=sys.stderr)
        except Exception as e:
            print(f"服务端异常：{str(e)}", file=sys.stderr)
        finally:
            sys.stdout.close()
            sys.stdin.close()


if __name__ == "__main__":
    # 启动服务端（异步运行）
    server = StdioMCPServer()
    print("正在监听")
    asyncio.run(server.run())