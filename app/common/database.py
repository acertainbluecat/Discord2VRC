from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

from common.config import config


class Mongo:

    motor: AsyncIOMotorClient
    db: AIOEngine

    @staticmethod
    def connect() -> None:
        """Sets up connection to MongoDB via motor
        and Odmantic's AIOEngine
        """
        Mongo.motor = AsyncIOMotorClient(
            "mongodb://{username}:{password}@{host}:{port}/{database}".format(
                **config["database"]
            )
        )
        Mongo.db = AIOEngine(
            motor_client=Mongo.motor, database=config["database"]["database"]
        )

    @staticmethod
    def close() -> None:
        """Close motor connection to mongodb"""
        Mongo.motor.close()
