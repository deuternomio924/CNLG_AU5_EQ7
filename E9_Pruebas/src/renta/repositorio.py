"""Persistencia SQLAlchemy del PIA de renta de vehiculos."""
from sqlalchemy import Boolean, Float, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class ClienteRow(Base):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    adeudo: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class CategoriaRow(Base):
    __tablename__ = "categorias"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    unidades_disponibles: Mapped[int] = mapped_column(Integer, nullable=False)


class VehiculoRow(Base):
    __tablename__ = "vehiculos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria_id: Mapped[int] = mapped_column(Integer, nullable=False)
    serie: Mapped[str] = mapped_column(String, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)


class ReservacionRow(Base):
    __tablename__ = "reservaciones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    cliente_id: Mapped[int] = mapped_column(Integer, nullable=False)
    categoria_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sucursal_id: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)


class ContratoRow(Base):
    __tablename__ = "contratos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reservacion_id: Mapped[int] = mapped_column(Integer, nullable=False)
    vehiculo_id: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)
    horas_extra: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cargo_extra: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class ActaEntregaRow(Base):
    __tablename__ = "actas_entrega"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contrato_id: Mapped[int] = mapped_column(Integer, nullable=False)
    licencia_vigente: Mapped[bool] = mapped_column(Boolean, nullable=False)
    firma_electronica: Mapped[bool] = mapped_column(Boolean, nullable=False)
    datos_completos: Mapped[bool] = mapped_column(Boolean, nullable=False)


class BitacoraDevolucionRow(Base):
    __tablename__ = "bitacora_devolucion"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contrato_id: Mapped[int] = mapped_column(Integer, nullable=False)
    serie_ingresada: Mapped[str] = mapped_column(String, nullable=False)
    retraso_minutos: Mapped[int] = mapped_column(Integer, nullable=False)


class RentaRepository:
    def __init__(self, session: Session):
        self.session = session

    def obtener_cliente(self, cliente_id):
        return self.session.get(ClienteRow, cliente_id)

    def obtener_categoria(self, categoria_id, sucursal_id):
        return self.session.scalar(
            select(CategoriaRow).where(
                CategoriaRow.id == categoria_id, CategoriaRow.sucursal_id == sucursal_id
            )
        )

    def obtener_reservacion(self, reservacion_id):
        return self.session.get(ReservacionRow, reservacion_id)

    def obtener_vehiculo(self, vehiculo_id):
        return self.session.get(VehiculoRow, vehiculo_id)

    def obtener_contrato(self, contrato_id):
        return self.session.get(ContratoRow, contrato_id)

    def agregar(self, fila):
        self.session.add(fila)
        self.session.flush()
        return fila


def make_engine(url="sqlite+pysqlite:///:memory:"):
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine
