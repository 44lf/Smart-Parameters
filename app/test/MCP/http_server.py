from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any

app = FastAPI(title="MCP HTTP Server")

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}

@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest):
    """MCP over HTTP"""
    if request.method == "tools/list":
        return await list_tools()
    elif request.method == "tools/call":
        return await call_tool(request.params)
    else:
        raise HTTPException(status_code=404, detail="Method not found")

async def list_tools():
    return {
        "tools": [
            {
                "name": "analyze_health_risk",
                "description": "分析健康风险",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "number"},
                        "bmi": {"type": "number"},
                        "conditions": {"type": "array"}
                    }
                }
            }
        ]
    }

async def call_tool(params: Dict):
    if params["name"] == "analyze_health_risk":
        # 模拟健康风险分析
        risk_score = params["arguments"]["age"] * 0.1 + params["arguments"]["bmi"] * 0.2
        return {
            "content": [{
                "type": "text",
                "text": f"风险评分: {risk_score:.2f}"
            }]
        }
    raise HTTPException(status_code=404, detail="Tool not found")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7000)