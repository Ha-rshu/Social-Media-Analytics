import os
import asyncio

from dotenv import load_dotenv
from telethon import TelegramClient


load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient(
    "sih_telegram_session",
    API_ID,
    API_HASH,
)


async def main():
    print("\nYour Telegram dialogs:\n")

    count = 0

    async for dialog in client.iter_dialogs():
        count += 1

        print(
            f"{count}. {dialog.name} "
            f"| ID: {dialog.id}"
        )

    print(f"\nTotal dialogs found: {count}")


async def run():
    await client.start()
    await main()
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(run())