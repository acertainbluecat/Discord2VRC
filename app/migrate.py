import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from common.config import config

motor = AsyncIOMotorClient(
    "mongodb://{username}:{password}@{host}:{port}/{database}".format(
        **config["database"]
    )
)
db = motor[config["database"]["database"]]


async def setup_collections():
    await db.image.create_index("created_at")
    await db.image.create_index("channel")
    await db.image.create_index("attachment_id")
    await db.image.create_index("deleted")
    await db.channel.create_index("alias")


if __name__ == "__main__":

    print("Setting up indexes for database")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_collections())
    print("done!")
