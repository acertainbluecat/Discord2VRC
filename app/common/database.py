from urllib.parse import quote_plus

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

from common.config import config

class Mongo:

    motor: AsyncIOMotorClient = None
    db: AIOEngine = None

    @staticmethod
    def connect():
        db_conf = config["database"]
        Mongo.motor = AsyncIOMotorClient(
            "mongodb://{username}:{password}@{host}:{port}/{database}".format(**db_conf))
        Mongo.db = AIOEngine(motor_client=Mongo.motor, database=db_conf["database"])

    @staticmethod
    def close():
        Mongo.motor.close()
