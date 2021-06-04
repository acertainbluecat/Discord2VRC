from urllib.parse import quote_plus

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

from common.config import DB_CONF

class Mongo:

    motor: AsyncIOMotorClient = None
    db: AIOEngine = None

    @staticmethod
    def connect():
        DB_CONF["password"] = quote_plus(DB_CONF["password"])
        Mongo.motor = AsyncIOMotorClient(
            "mongodb://{username}:{password}@{host}:{port}/{database_name}".format(**DB_CONF))
        Mongo.db = AIOEngine(motor_client=Mongo.motor, database=DB_CONF["database_name"])

    @staticmethod
    def close():
        Mongo.motor.close()
