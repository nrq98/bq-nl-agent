"""
BQ NL Agent — Interfaz gráfica con Streamlit.
Ejecutar: streamlit run app.py
"""

import matplotlib
matplotlib.use("Agg")  # backend no-interactivo, requerido por Streamlit

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import matplotlib.pyplot as plt
from src.agent.nl_to_sql import NLToSQL
from src.bigquery.client import BigQueryClient
from src.bigquery.validator import SQLValidator
from src.visualization.plotter import Plotter

# ── Configuración de página ──────────────────────────────────────────────────

st.set_page_config(
    page_title="BQ NL Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .sql-box { background:#1e1e1e; color:#d4d4d4; padding:1rem; border-radius:8px;
               font-family:monospace; font-size:0.85rem; white-space:pre-wrap; }
    .metric-card { background:#f0f4ff; border-radius:8px; padding:0.75rem 1rem;
                   border-left:4px solid #4C72B0; margin-bottom:0.5rem; }
    .history-item { cursor:pointer; }
</style>
""", unsafe_allow_html=True)

# ── Inicialización de estado ─────────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = []   # lista de dicts con claves: question, sql, df, chart_type, title

if "agents" not in st.session_state:
    with st.spinner("Inicializando agente..."):
        st.session_state.agents = {
            "nl_to_sql": NLToSQL(),
            "bq_client": BigQueryClient(),
            "validator": SQLValidator(),
            "plotter": Plotter(),
        }

nl_to_sql: NLToSQL = st.session_state.agents["nl_to_sql"]
bq_client: BigQueryClient = st.session_state.agents["bq_client"]
validator: SQLValidator = st.session_state.agents["validator"]
plotter: Plotter = st.session_state.agents["plotter"]

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🤖 BQ NL Agent")
    st.caption("Consulta datos en lenguaje natural")
    st.divider()

    st.subheader("⚙️ Opciones")
    dry_run = st.toggle("Modo dry-run (solo SQL)", value=False)
    show_raw = st.toggle("Mostrar tabla de datos", value=True)

    st.divider()
    st.subheader("📜 Historial")

    if not st.session_state.history:
        st.caption("Aún no hay consultas.")
    else:
        for i, entry in enumerate(reversed(st.session_state.history)):
            idx = len(st.session_state.history) - 1 - i
            label = entry["question"][:50] + ("…" if len(entry["question"]) > 50 else "")
            if st.button(label, key=f"hist_{idx}", use_container_width=True):
                st.session_state.selected_history = idx

    if st.session_state.history:
        st.divider()
        if st.button("🗑️ Limpiar historial", use_container_width=True):
            st.session_state.history = []
            if "selected_history" in st.session_state:
                del st.session_state.selected_history
            st.rerun()

# ── Cabecera principal ───────────────────────────────────────────────────────

st.title("Consulta de datos en lenguaje natural")
st.caption("Escribe tu pregunta y el agente generará la SQL, ejecutará la consulta y creará el gráfico automáticamente.")

st.divider()

# ── Formulario de consulta ───────────────────────────────────────────────────

with st.form("query_form", clear_on_submit=False):
    question = st.text_area(
        "Tu pregunta",
        placeholder="Ej: ¿Cuál es el total por Input? / ¿Cuántos registros hay por estado?",
        height=80,
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("🔍 Consultar", use_container_width=True, type="primary")

# ── Lógica de consulta ───────────────────────────────────────────────────────

def run_query(question: str):
    result = {"question": question, "sql": None, "df": None, "chart_type": None, "title": None, "error": None}

    with st.status("Procesando consulta…", expanded=True) as status:
        try:
            st.write("Generando SQL con Gemini…")
            sql = nl_to_sql.generate(question)
            result["sql"] = sql

            st.write("Validando SQL…")
            validator.validate(sql)

            if not dry_run:
                st.write("Ejecutando consulta…")
                df = bq_client.run_query(sql)
                result["df"] = df

                if not df.empty:
                    st.write("Seleccionando tipo de gráfico…")
                    result["chart_type"] = nl_to_sql.suggest_chart_type(question, df)
                    result["title"] = nl_to_sql.suggest_chart_title(question)

            status.update(label="✅ Listo", state="complete", expanded=False)

        except ValueError as e:
            result["error"] = str(e)
            status.update(label="❌ Error de validación", state="error", expanded=False)
        except Exception as e:
            result["error"] = str(e)
            status.update(label="❌ Error", state="error", expanded=False)

    return result


def display_result(result: dict):
    if result.get("error"):
        st.error(result["error"])
        return

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("📄 SQL generada")
        st.code(result["sql"], language="sql")

    if dry_run:
        st.info("Modo dry-run activo: la consulta no fue ejecutada.")
        return

    df: pd.DataFrame = result.get("df")

    if df is None:
        return

    with col2:
        st.subheader("📊 Resumen")
        m1, m2 = st.columns(2)
        m1.metric("Filas", f"{len(df):,}")
        m2.metric("Columnas", len(df.columns))

    if df.empty:
        st.warning("La consulta no devolvió resultados.")
        return

    if show_raw:
        st.subheader("🗂️ Datos")
        st.dataframe(df, use_container_width=True, height=280)

    if result.get("chart_type"):
        st.subheader(f"📈 {result.get('title', 'Gráfico')}")
        try:
            fig = plotter.build_figure(df, title=result["title"], chart_type=result["chart_type"])
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            buf = _fig_to_bytes(fig)
            st.download_button(
                "⬇️ Descargar gráfico",
                data=buf,
                file_name="grafico.png",
                mime="image/png",
            )
        except Exception as e:
            st.error(f"Error al generar el gráfico: {e}")


def _fig_to_bytes(fig: plt.Figure) -> bytes:
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return buf.read()


# ── Renderizado ──────────────────────────────────────────────────────────────

# Mostrar resultado del historial seleccionado
if "selected_history" in st.session_state:
    idx = st.session_state.selected_history
    if 0 <= idx < len(st.session_state.history):
        entry = st.session_state.history[idx]
        st.info(f"Mostrando resultado guardado: *{entry['question']}*")
        display_result(entry)

# Ejecutar nueva consulta
elif submitted and question.strip():
    result = run_query(question.strip())

    if not result.get("error"):
        st.session_state.history.append(result)

    display_result(result)

elif submitted:
    st.warning("Escribe una pregunta antes de consultar.")
