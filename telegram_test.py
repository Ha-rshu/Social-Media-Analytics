import os
import asyncio

from dotenv import load_dotenv
from telethon import TelegramClient


load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient(
    "sih_telegram_session",
    api_id,
    api_hash,
)


async def main():
    me = await client.get_me()

    print("\nTelegram connection successful!")
    print(f"Name: {me.first_name}")
    print(f"Username: @{me.username}")


async def run():
    await client.start()
    await main()
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(run())