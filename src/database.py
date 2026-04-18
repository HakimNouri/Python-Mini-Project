import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database

load_dotenv()

_client: MongoClient | None = None
_db: Database | None = None


def get_db() -> Database:
    global _client, _db
    if _db is None:
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DB_NAME", "supermarket")
        _client = MongoClient(uri)
        _db = _client[db_name]
        _db["products"].create_index([("code", ASCENDING)], unique=True)
    return _db


def get_products():
    return get_db()["products"]


def get_sales():
    return get_db()["sales"]


def get_users():
    return get_db()["users"]
