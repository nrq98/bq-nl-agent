# 🤖 BQ NL Agent

Agente en Python que convierte preguntas en **lenguaje natural** a **queries de BigQuery** y genera **gráficos automáticos** con los resultados.

```
"¿Cuáles fueron las ventas por mes en 2024?"
        ↓
  SELECT DATE_TRUNC(fecha, MONTH) AS mes, SUM(importe) ...
        ↓
  [Ejecuta en BigQuery]
        ↓
  📊 Gráfico de barras
```

---

## 📁 Estructura del proyecto

```
bq-nl-agent/
├── main.py                        # Punto de entrada CLI
├── schema.yaml                    # Esquema de tus tablas (debes crearlo)
├── schema.example.yaml            # Ejemplo de schema.yaml
├── .env                           # Variables de entorno (no subir a Git)
├── .env.example                   # Plantilla de variables de entorno
├── requirements.txt
└── src/
    ├── agent/
    │   ├── orchestrator.py        # Coordina todo el flujo
    │   └── nl_to_sql.py           # NL → SQL usando Claude API
    ├── bigquery/
    │   ├── client.py              # Conexión y ejecución en BigQuery
    │   └── validator.py           # Valida que la SQL sea segura
    ├── visualization/
    │   └── plotter.py             # Genera gráficos con Matplotlib
    └── utils/
        ├── logger.py              # Logging centralizado
        └── schema_loader.py       # Carga el esquema de tablas
```

---

## 🚀 Instalación

### 1. Clona el repositorio

```bash
git clone https://github.com/tu-usuario/bq-nl-agent.git
cd bq-nl-agent
```

### 2. Crea un entorno virtual e instala dependencias

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/Mac
# .venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

### 3. Configura las variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
ANTHROPIC_API_KEY=sk-ant-...
GCP_PROJECT_ID=mi-proyecto-gcp
```

### 4. Configura la autenticación con Google Cloud

**Opción A — Service Account (recomendado para producción):**
```bash
# Descarga el JSON de credenciales desde GCP Console y añade en .env:
GOOGLE_APPLICATION_CREDENTIALS=/ruta/a/service-account.json
```

**Opción B — ADC (recomendado para desarrollo local):**
```bash
gcloud auth application-default login
# No necesitas definir GOOGLE_APPLICATION_CREDENTIALS
```

### 5. Define el esquema de tus tablas

```bash
cp schema.example.yaml schema.yaml
# Edita schema.yaml con tus tablas reales de BigQuery
```

---

## 💻 Uso

### Pregunta directa

```bash
python main.py "¿Cuáles fueron las ventas totales por mes en 2024?"
```

### Guardar el gráfico en un fichero

```bash
python main.py "Ventas por categoría" --output ./grafico.png
```

### Modo dry-run (ver la SQL sin ejecutarla)

```bash
python main.py "Top 10 clientes por importe" --dry-run
```

### Modo interactivo (loop de preguntas)

```bash
python main.py --interactive
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 🔒 Seguridad

- Solo se permiten sentencias `SELECT` y `WITH`. Cualquier intento de `INSERT`, `DELETE`, `DROP`, etc. es rechazado antes de llegar a BigQuery.
- Las credenciales nunca se suben a Git (`.gitignore` lo previene).
- Usa `--dry-run` para revisar la SQL generada antes de ejecutarla.

---

## 🗺️ Roadmap

- [ ] Soporte para múltiples datasets en el schema
- [ ] Retry automático si la SQL falla (el LLM corrige el error)
- [ ] Exportar resultados a CSV además del gráfico
- [ ] Interfaz web con Streamlit
- [ ] Cache de queries para ahorrar costes en BigQuery

---

## 📄 Licencia

MIT
