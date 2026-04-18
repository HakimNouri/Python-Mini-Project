from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Product:
    code: str
    name: str
    category: str
    price: float
    quantity: int
    description: str = ""
    _id: Optional[Any] = field(default=None, repr=False)

    def validate(self) -> None:
        if not self.code or not self.code.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Product code must be non-empty and alphanumeric.")
        if self.price <= 0:
            raise ValueError("Price must be greater than zero.")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        if not self.name.strip():
            raise ValueError("Name cannot be empty.")

    def to_doc(self) -> dict:
        doc = {
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "quantity": self.quantity,
            "description": self.description,
        }
        if self._id is not None:
            doc["_id"] = self._id
        return doc

    @staticmethod
    def from_doc(doc: dict) -> Product:
        return Product(
            code=doc["code"],
            name=doc["name"],
            category=doc.get("category", ""),
            price=doc["price"],
            quantity=doc["quantity"],
            description=doc.get("description", ""),
            _id=doc.get("_id"),
        )
