import os
import pytest

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_supermarket")

from src.database import get_db
from src.models.product import Product
from src.services import DuplicateCodeError, ProductInUseError
from src.services.product_service import (
    add_product, delete_product, get_product, list_products, update_product,
)


@pytest.fixture(autouse=True)
def clean_db():
    get_db()["products"].drop()
    get_db()["sales"].drop()
    yield
    get_db()["products"].drop()
    get_db()["sales"].drop()


def _p(**kwargs) -> Product:
    defaults = dict(code="P001", name="Milk", category="Dairy", price=250.0, quantity=10)
    defaults.update(kwargs)
    return Product(**defaults)


def test_add_product():
    add_product(_p())
    assert get_product("P001") is not None


def test_duplicate_code_raises():
    add_product(_p())
    with pytest.raises(DuplicateCodeError):
        add_product(_p())


def test_update_product():
    add_product(_p())
    update_product("P001", price=300.0, name="Full Milk")
    p = get_product("P001")
    assert p.price == 300.0
    assert p.name == "Full Milk"


def test_delete_product():
    add_product(_p())
    delete_product("P001")
    assert get_product("P001") is None


def test_delete_product_in_use_raises():
    add_product(_p())
    get_db()["sales"].insert_one({
        "receipt_no": "001", "date": None,
        "items": [{"product_code": "P001", "product_name": "Milk", "unit_price": 250, "quantity": 1}],
        "total": 250,
    })
    with pytest.raises(ProductInUseError):
        delete_product("P001")


def test_list_products_filter():
    add_product(_p(code="P001", name="Milk"))
    add_product(_p(code="P002", name="Bread", category="Bakery"))
    results = list_products("bread")
    assert len(results) == 1
    assert results[0].code == "P002"


def test_invalid_price_raises():
    with pytest.raises(ValueError):
        _p(price=-5).validate()


def test_invalid_code_raises():
    with pytest.raises(ValueError):
        _p(code="").validate()
