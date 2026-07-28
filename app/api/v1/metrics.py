import asyncio
import json
import psutil
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Mock workflow data for streaming
workflow_executions = {"success": 85, "failed": 15}
active_agents = 24
total_executions = 12403

@router.websocket("/metrics/live")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # 1. System Memory (psutil)
            memory_info = psutil.virtual_memory()
            memory_gb = round(memory_info.used / (1024 ** 3), 1)

            # 2. Avg Latency (Simulated random jitter between 90ms and 150ms)
            import random
            latency_ms = random.randint(90, 150)
            
            # Update running mock totals
            global total_executions
            total_executions += random.randint(0, 5)
            
            metrics = {
                "activeAgents": active_agents,
                "memoryGb": memory_gb,
                "latencyMs": latency_ms,
                "totalExecutions": total_executions,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            await websocket.send_text(json.dumps(metrics))
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
