class AppError(Exception):
    pass


class DuplicateCodeError(AppError):
    pass


class ProductInUseError(AppError):
    pass


class InsufficientStockError(AppError):
    def __init__(self, code: str, available: int, requested: int):
        self.code = code
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient stock for '{code}': requested {requested}, available {available}."
        )


class AuthError(AppError):
    pass
