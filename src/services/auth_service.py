import bcrypt

from src.database import get_users
from src.services import AuthError


def _seed_admin() -> None:
    if get_users().count_documents({}) == 0:
        create_user("admin", "admin123", "admin")


def create_user(username: str, password: str, role: str = "staff") -> None:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    get_users().insert_one({
        "username": username,
        "password": hashed,
        "role": role,
    })


def list_users() -> list[dict]:
    return [
        {"username": u["username"], "role": u["role"]}
        for u in get_users().find({}, {"_id": 0, "password": 0})
    ]


def update_user(username: str, new_password: str | None, new_role: str | None) -> None:
    updates = {}
    if new_password:
        updates["password"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    if new_role:
        updates["role"] = new_role
    if updates:
        get_users().update_one({"username": username}, {"$set": updates})


def delete_user(username: str) -> None:
    get_users().delete_one({"username": username})


def authenticate(username: str, password: str) -> dict:
    _seed_admin()
    user = get_users().find_one({"username": username})
    if not user or not bcrypt.checkpw(password.encode(), user["password"]):
        raise AuthError("Invalid username or password.")
    return {"username": user["username"], "role": user["role"]}
