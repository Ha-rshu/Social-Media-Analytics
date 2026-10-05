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


CHAT_NAME = "-1004483580830"


async def main():
    print(f"\nReading messages from: {CHAT_NAME}\n")

    async for message in client.iter_messages(-1004483580830, limit=20):
        if message.text:
            print(
                f"Message ID : {message.id}\n"
                f"Date       : {message.date}\n"
                f"Sender ID  : {message.sender_id}\n"
                f"Text       : {message.text}\n"
                f"{'-' * 60}"
            )


async def run():
    await client.start()
    await main()
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(run())