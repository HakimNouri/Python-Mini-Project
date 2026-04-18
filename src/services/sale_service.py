import calendar
from datetime import datetime, timezone

from src.database import get_products, get_sales
from src.models.sale import Sale, SaleItem
from src.services import InsufficientStockError
from src.services.product_service import decrement_stock


def get_next_receipt_no() -> str:
    count = get_sales().count_documents({})
    return str(count + 1).zfill(3)


def process_sale(items: list[SaleItem], payment_method: str = "cash") -> Sale:
    for item in items:
        doc = get_products().find_one({"code": item.product_code})
        if doc is None:
            raise ValueError(f"Product '{item.product_code}' not found.")
        if doc["quantity"] < item.quantity:
            raise InsufficientStockError(item.product_code, doc["quantity"], item.quantity)

    for item in items:
        decrement_stock(item.product_code, item.quantity)

    total = round(sum(i.subtotal for i in items), 2)
    sale = Sale(
        receipt_no=get_next_receipt_no(),
        date=datetime.now(timezone.utc),
        items=items,
        total=total,
        payment_method=payment_method,
    )
    result = get_sales().insert_one(sale.to_doc())
    sale._id = result.inserted_id
    return sale


def list_sales(date_from: datetime | None = None, date_to: datetime | None = None) -> list[Sale]:
    filt: dict = {}
    if date_from or date_to:
        filt["date"] = {}
        if date_from:
            filt["date"]["$gte"] = date_from
        if date_to:
            filt["date"]["$lte"] = date_to
    return [Sale.from_doc(d) for d in get_sales().find(filt).sort("date", -1)]


def daily_revenue(date: datetime) -> float:
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    pipeline = [
        {"$match": {"date": {"$gte": start, "$lte": end}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}},
    ]
    result = list(get_sales().aggregate(pipeline))
    return result[0]["total"] if result else 0.0


def monthly_revenue_by_day(year: int, month: int) -> dict[int, float]:
    _, days_in_month = calendar.monthrange(year, month)
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year, month, days_in_month, 23, 59, 59, tzinfo=timezone.utc)
    pipeline = [
        {"$match": {"date": {"$gte": start, "$lte": end}}},
        {"$group": {"_id": {"$dayOfMonth": "$date"}, "total": {"$sum": "$total"}}},
        {"$sort": {"_id": 1}},
    ]
    data = {d: 0.0 for d in range(1, days_in_month + 1)}
    for r in get_sales().aggregate(pipeline):
        data[r["_id"]] = r["total"]
    return data


def top_products(year: int, month: int, limit: int = 5) -> list[dict]:
    _, days_in_month = calendar.monthrange(year, month)
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year, month, days_in_month, 23, 59, 59, tzinfo=timezone.utc)
    pipeline = [
        {"$match": {"date": {"$gte": start, "$lte": end}}},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_name",
            "total": {"$sum": {"$multiply": ["$items.unit_price", "$items.quantity"]}},
            "qty": {"$sum": "$items.quantity"},
        }},
        {"$sort": {"total": -1}},
        {"$limit": limit},
    ]
    return list(get_sales().aggregate(pipeline))
