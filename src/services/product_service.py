from pymongo.errors import DuplicateKeyError

from src.database import get_products, get_sales
from src.models.product import Product
from src.services import DuplicateCodeError, InsufficientStockError, ProductInUseError


def add_product(p: Product) -> None:
    p.validate()
    try:
        get_products().insert_one(p.to_doc())
    except DuplicateKeyError:
        raise DuplicateCodeError(f"A product with code '{p.code}' already exists.")


def update_product(code: str, **fields) -> None:
    allowed = {"name", "category", "price", "quantity", "description"}
    invalid = set(fields) - allowed
    if invalid:
        raise ValueError(f"Unknown fields: {invalid}")
    if "price" in fields and fields["price"] <= 0:
        raise ValueError("Price must be greater than zero.")
    if "quantity" in fields and fields["quantity"] < 0:
        raise ValueError("Quantity cannot be negative.")
    get_products().update_one({"code": code}, {"$set": fields})


def delete_product(code: str) -> None:
    in_use = get_sales().find_one({"items.product_code": code})
    if in_use:
        raise ProductInUseError(
            f"Cannot delete '{code}': it appears in existing sales records."
        )
    get_products().delete_one({"code": code})


def get_product(code: str) -> Product | None:
    doc = get_products().find_one({"code": code})
    return Product.from_doc(doc) if doc else None


def list_products(query: str = "") -> list[Product]:
    filt = {}
    if query:
        filt = {"$or": [
            {"code": {"$regex": query, "$options": "i"}},
            {"name": {"$regex": query, "$options": "i"}},
            {"category": {"$regex": query, "$options": "i"}},
        ]}
    return [Product.from_doc(d) for d in get_products().find(filt).sort("name", 1)]


def decrement_stock(code: str, qty: int) -> None:
    doc = get_products().find_one_and_update(
        {"code": code},
        {"$inc": {"quantity": -qty}},
        return_document=True,
    )
    if doc is None:
        raise ValueError(f"Product '{code}' not found.")
    if doc["quantity"] < 0:
        get_products().update_one({"code": code}, {"$inc": {"quantity": qty}})
        available = doc["quantity"] + qty
        raise InsufficientStockError(code, available, qty)
