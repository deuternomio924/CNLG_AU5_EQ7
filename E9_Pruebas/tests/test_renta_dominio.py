"""Pruebas unitarias del dominio del PIA (sin BD, sin mocks)."""
import pytest

from src.renta import dominio as d


def test_dom_reservacion_valida_no_lanza():
    d.validar_reservacion(adeudo=0, unidades_disponibles=1)  # limite: ultima unidad


def test_dom_reservacion_con_adeudo_se_rechaza():
    with pytest.raises(d.ClienteConAdeudo):
        d.validar_reservacion(adeudo=0.01, unidades_disponibles=5)


def test_dom_reservacion_sin_unidades_se_rechaza():
    with pytest.raises(d.CategoriaSinDisponibilidad):
        d.validar_reservacion(adeudo=0, unidades_disponibles=0)


def test_dom_entrega_completa_no_lanza():
    d.validar_entrega(True, d.ChecklistEntrega(True, True))


def test_dom_entrega_licencia_vencida():
    with pytest.raises(d.LicenciaVencida):
        d.validar_entrega(False, d.ChecklistEntrega(True, True))


@pytest.mark.parametrize(
    "firma, datos",
    [(False, True), (True, False), (False, False)],
)
def test_dom_checklist_incompleto(firma, datos):
    with pytest.raises(d.ChecklistIncompleto):
        d.validar_entrega(True, d.ChecklistEntrega(firma, datos))


def test_dom_serie_coincidente_no_lanza():
    d.validar_serie("ABC-123", "ABC-123")


@pytest.mark.parametrize("ingresada", ["XYZ-999", "abc-123", "ABC-123 "])
def test_dom_serie_distinta_se_rechaza_estrictamente(ingresada):
    with pytest.raises(d.SerieNoCoincide):
        d.validar_serie(ingresada, "ABC-123")


@pytest.mark.parametrize(
    "retraso, horas, cargo",
    [(0, 0, 0.0), (15, 0, 0.0), (29, 0, 0.0), (30, 1, 150.0), (60, 1, 150.0), (61, 2, 300.0)],
)
def test_dom_cargo_por_retraso_limites_de_tolerancia(retraso, horas, cargo):
    assert d.calcular_cargo_retraso(retraso, 150.0) == (horas, cargo)
