import os
import json
import time
import logging
import sys
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import uvicorn
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gpu-mcp-agent")

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")


def build_llm_client_and_model():
    if LLM_PROVIDER == "ollama":
        model_name = os.getenv("OLLAMA_MODEL", "llama3.1")
        return OpenAI(api_key=OLLAMA_API_KEY, base_url=OLLAMA_BASE_URL), model_name
    if LLM_PROVIDER != "openai":
        logger.warning("LLM_PROVIDER no reconocido, usando OpenAI por defecto.")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    if OPENAI_BASE_URL:
        return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL), model_name
    return OpenAI(api_key=OPENAI_API_KEY), model_name


client, MODEL_NAME = build_llm_client_and_model()

app = FastAPI(title="GPU Agent Standard API")

# ============================================================================
# SYSTEM PROMPT: LA MENTE DEL ANALISTA DE BI
# ============================================================================
SYSTEM_PROMPT = """Eres el 'Senior GPU Business Intelligence Analyst'. Tu objetivo es asesorar sobre compras de hardware basadas estrictamente en datos.

Sigue estas directrices de BI:
1. **Pensamiento Analítico**: No digas "es buena"; di "ofrece un score de valor un 15% superior a la media del segmento".
2. **Formato Estructurado**: Siempre que compares más de 2 productos, utiliza TABLAS Markdown.
3. **KPIs Clave**:
   - VRAM Value (Precio/GB).
   - Performance ROI (Score de potencia/Precio).
   - Eficiencia Energética (TDP vs Potencia).
4. **Contexto de Mercado**: Identifica si una oferta es un 'Sweet Spot' o si el sobrecoste no justifica el rendimiento extra.
5. **Neutralidad**: Eres agnóstico a marcas (NVIDIA/AMD/Intel). Solo te importan los números.

Si no hay datos en la herramienta para una pregunta específica, indícalo claramente en lugar de inventar."""

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
    start_time = time.time()

    # Inyectamos el System Prompt si no está presente para forzar el comportamiento BI
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + request.messages

    # 1. Llamada inicial (Detección de intención)
    response = client.chat.completions.create(
        model=MODEL_NAME, messages=messages, tools=tools_definition, tool_choice="auto"
    )

    msg = response.choices[0].message

    # 2. Loop de ejecución de herramientas
    if msg.tool_calls:
        messages.append(msg)
        for tc in msg.tool_calls:
            f_name, args = tc.function.name, json.loads(tc.function.arguments)
            logger.info(f"BI Analysis Triggered: {f_name} | Params: {args}")

            if f_name == "get_gpu_technical_specs":
                res = get_gpu_technical_specs(**args)
            elif f_name == "find_best_value_gpus":
                res = find_best_value_gpus(**args)
            elif f_name == "check_market_prices":
                res = check_market_prices(**args)
            else:
                res = {"error": "tool_not_found"}

            messages.append(
                {
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "name": f_name,
                    "content": json.dumps(res),
                }
            )

        # 3. Respuesta final sintetizada con mentalidad BI
        final_response = client.chat.completions.create(
            model=MODEL_NAME, messages=messages
        )
        logger.info(f"BI Insight delivered in {round(time.time() - start_time, 2)}s")
        return final_response.model_dump()

    return response.model_dump()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
