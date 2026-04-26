import os
import duckdb
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)

CSV_PATH = os.environ.get("CSV_PATH", "data/Datos_Muestra_Hackaton.csv")
TABLE_NAME = "datos_muestra_hackaton"

class BigQueryClient:
    def __init__(self):
        logger.info(f"Cargando CSV: {CSV_PATH}")
        df = pd.read_csv(CSV_PATH, sep=";")
        self.conn = duckdb.connect()
        self.conn.register(TABLE_NAME, df)
        logger.info(f"  → Tabla '{TABLE_NAME}': {len(df)} filas, {list(df.columns)}")

    def run_query(self, sql: str) -> pd.DataFrame:
        try:
            result = self.conn.execute(sql).df()
            logger.info(f"Query OK: {len(result)} filas devueltas")
            return result
        except Exception as e:
            logger.error(f"Error ejecutando query: {e}")
            raise RuntimeError(f"Error en query: {e}") from e
