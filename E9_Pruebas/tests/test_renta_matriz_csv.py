"""Verifica que la matriz CSV cumple el minimo del laboratorio y que cada caso tiene prueba."""
import csv
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV_PATH = RAIZ / "datos" / "matriz_casos_pia.csv"


def cargar_matriz():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_matriz_tiene_al_menos_nueve_casos_con_ids_unicos():
    filas = cargar_matriz()
    ids = [f["ID"] for f in filas]
    assert len(filas) >= 9
    assert len(set(ids)) == len(ids)


def test_cada_regla_tiene_exito_error_y_limite():
    tipos_por_regla = defaultdict(set)
    for fila in cargar_matriz():
        tipos_por_regla[fila["Regla_PIA"]].add(fila["Tipo"])
    assert len(tipos_por_regla) >= 3
    for regla, tipos in tipos_por_regla.items():
        assert tipos == {"Exito", "Error", "Limite"}, regla


def test_cada_caso_de_la_matriz_tiene_su_funcion_de_prueba():
    codigo = "\n".join(p.read_text(encoding="utf-8") for p in (RAIZ / "tests").glob("test_*.py"))
    for fila in cargar_matriz():
        nombre = fila["Prueba_pytest"]
        assert f"def {nombre}(" in codigo, fila["ID"]
