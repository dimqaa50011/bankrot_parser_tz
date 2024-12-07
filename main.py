import asyncio
import os

from parser import BankruptParser
from storage import Storage
from logger import logger


def get_target_data(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as fp:
            data = fp.readlines()

        user_data = []
        for item in data:
            try:
                username, birthday = item.strip("\n").split("||")
                user_data.append({"username": username, "birthday": birthday})
            except ValueError:
                logger.warning("Invalid separator character. Must be ||.")

        logger.info(f"Found targer data {user_data}")

        return user_data
    logger.info(f"File {file} not found")


async def main():
    user_data = get_target_data("target.txt")
    if user_data:
        storage = Storage()
        parser = BankruptParser(storage)
        await parser.start(data=user_data, debug=False)
        storage.print_items()


if __name__ == "__main__":
    asyncio.run(main())
