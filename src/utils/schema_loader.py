"""
Carga el esquema de tablas de BigQuery desde un fichero YAML o JSON.
Este esquema se inyecta en el prompt del LLM para que genere SQL correcta.
"""

import os
import json
import yaml
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_PATH = Path(os.environ.get("BQ_SCHEMA_PATH", "schema.yaml"))


def load_schema() -> str:
    """
    Carga y devuelve el esquema como string para incluirlo en el prompt.

    Returns:
        Esquema formateado como texto.

    Raises:
        FileNotFoundError: Si no se encuentra el fichero de esquema.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el fichero de esquema en '{SCHEMA_PATH}'. "
            "Crea un schema.yaml con la estructura de tus tablas de BigQuery. "
            "Consulta schema.example.yaml como referencia."
        )

    suffix = SCHEMA_PATH.suffix.lower()

    if suffix in (".yaml", ".yml"):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)

    elif suffix == ".json":
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)

    else:
        # Fallback: leer como texto plano
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            return f.read()
