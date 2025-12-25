import sqlite3
import pandas as pd
import os
import logging
import sys
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Configuración de Logging para el servidor de datos
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] SQL_LOG: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
sql_logger = logging.getLogger("gpu-db-query")

# Carga variables desde .env si existe
load_dotenv()

# Configuración de BD
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///gpu_database.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")

mcp = FastMCP("GPU_Intelligence_Server")


def query_db(sql: str, params=None):
    """Ejecuta una consulta SQL y registra la query exacta."""
    if params is None:
        params = []

    # LOG DE LA CONSULTA
    sql_logger.info(f"EJECUTANDO: {sql}")
    sql_logger.info(f"PARÁMETROS: {params}")

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)


@mcp.tool()
def find_best_value_gpus(metric: str = "price_per_vram_gb", limit: int = 5):
    """Identifica GPUs con mejor relación valor/precio."""
    if metric == "performance_per_euro_score":
        table, order_col, direction = (
            "gold_gpu_price_performance",
            "performance_per_euro_score",
            "DESC",
        )
    else:
        table, order_col, direction = "gpu_value_analysis", "price_per_vram_gb", "ASC"

    sql = f"SELECT * FROM {table} ORDER BY {order_col} {direction} LIMIT ?"
    return query_db(sql, params=(limit,)).to_dict(orient="records")


@mcp.tool()
def get_gpu_technical_specs(model_name: str):
    """Obtiene ficha técnica de la vista gpu_technical_sheet."""
    sql = "SELECT * FROM gpu_technical_sheet WHERE full_model_name LIKE ?"
    return query_db(sql, params=(f"%{model_name}%",)).to_dict(orient="records")


@mcp.tool()
def check_market_prices(model_keyword: str = None):
    """Consulta precios actuales y stock."""
    sql = "SELECT * FROM current_gpu_prices"
    params = []
    if model_keyword:
        sql += " WHERE model_suffix LIKE ? OR chip_id LIKE ?"
        params = [f"%{model_keyword}%", f"%{model_keyword}%"]

    return query_db(sql, params=params).to_dict(orient="records")


if __name__ == "__main__":
    mcp.run()
