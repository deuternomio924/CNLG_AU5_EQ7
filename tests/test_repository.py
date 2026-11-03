from sqlalchemy.orm import Session
from sqlalchemy import select
from src.domain import Order
from src.repository import make_engine, SqlOrderRepository, OrderRow

def test_repository_commit():
    engine = make_engine()
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(120))
        session.commit()
        assert session.scalar(select(OrderRow).where(OrderRow.id == 1)).total == 120

def test_repository_rollback():
    engine = make_engine()
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(120))
        session.rollback()
        assert session.scalar(select(OrderRow).where(OrderRow.id == 1)) is None
#//////////////////////
def test_repository_commit_id_2_250():
    engine = make_engine()
    with Session(engine) as session:
        SqlOrderRepository(session).save(2, Order(250))
        session.commit()
        assert session.scalar(select(OrderRow).where(OrderRow.id == 2)).total == 250
