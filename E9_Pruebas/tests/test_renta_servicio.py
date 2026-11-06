"""Pruebas de integracion (SQLite en memoria) y con mock de la pasarela de pagos.

Cada prueba cp0X corresponde a una fila de datos/matriz_casos_pia.csv.
"""
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.renta import dominio as d
from src.renta.repositorio import (
    ActaEntregaRow,
    BitacoraDevolucionRow,
    CategoriaRow,
    ClienteRow,
    ContratoRow,
    ReservacionRow,
    VehiculoRow,
    make_engine,
)
from src.renta.servicio import ServicioRenta

CHECKLIST_OK = d.ChecklistEntrega(firma_electronica=True, datos_completos=True)


@pytest.fixture
def session():
    engine = make_engine()  # BD en memoria: no toca datos reales
    with Session(engine) as s:
        s.add_all(
            [
                ClienteRow(id=1, nombre="Cliente Sin Adeudo", adeudo=0),
                ClienteRow(id=2, nombre="Cliente Con Adeudo", adeudo=500),
                CategoriaRow(id=1, sucursal_id=1, nombre="Compacto", unidades_disponibles=3),
                CategoriaRow(id=2, sucursal_id=1, nombre="SUV", unidades_disponibles=0),
                CategoriaRow(id=3, sucursal_id=1, nombre="Pickup", unidades_disponibles=1),
                VehiculoRow(id=1, categoria_id=1, serie="ABC-123", estado=d.VEHICULO_DISPONIBLE),
            ]
        )
        s.commit()
        yield s


@pytest.fixture
def pasarela():
    # spec: solo existe verificar_pago; cualquier intento de "cobrar" fallaria (sin cobro real)
    gateway = Mock(spec=["verificar_pago"])
    gateway.verificar_pago.return_value = True
    return gateway


@pytest.fixture
def servicio(session, pasarela):
    return ServicioRenta(session, pasarela, tarifa_hora_extra=150.0)


def contar(session, modelo):
    return session.scalar(select(func.count()).select_from(modelo))


def reservar(servicio):
    return servicio.crear_reservacion(cliente_id=1, categoria_id=1, sucursal_id=1)


def contrato_activo(servicio):
    reserva = reservar(servicio)
    return servicio.entregar_vehiculo(reserva.id, 1, True, CHECKLIST_OK)


# ---------- R1: Reservacion ----------
def test_cp01_reservacion_exitosa_genera_folio_y_pendiente_de_pago(servicio, session):
    reserva = reservar(servicio)
    fila = session.scalar(select(ReservacionRow).where(ReservacionRow.id == reserva.id))
    assert fila.folio == "RES-00001"
    assert fila.estado == d.RESERVA_PENDIENTE_PAGO
    assert session.get(CategoriaRow, 1).unidades_disponibles == 2  # stock descontado


def test_cp02_cliente_con_adeudo_se_rechaza_sin_persistir(servicio, session):
    with pytest.raises(d.ClienteConAdeudo):
        servicio.crear_reservacion(cliente_id=2, categoria_id=1, sucursal_id=1)
    assert contar(session, ReservacionRow) == 0
    assert session.get(CategoriaRow, 1).unidades_disponibles == 3


def test_cp03_categoria_sin_stock_se_rechaza(servicio, session):
    with pytest.raises(d.CategoriaSinDisponibilidad):
        servicio.crear_reservacion(cliente_id=1, categoria_id=2, sucursal_id=1)
    assert contar(session, ReservacionRow) == 0


def test_cp03b_limite_ultima_unidad_se_reserva_y_la_siguiente_se_rechaza(servicio, session):
    servicio.crear_reservacion(cliente_id=1, categoria_id=3, sucursal_id=1)
    assert session.get(CategoriaRow, 3).unidades_disponibles == 0
    with pytest.raises(d.CategoriaSinDisponibilidad):
        servicio.crear_reservacion(cliente_id=1, categoria_id=3, sucursal_id=1)


def test_cliente_no_registrado_se_rechaza(servicio):
    with pytest.raises(d.ClienteNoRegistrado):
        servicio.crear_reservacion(cliente_id=99, categoria_id=1, sucursal_id=1)


def test_categoria_inexistente_en_la_sucursal_se_rechaza(servicio):
    with pytest.raises(d.CategoriaSinDisponibilidad):
        servicio.crear_reservacion(cliente_id=1, categoria_id=1, sucursal_id=99)


# ---------- R2: Entrega ----------
def test_cp04_entrega_exitosa_crea_contrato_acta_y_vehiculo_rentado(servicio, session, pasarela):
    reserva = reservar(servicio)
    contrato = servicio.entregar_vehiculo(reserva.id, 1, True, CHECKLIST_OK)
    assert session.get(ContratoRow, contrato.id).estado == d.CONTRATO_ACTIVO
    assert contar(session, ActaEntregaRow) == 1
    assert session.get(VehiculoRow, 1).estado == d.VEHICULO_RENTADO
    assert session.get(ReservacionRow, reserva.id).estado == d.RESERVA_ENTREGADA
    pasarela.verificar_pago.assert_called_once_with("RES-00001")


def test_cp05_licencia_vencida_bloquea_entrega(servicio, session, pasarela):
    reserva = reservar(servicio)
    with pytest.raises(d.LicenciaVencida):
        servicio.entregar_vehiculo(reserva.id, 1, False, CHECKLIST_OK)
    assert contar(session, ContratoRow) == 0
    assert contar(session, ActaEntregaRow) == 0
    assert session.get(VehiculoRow, 1).estado == d.VEHICULO_DISPONIBLE
    pasarela.verificar_pago.assert_not_called()


def test_cp06_checklist_sin_firma_ni_datos_rechaza_entrega(servicio, session):
    reserva = reservar(servicio)
    checklist = d.ChecklistEntrega(firma_electronica=False, datos_completos=False)
    with pytest.raises(d.ChecklistIncompleto):
        servicio.entregar_vehiculo(reserva.id, 1, True, checklist)
    assert contar(session, ActaEntregaRow) == 0
    assert session.get(VehiculoRow, 1).estado == d.VEHICULO_DISPONIBLE


def test_pago_rechazado_por_pasarela_no_entrega_vehiculo(servicio, session, pasarela):
    pasarela.verificar_pago.return_value = False
    reserva = reservar(servicio)
    with pytest.raises(d.PagoNoValido):
        servicio.entregar_vehiculo(reserva.id, 1, True, CHECKLIST_OK)
    pasarela.verificar_pago.assert_called_once_with(reserva.folio)
    assert contar(session, ContratoRow) == 0
    assert session.get(VehiculoRow, 1).estado == d.VEHICULO_DISPONIBLE


def test_entrega_con_reservacion_inexistente(servicio):
    with pytest.raises(d.EntidadNoEncontrada):
        servicio.entregar_vehiculo(99, 1, True, CHECKLIST_OK)


def test_entrega_con_vehiculo_inexistente(servicio):
    reserva = reservar(servicio)
    with pytest.raises(d.EntidadNoEncontrada):
        servicio.entregar_vehiculo(reserva.id, 99, True, CHECKLIST_OK)


# ---------- R3: Devolucion ----------
def test_cp07_devolucion_en_tolerancia_cierra_sin_cargo_y_pasa_a_limpieza(servicio, session):
    contrato = contrato_activo(servicio)
    resultado = servicio.recibir_devolucion(contrato.id, "ABC-123", retraso_minutos=15)
    assert resultado.horas_extra == 0
    assert resultado.cargo_extra == 0.0
    fila = session.get(ContratoRow, contrato.id)
    assert fila.estado == d.CONTRATO_CERRADO
    assert fila.cargo_extra == 0.0
    assert session.get(VehiculoRow, 1).estado == d.VEHICULO_LIMPIEZA


def test_cp08_serie_no_coincidente_lanza_excepcion_y_hace_rollback(servicio, session):
    contrato = contrato_activo(servicio)
    with pytest.raises(d.SerieNoCoincide):
        servicio.recibir_devolucion(contrato.id, "XYZ-999", retraso_minutos=0)
    # Rollback: la bitacora flusheada se deshizo y el estado quedo como antes
    assert contar(session, BitacoraDevolucionRow) == 0
    assert session.get(ContratoRow, contrato.id).estado == d.CONTRATO_ACTIVO
    assert session.get(VehiculoRow, 1).estado == d.VEHICULO_RENTADO


def test_cp09_retraso_de_30_minutos_cobra_una_hora_extra(servicio, session):
    contrato = contrato_activo(servicio)
    resultado = servicio.recibir_devolucion(contrato.id, "ABC-123", retraso_minutos=30)
    assert resultado.horas_extra == 1
    assert resultado.cargo_extra == 150.0
    fila = session.get(ContratoRow, contrato.id)
    assert (fila.horas_extra, fila.cargo_extra) == (1, 150.0)
    assert fila.estado == d.CONTRATO_CERRADO


def test_cp09b_limite_29_minutos_no_cobra(servicio):
    contrato = contrato_activo(servicio)
    resultado = servicio.recibir_devolucion(contrato.id, "ABC-123", retraso_minutos=29)
    assert resultado.cargo_extra == 0.0


def test_devolucion_de_contrato_ya_cerrado_se_rechaza(servicio):
    contrato = contrato_activo(servicio)
    servicio.recibir_devolucion(contrato.id, "ABC-123", retraso_minutos=0)
    with pytest.raises(d.ContratoNoActivo):
        servicio.recibir_devolucion(contrato.id, "ABC-123", retraso_minutos=0)


def test_devolucion_de_contrato_inexistente_se_rechaza(servicio):
    with pytest.raises(d.ContratoNoActivo):
        servicio.recibir_devolucion(99, "ABC-123", retraso_minutos=0)
