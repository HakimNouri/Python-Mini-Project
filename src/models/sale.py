from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class SaleItem:
    product_code: str
    product_name: str
    unit_price: float
    quantity: int

    @property
    def subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)

    def to_doc(self) -> dict:
        return {
            "product_code": self.product_code,
            "product_name": self.product_name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
        }

    @staticmethod
    def from_doc(doc: dict) -> SaleItem:
        return SaleItem(
            product_code=doc["product_code"],
            product_name=doc["product_name"],
            unit_price=doc["unit_price"],
            quantity=doc["quantity"],
        )


@dataclass
class Sale:
    receipt_no: str
    date: datetime
    items: list[SaleItem]
    total: float
    payment_method: str = "cash"
    _id: Optional[Any] = field(default=None, repr=False)

    def to_doc(self) -> dict:
        doc = {
            "receipt_no": self.receipt_no,
            "date": self.date,
            "items": [i.to_doc() for i in self.items],
            "total": self.total,
            "payment_method": self.payment_method,
        }
        if self._id is not None:
            doc["_id"] = self._id
        return doc

    @staticmethod
    def from_doc(doc: dict) -> Sale:
        return Sale(
            receipt_no=doc["receipt_no"],
            date=doc["date"],
            items=[SaleItem.from_doc(i) for i in doc["items"]],
            total=doc["total"],
            payment_method=doc.get("payment_method", "cash"),
            _id=doc.get("_id"),
        )
