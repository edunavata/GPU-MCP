import os
import json
import time
import logging
import sys
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import uvicorn

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gpu-mcp-agent")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="GPU Agent Standard API")

# Importación segura
try:
    from mcp_gpu_server import (
        get_gpu_technical_specs,
        find_best_value_gpus,
        check_market_prices,
    )

    logger.info("Herramientas MCP cargadas correctamente.")
except ImportError as e:
    logger.critical(f"Error de importación: {e}")
    sys.exit(1)

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_gpu_technical_specs",
            "description": "Especificaciones técnicas (VRAM, Cores, TDP).",
            "parameters": {
                "type": "object",
                "properties": {"model_name": {"type": "string"}},
                "required": ["model_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_best_value_gpus",
            "description": "Mejor relación calidad/precio o precio/VRAM.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["price_per_vram_gb", "performance_per_euro_score"],
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_market_prices",
            "description": "Precios actuales y disponibilidad en tiendas.",
            "parameters": {
                "type": "object",
                "properties": {"model_keyword": {"type": "string"}},
            },
        },
    },
]


class ChatRequest(BaseModel):
    model: str = "gpu-analyst-v1"
    messages: list

    class Config:
        extra = "allow"


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "gpu-analyst-v1",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "mcp-system",
            }
        ],
    }


@app.post("/v1/chat/completions")
async def chat_endpoint(request: ChatRequest):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=request.messages,
        tools=tools_definition,
        tool_choice="auto",
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        messages = request.messages + [msg]
        for tc in msg.tool_calls:
            f_name, args = tc.function.name, json.loads(tc.function.arguments)
            logger.info(f"Tool: {f_name} | Args: {args}")

            if f_name == "get_gpu_technical_specs":
                res = get_gpu_technical_specs(**args)
            elif f_name == "find_best_value_gpus":
                res = find_best_value_gpus(**args)
            elif f_name == "check_market_prices":
                res = check_market_prices(**args)
            else:
                res = {"error": "not found"}

            messages.append(
                {
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "name": f_name,
                    "content": json.dumps(res),
                }
            )

        final = client.chat.completions.create(model="gpt-4o", messages=messages)
        return final.model_dump()

    return response.model_dump()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
