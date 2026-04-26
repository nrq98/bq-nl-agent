# BQ NL Agent — Contexto del proyecto

## Descripción

Agente que convierte preguntas en lenguaje natural a queries SQL, las ejecuta sobre un CSV local mediante DuckDB y genera gráficos con Matplotlib. Usa Google Gemini como LLM.

## Flujo de ejecución

```
Pregunta (NL)
    → NLToSQL.generate()       — Gemini genera la SQL
    → SQLValidator.validate()  — bloquea todo lo que no sea SELECT/WITH
    → BigQueryClient.run_query() — DuckDB ejecuta la SQL sobre el CSV
    → NLToSQL.suggest_chart_*() — Gemini elige tipo y título del gráfico
    → Plotter.plot()           — Matplotlib renderiza el gráfico
```

## Estructura de ficheros

```
bq-nl-agent/
├── main.py                        # Punto de entrada (CLI con argparse)
├── schema.yaml                    # Esquema de tablas (cargado en el prompt)
├── schema.example.yaml            # Referencia de esquema
├── requirements.txt               # Dependencias Python
├── .env                           # Variables de entorno (no subir a git)
├── .env.example                   # Plantilla de variables
├── data/
│   └── Datos_Muestra_Hackaton.csv # Datos de reconciliación (separador ;)
└── src/
    ├── agent/
    │   ├── orchestrator.py        # Coordina el flujo completo
    │   └── nl_to_sql.py           # Llama a Gemini para generar SQL y metadatos del gráfico
    ├── bigquery/
    │   ├── client.py              # Carga el CSV con pandas y ejecuta SQL con DuckDB
    │   └── validator.py           # Valida que la SQL solo sea SELECT/WITH
    ├── visualization/
    │   └── plotter.py             # Genera gráficos (bar, line, pie, scatter, hist)
    └── utils/
        ├── schema_loader.py       # Lee schema.yaml e inyecta su contenido en el prompt
        └── logger.py              # Logger con timestamp
```

## Variables de entorno (.env)

| Variable | Obligatoria | Descripción |
|---|---|---|
| `GOOGLE_API_KEY` | Sí | API key de Google AI Studio |
| `GEMINI_MODEL` | No | Modelo Gemini (default: `gemini-2.0-flash-lite`) |
| `CSV_PATH` | No | Ruta al CSV de datos (default: `data/Datos_Muestra_Hackaton.csv`) |
| `BQ_SCHEMA_PATH` | No | Ruta al schema YAML (default: `schema.yaml`) |
| `LOG_LEVEL` | No | Nivel de log: DEBUG / INFO / WARNING / ERROR |

## Tabla de datos: `datos_muestra_hackaton`

Fichero: `data/Datos_Muestra_Hackaton.csv` (separador `;`)

| Columna | Tipo | Descripción |
|---|---|---|
| `ID` | INTEGER | Identificador de la operación |
| `Input` | STRING | Fuente del dato (MARKIT, BBVA, etc.) |
| `Notional_1_CRV_EUR` | FLOAT | Nocional lado 1 en EUR |
| `Notional_2_CRV_EUR` | FLOAT | Nocional lado 2 en EUR |
| `Workflow` | STRING | Estado del flujo de trabajo |
| `Match_status` | STRING | Resultado de la reconciliación (Match, Break…) |
| `Labels` | STRING | Etiquetas adicionales |
| `snapshot_uid` | STRING | UUID del snapshot |
| `part` | INTEGER | Índice de partición del snapshot |
| `snapshot_date` | TIMESTAMP | Fecha/hora del snapshot |
| `process_code` | STRING | Código del proceso de reconciliación |
| `run_id` | INTEGER | ID de la ejecución |
| `recon_date` | TIMESTAMP | Fecha/hora de la reconciliación |

## Dependencias principales

| Paquete | Uso |
|---|---|
| `google-genai` | Cliente Gemini (NL → SQL, tipo de gráfico, título) |
| `duckdb` | Motor SQL sobre DataFrames de pandas |
| `pandas` | Lectura del CSV y manipulación de datos |
| `matplotlib` | Renderizado de gráficos |
| `PyYAML` | Lectura de `schema.yaml` |
| `python-dotenv` | Carga de `.env` al arrancar |

## Uso por línea de comandos

```bash
# Una sola pregunta
python main.py "¿Cuántos registros hay por Match_status?"

# Modo interactivo
python main.py -i

# Guardar gráfico en fichero
python main.py "Distribución de Notional_1 por Input" -o grafico.png

# Solo generar SQL sin ejecutar
python main.py "¿Cuál es el Notional medio?" --dry-run
```

## Notas importantes

- La API key debe generarse en [Google AI Studio](https://aistudio.google.com/app/apikey), no desde Google Cloud Console. Las keys de proyectos corporativos pueden tener cuota 0 en el free tier.
- El nombre de tabla en las queries SQL debe ser exactamente `datos_muestra_hackaton` (tal como aparece en `schema.yaml`).
- El validador de SQL bloquea cualquier sentencia que no sea `SELECT` o `WITH`. No se puede modificar datos.
- `schema.yaml` se inyecta en el system prompt de Gemini en cada arranque; si se modifica, basta con reiniciar el proceso.
