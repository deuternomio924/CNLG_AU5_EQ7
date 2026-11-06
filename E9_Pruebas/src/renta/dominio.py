"""Reglas de negocio del PIA (renta de vehiculos). Dominio puro: sin BD ni servicios externos."""
from dataclasses import dataclass
from math import ceil

TOLERANCIA_MINUTOS = 29
MINUTOS_POR_HORA = 60

RESERVA_PENDIENTE_PAGO = "PENDIENTE_PAGO"
RESERVA_ENTREGADA = "ENTREGADA"
CONTRATO_ACTIVO = "ACTIVO"
CONTRATO_CERRADO = "CERRADO"
VEHICULO_DISPONIBLE = "DISPONIBLE"
VEHICULO_RENTADO = "RENTADO"
VEHICULO_LIMPIEZA = "LIMPIEZA"


class ReglaDeNegocioError(Exception):
    """Base de todas las excepciones de dominio."""


class ClienteNoRegistrado(ReglaDeNegocioError):
    pass


class ClienteConAdeudo(ReglaDeNegocioError):
    pass


class CategoriaSinDisponibilidad(ReglaDeNegocioError):
    pass


class LicenciaVencida(ReglaDeNegocioError):
    pass


class ChecklistIncompleto(ReglaDeNegocioError):
    pass


class PagoNoValido(ReglaDeNegocioError):
    pass


class SerieNoCoincide(ReglaDeNegocioError):
    pass


class EntidadNoEncontrada(ReglaDeNegocioError):
    pass


class ContratoNoActivo(ReglaDeNegocioError):
    pass


@dataclass(frozen=True)
class ChecklistEntrega:
    firma_electronica: bool
    datos_completos: bool

    def validar(self):
        if not (self.firma_electronica and self.datos_completos):
            raise ChecklistIncompleto("falta firma electronica o datos completos")


@dataclass(frozen=True)
class ResultadoDevolucion:
    horas_extra: int
    cargo_extra: float
    estado_vehiculo: str


def validar_reservacion(adeudo, unidades_disponibles):
    """R1: sin adeudo y con unidades disponibles en la categoria."""
    if adeudo > 0:
        raise ClienteConAdeudo("el cliente tiene adeudo pendiente")
    if unidades_disponibles <= 0:
        raise CategoriaSinDisponibilidad("la categoria no tiene unidades disponibles")


def validar_entrega(licencia_vigente, checklist):
    """R2 (parte de dominio): licencia vigente y checklist completo."""
    if not licencia_vigente:
        raise LicenciaVencida("la licencia de conducir no esta vigente")
    checklist.validar()


def validar_serie(serie_ingresada, serie_esperada):
    """R3: la serie devuelta debe coincidir estrictamente con la asignada."""
    if serie_ingresada != serie_esperada:
        raise SerieNoCoincide(f"serie {serie_ingresada!r} != {serie_esperada!r}")


def calcular_cargo_retraso(retraso_minutos, tarifa_hora_extra):
    """R3: hasta 29 min sin cargo; desde el minuto 30 se cobra por hora iniciada."""
    if retraso_minutos <= TOLERANCIA_MINUTOS:
        return 0, 0.0
    horas = ceil(retraso_minutos / MINUTOS_POR_HORA)
    return horas, round(horas * tarifa_hora_extra, 2)
