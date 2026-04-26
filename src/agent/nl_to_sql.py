"""
Módulo de conversión de lenguaje natural a SQL usando la API de Google Gemini.
"""

import os
from google import genai
from google.genai import types
import pandas as pd
from src.utils.logger import get_logger
from src.utils.schema_loader import load_schema

logger = get_logger(__name__)

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")

SYSTEM_PROMPT = """Eres un experto en SQL. Tu tarea es convertir preguntas en lenguaje natural a queries SQL válidas.

Reglas estrictas:
1. Genera ÚNICAMENTE la query SQL, sin explicaciones ni bloques de código markdown.
2. Usa solo sentencias SELECT. Nunca generes INSERT, UPDATE, DELETE, DROP, CREATE, ALTER o cualquier sentencia que modifique datos.
3. Usa el nombre de tabla exacto tal como aparece en el esquema.
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
        self.client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self.schema = load_schema()
        self.system_instruction = SYSTEM_PROMPT.format(schema=self.schema)

    def generate(self, question: str) -> str:
        """Convierte una pregunta en lenguaje natural a SQL."""
        response = self.client.models.generate_content(
            model=MODEL,
            config=types.GenerateContentConfig(system_instruction=self.system_instruction),
            contents=question,
        )
        sql = response.text.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql

    def suggest_chart_title(self, question: str) -> str:
        """Genera un título descriptivo para el gráfico basado en la pregunta."""
        prompt = f'Genera un título corto (máximo 8 palabras) para un gráfico que responde a: "{question}". Solo el título, sin comillas.'
        response = self.client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()

    def suggest_chart_type(self, question: str, df: pd.DataFrame) -> str:
        """Decide el tipo de gráfico más adecuado según la pregunta y los datos."""
        prompt = CHART_TYPE_PROMPT.format(question=question, columns=list(df.columns))
        response = self.client.models.generate_content(model=MODEL, contents=prompt)
        chart_type = response.text.strip().lower()
        valid_types = {"bar", "line", "pie", "scatter", "hist"}
        return chart_type if chart_type in valid_types else "bar"
