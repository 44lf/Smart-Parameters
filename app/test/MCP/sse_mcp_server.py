import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sse-mcp-server")

app = FastAPI(title="SSE MCP Server")

# 存储活动会话和工具状态
active_sessions = {}
tool_results = {}

# MCP 工具定义
MCP_TOOLS = {
    "query_health_data": {
        "name": "query_health_data",
        "description": "查询健康数据",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "metric": {"type": "string"}
            },
            "required": ["user_id"]
        }
    },
    "analyze_health_risk": {
        "name": "analyze_health_risk",
        "description": "分析健康风险",
        "parameters": {
            "type": "object",
            "properties": {
                "age": {"type": "number"},
                "bmi": {"type": "number"},
                "conditions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["age", "bmi"]
        }
    },
    "nrs2002_assessment": {
        "name": "nrs2002_assessment",
        "description": "NRS2002营养风险评估",
        "parameters": {
            "type": "object",
            "properties": {
                "bmi": {"type": "number"},
                "weight_change": {"type": "string"},
                "disease_condition": {"type": "string"},
                "age": {"type": "number"}
            },
            "required": ["bmi", "age"]
        }
    }
}


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]
    session_id: Optional[str] = None


class SessionCreateRequest(BaseModel):
    client_info: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "SSE MCP Server",
        "version": "1.0.0",
        "protocol": "Server-Sent Events",
        "available_tools": list(MCP_TOOLS.keys())
    }


@app.post("/sessions")
async def create_session(request: SessionCreateRequest):
    """创建新的MCP会话"""
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "created_at": datetime.now().isoformat(),
        "client_info": request.client_info or {},
        "last_activity": datetime.now().isoformat()
    }

    logger.info(f"创建新会话: {session_id}")
    return {
        "session_id": session_id,
        "status": "created",
        "tools_available": list(MCP_TOOLS.keys())
    }


@app.get("/sse/{session_id}")
async def sse_endpoint(session_id: str, request: Request):
    """SSE流端点 - 用于接收服务器推送的事件"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    async def event_generator():
        """生成SSE事件"""
        try:
            # 发送初始消息
            yield f"data: {json.dumps({
                'type': 'session_connected',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'message': 'SSE连接已建立'
            })}\n\n"

            # 保持连接活跃，定期发送心跳
            while True:
                if session_id not in active_sessions:
                    break

                # 检查是否有待处理的结果
                if session_id in tool_results and tool_results[session_id]:
                    result = tool_results[session_id].pop(0)
                    yield f"data: {json.dumps(result)}\n\n"

                # 发送心跳（每30秒）
                await asyncio.sleep(30)
                yield f"data: {json.dumps({
                    'type': 'heartbeat',
                    'timestamp': datetime.now().isoformat()
                })}\n\n"

        except asyncio.CancelledError:
            logger.info(f"SSE连接关闭: {session_id}")
        except Exception as e:
            logger.error(f"SSE流错误: {str(e)}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """调用MCP工具"""
    if request.name not in MCP_TOOLS:
        raise HTTPException(status_code=404, detail=f"工具不存在: {request.name}")

    # 验证会话
    session_id = request.session_id
    if session_id and session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    # 如果没有提供session_id，创建一个临时会话
    if not session_id:
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "temporary": True
        }

    # 更新会话活动时间
    active_sessions[session_id]["last_activity"] = datetime.now().isoformat()

    # 异步处理工具调用（模拟耗时操作）
    asyncio.create_task(process_tool_call(session_id, request.name, request.arguments))

    return {
        "session_id": session_id,
        "tool": request.name,
        "status": "processing",
        "message": "工具调用已接收，正在处理..."
    }


async def process_tool_call(session_id: str, tool_name: str, arguments: Dict[str, Any]):
    """异步处理工具调用"""
    try:
        # 模拟处理时间
        await asyncio.sleep(1)

        # 处理不同的工具
        if tool_name == "query_health_data":
            result = await handle_health_query(arguments)
        elif tool_name == "analyze_health_risk":
            result = await handle_risk_analysis(arguments)
        elif tool_name == "nrs2002_assessment":
            result = await handle_nrs2002_assessment(arguments)
        else:
            result = {"error": f"未知工具: {tool_name}"}

        # 将结果添加到会话的结果队列
        if session_id not in tool_results:
            tool_results[session_id] = []

        tool_results[session_id].append({
            "type": "tool_result",
            "tool": tool_name,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "result": result
        })

        logger.info(f"工具调用完成: {tool_name} for session {session_id}")

    except Exception as e:
        logger.error(f"工具处理错误: {str(e)}")

        # 发送错误结果
        if session_id not in tool_results:
            tool_results[session_id] = []

        tool_results[session_id].append({
            "type": "tool_error",
            "tool": tool_name,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        })


async def handle_health_query(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理健康数据查询"""
    user_id = arguments.get("user_id", "unknown")
    metric = arguments.get("metric", "all")

    # 模拟健康数据
    health_data = {
        "user_id": user_id,
        "metrics": {
            "bmi": 19.2,
            "blood_pressure": "120/80",
            "heart_rate": 72,
            "weight": 62.5,
            "height": 165
        },
        "last_checkup": "2024-01-15T14:20:00Z"
    }

    if metric != "all":
        health_data["requested_metric"] = metric
        health_data["value"] = health_data["metrics"].get(metric, "N/A")

    return health_data


async def handle_risk_analysis(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理健康风险分析"""
    age = arguments.get("age", 0)
    bmi = arguments.get("bmi", 0)
    conditions = arguments.get("conditions", [])

    # 风险评估逻辑
    risk_score = (age * 0.1) + ((bmi - 18.5) * 0.5 if bmi < 18.5 else 0)

    if "diabetes" in conditions:
        risk_score += 0.3
    if "hypertension" in conditions:
        risk_score += 0.2
    if "heart_disease" in conditions:
        risk_score += 0.4

    risk_level = "低风险" if risk_score < 0.5 else "中风险" if risk_score < 1.0 else "高风险"

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "factors": {
            "age_contribution": round(age * 0.1, 2),
            "bmi_contribution": round((bmi - 18.5) * 0.5 if bmi < 18.5 else 0, 2),
            "conditions_contribution": len(conditions) * 0.1
        },
        "recommendations": [
            "定期监测健康指标",
            "保持均衡饮食",
            "适当运动",
            "定期体检"
        ]
    }


async def handle_nrs2002_assessment(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理NRS2002营养风险评估"""
    bmi = arguments.get("bmi", 0)
    age = arguments.get("age", 0)
    weight_change = arguments.get("weight_change", "")
    disease_condition = arguments.get("disease_condition", "")

    # NRS2002评分逻辑
    # 1. 营养状况评分
    nutritional_score = 0
    if bmi < 18.5:
        nutritional_score = 3
    elif bmi < 20.5:
        nutritional_score = 1

    # 2. 疾病严重度评分
    disease_score = 0
    if "重症" in disease_condition or "ICU" in disease_condition:
        disease_score = 3
    elif "中等" in disease_condition:
        disease_score = 2
    elif "轻度" in disease_condition:
        disease_score = 1

    # 3. 年龄评分
    age_score = 1 if age >= 70 else 0

    # 总分
    total_score = nutritional_score + disease_score + age_score

    # 风险等级
    if total_score >= 3:
        risk_level = "高风险"
    elif total_score >= 1:
        risk_level = "中风险"
    else:
        risk_level = "低风险"

    return {
        "assessment": "NRS2002营养风险评估",
        "scores": {
            "nutritional_score": nutritional_score,
            "disease_score": disease_score,
            "age_score": age_score,
            "total_score": total_score
        },
        "risk_level": risk_level,
        "interpretation": f"总分{total_score}分，{risk_level}",
        "recommendations": [
            "定期监测营养指标",
            "根据评分调整营养支持方案",
            "定期复查体重和BMI"
        ]
    }


@app.get("/tools")
async def list_tools():
    """列出所有可用工具"""
    return {
        "tools": MCP_TOOLS,
        "count": len(MCP_TOOLS)
    }


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """获取会话信息"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    return active_sessions[session_id]


@app.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    """关闭会话"""
    if session_id in active_sessions:
        del active_sessions[session_id]
    if session_id in tool_results:
        del tool_results[session_id]

    return {"status": "closed", "session_id": session_id}


# 定期清理过期会话
async def cleanup_expired_sessions():
    """定期清理过期会话"""
    while True:
        await asyncio.sleep(300)  # 每5分钟清理一次

        now = datetime.now()
        expired_sessions = []

        for session_id, session_data in active_sessions.items():
            last_activity = datetime.fromisoformat(session_data["last_activity"])
            if (now - last_activity).total_seconds() > 1800:  # 30分钟无活动
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del active_sessions[session_id]
            if session_id in tool_results:
                del tool_results[session_id]
            logger.info(f"清理过期会话: {session_id}")


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    # 启动会话清理任务
    asyncio.create_task(cleanup_expired_sessions())
    logger.info("SSE MCP服务器启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("SSE MCP服务器关闭")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8500,
        log_level="info"
    )

    