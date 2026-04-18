import os
import pytest
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_supermarket")

from src.models.sale import Sale, SaleItem
from src.services.receipt_service import generate, RECEIPTS_DIR


@pytest.fixture(autouse=True)
def cleanup_receipts():
    yield
    for f in RECEIPTS_DIR.glob("receipt_TEST*.txt"):
        f.unlink(missing_ok=True)


def _make_sale() -> Sale:
    return Sale(
        receipt_no="TEST001",
        date=datetime(2026, 4, 16, 14, 30, tzinfo=timezone.utc),
        items=[
            SaleItem("P001", "Milk", 250.0, 2),
            SaleItem("P002", "Bread", 20.0, 1),
        ],
        total=520.0,
    )


def test_receipt_file_created():
    sale = _make_sale()
    path = generate(sale, "TEST MARKET")
    assert Path(path).exists()


def test_receipt_filename():
    sale = _make_sale()
    path = generate(sale, "TEST MARKET")
    assert Path(path).name == "receipt_TEST001.txt"


def test_receipt_contains_store_name():
    sale = _make_sale()
    path = generate(sale, "TEST MARKET")
    content = Path(path).read_text(encoding="utf-8")
    assert "TEST MARKET" in content


def test_receipt_contains_total():
    sale = _make_sale()
    path = generate(sale, "TEST MARKET")
    content = Path(path).read_text(encoding="utf-8")
    assert "520.00" in content


def test_receipt_contains_items():
    sale = _make_sale()
    path = generate(sale, "TEST MARKET")
    content = Path(path).read_text(encoding="utf-8")
    assert "Milk" in content
    assert "Bread" in content


def test_receipt_contains_receipt_no():
    sale = _make_sale()
    path = generate(sale, "TEST MARKET")
    content = Path(path).read_text(encoding="utf-8")
    assert "TEST001" in content
