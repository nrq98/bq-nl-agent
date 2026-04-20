"""
Generador de gráficos con Matplotlib.
Soporta: bar, line, pie, scatter, hist.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Plotter:
    def plot(
        self,
        df: pd.DataFrame,
        title: str = "Resultado",
        chart_type: str = "bar",
        output_path: str = None,
    ):
        """
        Genera un gráfico a partir de un DataFrame.

        Args:
            df:          DataFrame con los datos.
            title:       Título del gráfico.
            chart_type:  Tipo de gráfico (bar, line, pie, scatter, hist).
            output_path: Ruta para guardar la imagen. None = mostrar en pantalla.
        """
        if df.empty:
            print("⚠️  No hay datos para graficar.")
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#f9f9f9")
        ax.set_facecolor("#ffffff")

        try:
            if chart_type == "bar":
                self._bar(df, ax)
            elif chart_type == "line":
                self._line(df, ax)
            elif chart_type == "pie":
                self._pie(df, ax)
            elif chart_type == "scatter":
                self._scatter(df, ax)
            elif chart_type == "hist":
                self._hist(df, ax)
            else:
                logger.warning(f"Tipo de gráfico '{chart_type}' no reconocido. Usando bar.")
                self._bar(df, ax)
        except Exception as e:
            logger.error(f"Error generando gráfico '{chart_type}': {e}. Intentando bar como fallback.")
            ax.clear()
            self._bar(df, ax)

        ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            logger.info(f"Gráfico guardado en {output_path}")
        else:
            plt.show()

        plt.close(fig)

    # ── Tipos de gráficos ──────────────────────────────────────────────────────

    def _bar(self, df: pd.DataFrame, ax: plt.Axes):
        x_col = df.columns[0]
        y_col = df.select_dtypes(include="number").columns[0] if len(df.select_dtypes(include="number").columns) > 0 else df.columns[1]
        ax.bar(df[x_col].astype(str), df[y_col], color="#4C72B0", edgecolor="white")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        plt.xticks(rotation=45, ha="right")

    def _line(self, df: pd.DataFrame, ax: plt.Axes):
        x_col = df.columns[0]
        numeric_cols = df.select_dtypes(include="number").columns
        for col in numeric_cols:
            ax.plot(df[x_col].astype(str), df[col], marker="o", label=col)
        ax.set_xlabel(x_col)
        ax.legend()
        plt.xticks(rotation=45, ha="right")

    def _pie(self, df: pd.DataFrame, ax: plt.Axes):
        label_col = df.columns[0]
        value_col = df.select_dtypes(include="number").columns[0]
        ax.pie(
            df[value_col],
            labels=df[label_col].astype(str),
            autopct="%1.1f%%",
            startangle=140,
        )
        ax.axis("equal")

    def _scatter(self, df: pd.DataFrame, ax: plt.Axes):
        numeric = df.select_dtypes(include="number")
        if len(numeric.columns) < 2:
            raise ValueError("Scatter necesita al menos 2 columnas numéricas.")
        ax.scatter(numeric.iloc[:, 0], numeric.iloc[:, 1], alpha=0.7, color="#DD8452")
        ax.set_xlabel(numeric.columns[0])
        ax.set_ylabel(numeric.columns[1])

    def _hist(self, df: pd.DataFrame, ax: plt.Axes):
        value_col = df.select_dtypes(include="number").columns[0]
        ax.hist(df[value_col].dropna(), bins=20, color="#55A868", edgecolor="white")
        ax.set_xlabel(value_col)
        ax.set_ylabel("Frecuencia")
