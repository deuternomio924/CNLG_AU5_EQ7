"""Casos de uso del PIA: reservar, entregar y recibir vehiculos.

La pasarela de pagos es un servicio externo (duck typing): debe exponer
`verificar_pago(folio) -> bool`. En las pruebas se sustituye por un Mock.
"""
from contextlib import contextmanager

from src.renta import dominio as d
from src.renta.repositorio import (
    ActaEntregaRow,
    BitacoraDevolucionRow,
    ContratoRow,
    RentaRepository,
    ReservacionRow,
)


class ServicioRenta:
    def __init__(self, session, pasarela_pagos, tarifa_hora_extra=150.0):
        self.session = session
        self.repo = RentaRepository(session)
        self.pasarela = pasarela_pagos
        self.tarifa_hora_extra = tarifa_hora_extra

    @contextmanager
    def _transaccion(self):
        """Unidad de trabajo: commit si todo sale bien, rollback ante cualquier error."""
        try:
            yield
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def crear_reservacion(self, cliente_id, categoria_id, sucursal_id):
        with self._transaccion():
            cliente = self.repo.obtener_cliente(cliente_id)
            if cliente is None:
                raise d.ClienteNoRegistrado(f"cliente {cliente_id} no registrado")
            categoria = self.repo.obtener_categoria(categoria_id, sucursal_id)
            if categoria is None:
                raise d.CategoriaSinDisponibilidad("la categoria no existe en la sucursal")
            d.validar_reservacion(cliente.adeudo, categoria.unidades_disponibles)
            categoria.unidades_disponibles -= 1
            reserva = self.repo.agregar(
                ReservacionRow(
                    cliente_id=cliente_id,
                    categoria_id=categoria_id,
                    sucursal_id=sucursal_id,
                    estado=d.RESERVA_PENDIENTE_PAGO,
                )
            )
            reserva.folio = f"RES-{reserva.id:05d}"
        return reserva

    def entregar_vehiculo(self, reservacion_id, vehiculo_id, licencia_vigente, checklist):
        with self._transaccion():
            reserva = self.repo.obtener_reservacion(reservacion_id)
            if reserva is None:
                raise d.EntidadNoEncontrada(f"reservacion {reservacion_id} no existe")
            vehiculo = self.repo.obtener_vehiculo(vehiculo_id)
            if vehiculo is None:
                raise d.EntidadNoEncontrada(f"vehiculo {vehiculo_id} no existe")
            d.validar_entrega(licencia_vigente, checklist)
            if not self.pasarela.verificar_pago(reserva.folio):
                raise d.PagoNoValido("la pasarela no confirmo el pago")
            contrato = self.repo.agregar(
                ContratoRow(
                    reservacion_id=reserva.id,
                    vehiculo_id=vehiculo.id,
                    estado=d.CONTRATO_ACTIVO,
                    horas_extra=0,
                    cargo_extra=0.0,
                )
            )
            self.repo.agregar(
                ActaEntregaRow(
                    contrato_id=contrato.id,
                    licencia_vigente=licencia_vigente,
                    firma_electronica=checklist.firma_electronica,
                    datos_completos=checklist.datos_completos,
                )
            )
            vehiculo.estado = d.VEHICULO_RENTADO
            reserva.estado = d.RESERVA_ENTREGADA
        return contrato

    def recibir_devolucion(self, contrato_id, serie_ingresada, retraso_minutos):
        with self._transaccion():
            contrato = self.repo.obtener_contrato(contrato_id)
            if contrato is None or contrato.estado != d.CONTRATO_ACTIVO:
                raise d.ContratoNoActivo(f"contrato {contrato_id} no esta activo")
            vehiculo = self.repo.obtener_vehiculo(contrato.vehiculo_id)
            # La recepcion se registra antes de validar: si la serie no coincide,
            # el rollback debe deshacer este registro (atomicidad de la devolucion).
            self.repo.agregar(
                BitacoraDevolucionRow(
                    contrato_id=contrato.id,
                    serie_ingresada=serie_ingresada,
                    retraso_minutos=retraso_minutos,
                )
            )
            d.validar_serie(serie_ingresada, vehiculo.serie)
            horas, cargo = d.calcular_cargo_retraso(retraso_minutos, self.tarifa_hora_extra)
            contrato.estado = d.CONTRATO_CERRADO
            contrato.horas_extra = horas
            contrato.cargo_extra = cargo
            vehiculo.estado = d.VEHICULO_LIMPIEZA
            resultado = d.ResultadoDevolucion(horas, cargo, d.VEHICULO_LIMPIEZA)
        return resultado
