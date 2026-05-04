# BQ NL Agent — Contexto del proyecto

## Descripción

Agente que convierte preguntas en lenguaje natural a queries SQL, las ejecuta sobre un CSV local mediante DuckDB y genera gráficos con Matplotlib. Usa Google Gemini como LLM.

## Flujo de ejecución

```
Pregunta (NL)
    → NLToSQL.generate()         — Gemini genera la SQL
    → SQLValidator.validate()    — bloquea todo lo que no sea SELECT/WITH
    → Orchestrator._run_with_retry()
        → BigQueryClient.run_query()   — DuckDB ejecuta la SQL sobre el CSV
        → [si falla] NLToSQL.fix()     — Gemini corrige la SQL con el error
        → [reintento] hasta MAX_RETRIES=2 veces
    → NLToSQL.suggest_chart_*()  — Gemini elige tipo y título del gráfico
    → Plotter.build_figure()     — Matplotlib construye la figura (devuelve Figure)
    → Plotter.plot() / st.pyplot() — muestra o guarda el gráfico
```

## Estructura de ficheros

```
bq-nl-agent/
├── main.py                        # Punto de entrada CLI (argparse)
├── app.py                         # Interfaz gráfica Streamlit (streamlit run app.py)
├── schema.yaml                    # Esquema de tablas (cargado en el prompt)
├── requirements.txt               # Dependencias Python
├── .env                           # Variables de entorno (no subir a git)
├── data/
│   └── Datos_Muestra_Hackaton.csv # Datos de reconciliación (separador ;)
└── src/
    ├── agent/
    │   ├── orchestrator.py        # Coordina el flujo; incluye reintento automático con NLToSQL.fix()
    │   └── nl_to_sql.py           # Gemini: generate() / fix() / suggest_chart_*()
    ├── bigquery/
    │   ├── client.py              # Carga el CSV con pandas y ejecuta SQL con DuckDB
    │   └── validator.py           # Valida que la SQL solo sea SELECT/WITH
    ├── visualization/
    │   └── plotter.py             # build_figure() → Figure | plot() → pantalla/fichero
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
| `google-genai` | Cliente Gemini (NL → SQL, corrección de SQL, tipo de gráfico, título) |
| `duckdb` | Motor SQL sobre DataFrames de pandas |
| `pandas` | Lectura del CSV y manipulación de datos |
| `matplotlib` | Renderizado de gráficos |
| `streamlit` | Interfaz gráfica web (`app.py`) |
| `PyYAML` | Lectura de `schema.yaml` |
| `python-dotenv` | Carga de `.env` al arrancar |

## Uso

### Interfaz gráfica (Streamlit)

```bash
streamlit run app.py
```

Funcionalidades de `app.py`:
- Textarea para preguntas en lenguaje natural
- Estado en tiempo real (generando SQL → validando → ejecutando → gráfico)
- Vista SQL generada + tabla de resultados + gráfico inline descargable
- Toggle dry-run y toggle para mostrar/ocultar la tabla de datos
- Historial de consultas en el sidebar (reutilizable)

### Línea de comandos (`main.py`)

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
- El system prompt incluye la regla explícita de no aplicar `SUM`/`AVG`/`MIN`/`MAX` a columnas `STRING`. Para columnas categóricas, Gemini debe usar `COUNT(*)`.
- Si DuckDB devuelve un error de tipos al ejecutar una query, el orquestador llama a `NLToSQL.fix()` con el mensaje de error y reintenta hasta `MAX_RETRIES=2` veces antes de propagar la excepción.
- En Streamlit (`app.py`) los agentes se inicializan una sola vez en `st.session_state` para evitar re-crear el cliente Gemini en cada interacción.
- `Plotter.build_figure()` devuelve el objeto `Figure` sin mostrarlo ni guardarlo, lo que permite a Streamlit renderizarlo con `st.pyplot()`. `Plotter.plot()` sigue funcionando igual para la CLI.
