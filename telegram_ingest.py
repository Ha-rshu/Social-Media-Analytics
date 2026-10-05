import os
import json
import asyncio
from datetime import timezone

from dotenv import load_dotenv
from telethon import TelegramClient, events


load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

SESSION_NAME = "sih_telegram_session"

# Use the SAME channel ID that worked earlier.
CHANNEL_ID = -1004483580830

OUTPUT_FILE = "telegram_messages.jsonl"


client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
)


def save_message(message):
    """Convert a Telegram message into our SIH standard format."""

    if not message.text:
        return

    timestamp = message.date

    if timestamp and timestamp.tzinfo is not None:
        timestamp = timestamp.astimezone(timezone.utc)

    record = {
        "id": message.id,
        "timestamp": timestamp.isoformat() if timestamp else None,
        "platform": "Telegram",
        "user_id": str(message.sender_id) if message.sender_id else None,
        "text": message.text,
        "target_user": None,
    }

    with open(
        OUTPUT_FILE,
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(
                record,
                ensure_ascii=False
            ) + "\n"
        )

    print("New Telegram message saved:")
    print(f"  ID: {record['id']}")
    print(f"  User: {record['user_id']}")
    print(f"  Text: {record['text']}")
    print()


@client.on(events.NewMessage(chats=CHANNEL_ID))
async def new_message_handler(event):
    save_message(event.message)


async def main():
    print("Telegram → SIH data collector started.")
    print("Waiting for new messages...")
    print(f"Output file: {OUTPUT_FILE}")
    print("Press Ctrl+C to stop.\n")

    await client.start()
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())