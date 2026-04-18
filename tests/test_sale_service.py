import os
import pytest

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_supermarket")

from src.database import get_db
from src.models.product import Product
from src.models.sale import SaleItem
from src.services import InsufficientStockError
from src.services.product_service import add_product, get_product
from src.services.sale_service import get_next_receipt_no, process_sale


@pytest.fixture(autouse=True)
def clean_db():
    get_db()["products"].drop()
    get_db()["sales"].drop()
    yield
    get_db()["products"].drop()
    get_db()["sales"].drop()


def _add(code="P001", name="Milk", qty=10, price=250.0):
    add_product(Product(code=code, name=name, category="Test", price=price, quantity=qty))


def test_receipt_no_increments():
    _add()
    no1 = get_next_receipt_no()
    process_sale([SaleItem("P001", "Milk", 250.0, 1)])
    no2 = get_next_receipt_no()
    assert int(no2) == int(no1) + 1


def test_process_sale_decrements_stock():
    _add(qty=10)
    process_sale([SaleItem("P001", "Milk", 250.0, 3)])
    p = get_product("P001")
    assert p.quantity == 7


def test_insufficient_stock_raises():
    _add(qty=2)
    with pytest.raises(InsufficientStockError) as exc_info:
        process_sale([SaleItem("P001", "Milk", 250.0, 5)])
    assert exc_info.value.code == "P001"
    assert exc_info.value.available == 2


def test_insufficient_stock_does_not_change_stock():
    _add(qty=2)
    with pytest.raises(InsufficientStockError):
        process_sale([SaleItem("P001", "Milk", 250.0, 5)])
    p = get_product("P001")
    assert p.quantity == 2


def test_sale_total_correct():
    _add(code="P001", price=250.0, qty=10)
    _add(code="P002", name="Bread", price=50.0, qty=10)
    sale = process_sale([
        SaleItem("P001", "Milk", 250.0, 2),
        SaleItem("P002", "Bread", 50.0, 1),
    ])
    assert sale.total == 550.0
