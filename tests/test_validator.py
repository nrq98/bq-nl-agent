"""
Tests unitarios para el validador de SQL.
"""

import pytest
from src.bigquery.validator import SQLValidator


validator = SQLValidator()


def test_select_valido():
    validator.validate("SELECT * FROM `proyecto.dataset.tabla` LIMIT 100")


def test_with_valido():
    sql = """
    WITH resumen AS (
        SELECT fecha, SUM(importe) AS total
        FROM `proyecto.dataset.ventas`
        GROUP BY fecha
    )
    SELECT * FROM resumen
    """
    validator.validate(sql)


def test_insert_rechazado():
    with pytest.raises(ValueError, match="INSERT"):
        validator.validate("INSERT INTO tabla VALUES (1, 'test')")


def test_delete_rechazado():
    with pytest.raises(ValueError, match="DELETE"):
        validator.validate("DELETE FROM tabla WHERE id = 1")


def test_drop_rechazado():
    with pytest.raises(ValueError, match="DROP"):
        validator.validate("DROP TABLE tabla")


def test_sin_select_rechazado():
    with pytest.raises(ValueError):
        validator.validate("SHOW TABLES")
