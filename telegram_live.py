import os
import asyncio

from dotenv import load_dotenv
from telethon import TelegramClient, events


load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

# Use the same session created during authentication
client = TelegramClient(
    "sih_telegram_session",
    API_ID,
    API_HASH,
)

# IMPORTANT:
# Replace this with the channel ID that worked in telegram_read_messages.py
CHANNEL_ID = -1004483580830


@client.on(events.NewMessage(chats=CHANNEL_ID))
async def new_message_handler(event):
    message = event.message

    if not message.text:
        return

    print("\n" + "=" * 60)
    print("NEW TELEGRAM MESSAGE")
    print("=" * 60)

    print(f"Message ID : {message.id}")
    print(f"Date       : {message.date}")
    print(f"Sender ID  : {message.sender_id}")
    print(f"Text       : {message.text}")

    print("=" * 60)


async def main():
    print("Telegram live collector started...")
    print("Waiting for new messages...")
    print("Press Ctrl+C to stop.\n")

    await client.start()
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())