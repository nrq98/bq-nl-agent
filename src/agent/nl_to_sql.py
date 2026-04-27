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

CHART_TYPE_PROMPT = """Eres un experto en visualización de datos. Elige el tipo de gráfico más adecuado.

Pregunta del usuario: "{question}"

Descripción del DataFrame resultante:
- Filas: {n_rows}
- Columnas:
{col_descriptions}

Reglas:
- line: si hay una columna temporal/fecha o la pregunta implica evolución en el tiempo
- pie: si hay una columna categórica con ≤8 valores únicos y una columna numérica, y la pregunta pide distribución/proporción
- scatter: si hay ≥2 columnas numéricas y la pregunta implica correlación o comparación directa entre magnitudes
- hist: si hay una sola columna numérica y la pregunta pide distribución de frecuencias
- bar: en cualquier otro caso (categorías + valores)

Responde ÚNICAMENTE con una de estas palabras (sin explicación): bar, line, pie, scatter, hist
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
        prompt = CHART_TYPE_PROMPT.format(
            question=question,
            n_rows=len(df),
            col_descriptions=self._describe_columns(df),
        )
        response = self.client.models.generate_content(model=MODEL, contents=prompt)
        chart_type = response.text.strip().lower()
        valid_types = {"bar", "line", "pie", "scatter", "hist"}
        return chart_type if chart_type in valid_types else "bar"

    @staticmethod
    def _describe_columns(df: pd.DataFrame) -> str:
        lines = []
        for col in df.columns:
            dtype = df[col].dtype
            n_unique = df[col].nunique()
            if pd.api.types.is_datetime64_any_dtype(dtype):
                kind = "fecha/tiempo"
            elif pd.api.types.is_numeric_dtype(dtype):
                kind = f"numérica (min={df[col].min():.4g}, max={df[col].max():.4g})"
            else:
                kind = "categórica"
                if n_unique <= 10:
                    samples = df[col].dropna().unique()[:10].tolist()
                    kind += f", valores: {samples}"
            lines.append(f"  - {col}: {kind}, {n_unique} valores únicos")
        return "\n".join(lines)
