"""
Cliente de Google BigQuery.
Soporta autenticación por Service Account (JSON) o Application Default Credentials (ADC).
"""

import os
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BigQueryClient:
    def __init__(self):
        self.project_id = os.environ.get("GCP_PROJECT_ID")
        if not self.project_id:
            raise EnvironmentError("La variable de entorno GCP_PROJECT_ID no está definida.")

        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if credentials_path:
            # Autenticación con Service Account (fichero JSON)
            logger.info(f"Autenticando con Service Account: {credentials_path}")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/bigquery.readonly"],
            )
            self.client = bigquery.Client(project=self.project_id, credentials=credentials)
        else:
            # Application Default Credentials (gcloud auth application-default login)
            logger.info("Autenticando con Application Default Credentials (ADC).")
            self.client = bigquery.Client(project=self.project_id)

    def run_query(self, sql: str) -> pd.DataFrame:
        """
        Ejecuta una query en BigQuery y devuelve un DataFrame.

        Args:
            sql: Query SQL válida para BigQuery.

        Returns:
            DataFrame con los resultados.

        Raises:
            RuntimeError: Si la query falla en BigQuery.
        """
        try:
            logger.info(f"Ejecutando query:\n{sql}")
            query_job = self.client.query(sql)
            df = query_job.to_dataframe()
            logger.info(f"Query completada. Filas devueltas: {len(df)}")
            return df
        except Exception as e:
            logger.error(f"Error ejecutando query en BigQuery: {e}")
            raise RuntimeError(f"Error en BigQuery: {e}") from e

    def dry_run(self, sql: str) -> int:
        """
        Hace un dry-run de la query para estimar bytes procesados sin ejecutarla.

        Returns:
            Bytes estimados que procesaría la query.
        """
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        job = self.client.query(sql, job_config=job_config)
        bytes_processed = job.total_bytes_processed
        gb = bytes_processed / (1024**3)
        logger.info(f"Dry-run: la query procesaría ~{gb:.4f} GB")
        return bytes_processed
