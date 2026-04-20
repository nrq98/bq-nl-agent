"""
Orquestador principal del agente.
Coordina: NL → SQL → BigQuery → Gráfico
"""

from src.agent.nl_to_sql import NLToSQL
from src.bigquery.client import BigQueryClient
from src.bigquery.validator import SQLValidator
from src.visualization.plotter import Plotter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Orchestrator:
    def __init__(self):
        self.nl_to_sql = NLToSQL()
        self.bq_client = BigQueryClient()
        self.validator = SQLValidator()
        self.plotter = Plotter()

    def run(self, question: str, output_path: str = None, dry_run: bool = False):
        """
        Flujo completo: pregunta → SQL → datos → gráfico.

        Args:
            question:    Pregunta del usuario en lenguaje natural.
            output_path: Ruta para guardar el gráfico. None = mostrar en pantalla.
            dry_run:     Si True, genera la SQL pero no la ejecuta.
        """
        print(f"\n🔍 Procesando: {question}\n")

        # 1. NL → SQL
        logger.info("Generando SQL a partir de la pregunta...")
        sql = self.nl_to_sql.generate(question)
        print(f"📄 SQL generada:\n{sql}\n")

        # 2. Validación
        self.validator.validate(sql)

        if dry_run:
            print("⚠️  Modo dry-run: la query NO se ha ejecutado en BigQuery.")
            return

        # 3. Ejecutar en BigQuery
        logger.info("Ejecutando query en BigQuery...")
        df = self.bq_client.run_query(sql)
        print(f"✅ Datos obtenidos: {len(df)} filas, {len(df.columns)} columnas\n")

        # 4. Generar gráfico
        logger.info("Generando gráfico...")
        chart_title = self.nl_to_sql.suggest_chart_title(question)
        chart_type = self.nl_to_sql.suggest_chart_type(question, df)
        self.plotter.plot(df, title=chart_title, chart_type=chart_type, output_path=output_path)

        if output_path:
            print(f"💾 Gráfico guardado en: {output_path}")
        else:
            print("📊 Gráfico mostrado en pantalla.")
