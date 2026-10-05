import os

from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env file")

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

request = youtube.search().list(
    part="snippet",
    q="cybersecurity",
    type="video",
    maxResults=5
)

response = request.execute()

for item in response.get("items", []):
    video_id = item["id"]["videoId"]
    title = item["snippet"]["title"]

    print(f"Video ID: {video_id}")
    print(f"Title: {title}")
    print("-" * 60)