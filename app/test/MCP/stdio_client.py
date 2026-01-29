import asyncio
import json
import subprocess
from typing import Dict, Any, Optional


class StdioMCPClient:
    def __init__(self, server_command: list):
        self.server_command = server_command
        self.process: Optional[subprocess.Process] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self.stderr_reader: Optional[asyncio.StreamReader] = None  # 捕获服务端错误日志

    # 修改 stdio_client.py 中的 _read_stderr 方法
    async def _read_stderr(self):
        """持续读取服务端的stderr输出（适配Windows GBK编码）"""
        assert self.stderr_reader is not None, "服务端未启动"
        while True:
            line = await self.stderr_reader.readline()
            if not line:
                break  # 服务端stderr关闭，退出循环

            # 关键修复：先用GBK解码（Windows默认），失败时用UTF-8兼容处理
            try:
                log_str = line.decode("gbk").strip()  # Windows控制台默认GBK编码
            except UnicodeDecodeError:
                log_str = line.decode("utf-8", errors="replace").strip()  # 兼容UTF-8，无法识别的字符用�代替

            # 打印服务端日志
            print(f"[服务端日志] {log_str}")

    async def connect(self, timeout: int = 5):
        """启动服务端进程并建立连接（增加超时和stderr捕获）"""
        try:
            # 启动服务端进程，绑定stdin/stdout/stderr
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=False  # 以字节流模式处理（避免编码问题）
            )

            # 绑定流对象
            self.reader = self.process.stdout
            self.writer = self.process.stdin
            self.stderr_reader = self.process.stderr

            # 启动独立任务读取服务端stderr（不阻塞主逻辑）
            asyncio.create_task(self._read_stderr())

            # 等待服务端启动（超时检测）
            await asyncio.sleep(0.5)
            if self.process.returncode is not None:
                raise RuntimeError(f"服务端启动失败，退出码：{self.process.returncode}")

            print("客户端已成功连接服务端")

        except Exception as e:
            raise ConnectionError(f"连接服务端失败：{str(e)}") from e

    async def call_tool(self, tool_name: str, arguments: Dict, timeout: int = 10) -> Dict:
        """调用远程工具（增加超时和错误处理）"""
        if not self.writer or not self.reader:
            raise ConnectionError("客户端未连接服务端，请先调用 connect()")

        # 1. 构造JSON-RPC请求
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1  # 固定ID，简化逻辑（生产环境可动态生成）
        }

        try:
            # 2. 发送请求（加换行符，服务端按行读取）
            request_json = json.dumps(request, ensure_ascii=False) + "\n"
            self.writer.write(request_json.encode("utf-8"))
            await self.writer.drain()  # 确保数据写入管道
            print(f"已发送请求：{request_json.strip()}")

            # 3. 读取响应（超时控制）
            response_line = await asyncio.wait_for(
                self.reader.readline(),  # 按行读取响应
                timeout=timeout
            )

            # 4. 处理空响应
            if not response_line:
                raise RuntimeError("服务端未返回响应（可能已崩溃）")

            # 5. 解析JSON响应
            response_str = response_line.decode("utf-8").strip()
            print(f"收到响应：{response_str}")
            return json.loads(response_str)

        except asyncio.TimeoutError:
            raise TimeoutError(f"调用工具超时（{timeout}秒内未收到响应）")
        except json.JSONDecodeError as e:
            raise ValueError(f"服务端响应不是有效JSON：{response_str}（错误：{str(e)}）") from e
        except Exception as e:
            raise RuntimeError(f"调用工具失败：{str(e)}") from e

    async def close(self):
        """优雅关闭连接"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        if self.process and self.process.returncode is None:
            self.process.terminate()
            await self.process.wait()
        print("客户端已关闭连接")


# 使用示例
async def main():
    # 启动服务端的命令（确保 stdio_server.py 在同一目录）
    server_cmd = ["python", "stdio_server.py"]
    client = StdioMCPClient(server_command=server_cmd)

    try:
        # 1. 连接服务端
        await client.connect()

        # 2. 调用工具（示例：查询user123的BMI）
        result = await client.call_tool(
            tool_name="query_health_data",
            arguments={"user_id": "user123", "metric": "bmi"}
        )

        # 3. 打印结果
        print("\n=== 工具调用结果 ===")
        if "result" in result:
            print(json.dumps(result["result"], indent=2, ensure_ascii=False))
        elif "error" in result:
            print(f"调用失败：{result['error']['message']}")

    except Exception as e:
        print(f"\n❌ 客户端异常：{str(e)}")
    finally:
        # 4. 关闭连接
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())