from pathlib import Path

from src.models.sale import Sale

RECEIPTS_DIR = Path(__file__).parent.parent.parent / "receipts"


def receipt_text(sale: Sale, store_name: str = "SUPERMARKET") -> str:
    width = 34
    sep = "=" * width
    thin = "-" * width

    lines = [
        sep,
        store_name.center(width),
        sep,
        f"Date    : {sale.date.strftime('%d-%m-%Y %H:%M')}",
        f"Receipt : {sale.receipt_no}",
        f"Payment : {sale.payment_method.upper()}",
        "",
        f"{'Product':<16} {'Qty':>5} {'Price':>8}",
        thin,
    ]

    for item in sale.items:
        lines.append(f"{item.product_name:<16} {item.quantity:>5} {item.subtotal:>8.2f}")

    lines += [
        thin,
        f"TOTAL : {sale.total:.2f} DZD".rjust(width),
        "Thank you for your visit".center(width),
        sep,
    ]
    return "\n".join(lines) + "\n"


def generate(sale: Sale, store_name: str = "SUPERMARKET") -> str:
    RECEIPTS_DIR.mkdir(exist_ok=True)
    content = receipt_text(sale, store_name)
    path = RECEIPTS_DIR / f"receipt_{sale.receipt_no}.txt"
    path.write_text(content, encoding="utf-8")
    return str(path)
