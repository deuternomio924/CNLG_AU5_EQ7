from dataclasses import dataclass

class CustomerHasDebt(Exception):
    pass

@dataclass
class Order:
    total: float
    vip: bool = False
    status: str = "NEW"
    discount: float = 0.0
#
    def _verificar_no_confirmado(self):
        if self.status == "CONFIRMED":
            raise ValueError("already confirmed")
#

    def confirm(self, customer_debt=0):
        #
        self._verificar_no_confirmado()
        #
        if self.total <= 0:
            raise ValueError("total must be positive")
        if customer_debt > 0:
            raise CustomerHasDebt("outstanding debt")
        self.discount = round(self.total * 0.15, 2) if self.vip else 0.0
        self.status = "CONFIRMED"
        return self.total - self.discount
