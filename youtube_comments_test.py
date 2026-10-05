import os

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env file")

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

# Replace this with a video ID from youtube_test.py
VIDEO_ID = "PASTE_VIDEO_ID_HERE"

try:
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=VIDEO_ID,
        maxResults=20,
        textFormat="plainText"
    )

    response = request.execute()

    comments = response.get("items", [])

    print(f"\nTotal comments returned: {len(comments)}\n")
    print("=" * 70)

    for i, item in enumerate(comments, start=1):
        comment = item["snippet"]["topLevelComment"]["snippet"]

        author = comment.get("authorDisplayName", "Unknown")
        text = comment.get("textDisplay", "")
        likes = comment.get("likeCount", 0)
        published = comment.get("publishedAt", "")

        print(f"\nComment #{i}")
        print(f"Author: {author}")
        print(f"Likes: {likes}")
        print(f"Published: {published}")
        print(f"Text: {text}")
        print("-" * 70)

except HttpError as error:
    print("YouTube API Error:")
    print(error)
    