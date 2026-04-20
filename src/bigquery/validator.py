"""
Validador de SQL: garantiza que solo se ejecuten queries de lectura (SELECT).
"""

import re
from src.utils.logger import get_logger

logger = get_logger(__name__)

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
    "ALTER", "TRUNCATE", "MERGE", "REPLACE", "CALL",
    "GRANT", "REVOKE", "EXECUTE",
]


class SQLValidator:
    def validate(self, sql: str):
        """
        Valida que la SQL sea segura para ejecutar.

        Args:
            sql: Query SQL generada por el LLM.

        Raises:
            ValueError: Si la query contiene operaciones no permitidas.
        """
        sql_upper = sql.upper()

        # Comprobación de palabras clave destructivas
        for keyword in FORBIDDEN_KEYWORDS:
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, sql_upper):
                raise ValueError(
                    f"⛔ Query rechazada: contiene la operación '{keyword}', "
                    "solo se permiten sentencias SELECT."
                )

        # Debe empezar con SELECT (ignorando comentarios y espacios)
        clean_sql = re.sub(r"--[^\n]*", "", sql_upper)  # eliminar comentarios
        clean_sql = re.sub(r"/\*.*?\*/", "", clean_sql, flags=re.DOTALL)
        clean_sql = clean_sql.strip()

        if not clean_sql.startswith("SELECT") and not clean_sql.startswith("WITH"):
            raise ValueError(
                "⛔ Query rechazada: debe comenzar con SELECT o WITH."
            )

        logger.info("✅ SQL validada correctamente.")
