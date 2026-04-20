"""
Módulo de conversión de lenguaje natural a SQL usando la API de Claude.
"""

import os
import anthropic
import pandas as pd
from src.utils.logger import get_logger
from src.utils.schema_loader import load_schema

logger = get_logger(__name__)

SYSTEM_PROMPT = """Eres un experto en SQL y BigQuery. Tu tarea es convertir preguntas en lenguaje natural a queries SQL válidas para Google BigQuery.

Reglas estrictas:
1. Genera ÚNICAMENTE la query SQL, sin explicaciones ni bloques de código markdown.
2. Usa solo sentencias SELECT. Nunca generes INSERT, UPDATE, DELETE, DROP, CREATE, ALTER o cualquier sentencia que modifique datos.
3. Usa el formato correcto de BigQuery: `proyecto.dataset.tabla`.
4. Si la pregunta es ambigua, elige la interpretación más razonable.
5. Añade LIMIT 1000 si la query no tiene límite explícito.

Esquema de tablas disponibles:
{schema}
"""

CHART_TYPE_PROMPT = """Dada esta pregunta del usuario: "{question}"
Y este DataFrame con columnas: {columns}

Responde ÚNICAMENTE con una de estas opciones (sin explicación):
- bar
- line
- pie
- scatter
- hist
"""


class NLToSQL:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.schema = load_schema()

    def generate(self, question: str) -> str:
        """Convierte una pregunta en lenguaje natural a SQL para BigQuery."""
        system = SYSTEM_PROMPT.format(schema=self.schema)

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": question}],
        )

        sql = message.content[0].text.strip()
        # Limpiar posibles bloques markdown que el modelo pueda añadir
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql

    def suggest_chart_title(self, question: str) -> str:
        """Genera un título descriptivo para el gráfico basado en la pregunta."""
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=64,
            messages=[
                {
                    "role": "user",
                    "content": f'Genera un título corto (máximo 8 palabras) para un gráfico que responde a: "{question}". Solo el título, sin comillas.',
                }
            ],
        )
        return message.content[0].text.strip()

    def suggest_chart_type(self, question: str, df: pd.DataFrame) -> str:
        """Decide el tipo de gráfico más adecuado según la pregunta y los datos."""
        columns = list(df.columns)
        prompt = CHART_TYPE_PROMPT.format(question=question, columns=columns)

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16,
            messages=[{"role": "user", "content": prompt}],
        )

        chart_type = message.content[0].text.strip().lower()
        valid_types = {"bar", "line", "pie", "scatter", "hist"}
        return chart_type if chart_type in valid_types else "bar"
