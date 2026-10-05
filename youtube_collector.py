import os
from typing import Any

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")


class YouTubeCollector:
    """Collect video metadata and comments using YouTube Data API v3."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or API_KEY

        if not self.api_key:
            raise ValueError(
                "YOUTUBE_API_KEY not found. "
                "Check your .env file."
            )

        self.youtube = build(
            "youtube",
            "v3",
            developerKey=self.api_key
        )

    def search_videos(
        self,
        query: str,
        max_results: int = 10
    ) -> list[dict[str, Any]]:
        """Search YouTube for videos matching a keyword."""

        try:
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results
            )

            response = request.execute()

            videos = []

            for item in response.get("items", []):
                snippet = item.get("snippet", {})

                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "channel_id": snippet.get("channelId", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                })

            return videos

        except HttpError as error:
            print(f"YouTube search error: {error}")
            return []

    def get_video_details(
        self,
        video_id: str
    ) -> dict[str, Any] | None:
        """Get statistics and metadata for a video."""

        try:
            request = self.youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            )

            response = request.execute()

            items = response.get("items", [])

            if not items:
                return None

            video = items[0]

            snippet = video.get("snippet", {})
            statistics = video.get("statistics", {})

            return {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(
                    statistics.get("commentCount", 0)
                ),
            }

        except HttpError as error:
            print(f"Video details error: {error}")
            return None

    def get_comments(
        self,
        video_id: str,
        max_results: int = 100
    ) -> list[dict[str, Any]]:
        """Extract top-level comments from a YouTube video."""

        comments = []

        try:
            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(max_results, 100),
                textFormat="plainText"
            )

            response = request.execute()

            for item in response.get("items", []):
                comment_data = (
                    item["snippet"]
                    ["topLevelComment"]
                    ["snippet"]
                )

                comments.append({
                    "comment_id": (
                        item["snippet"]
                        ["topLevelComment"]
                        ["id"]
                    ),
                    "video_id": video_id,
                    "author": comment_data.get(
                        "authorDisplayName",
                        "Unknown"
                    ),
                    "text": comment_data.get(
                        "textDisplay",
                        ""
                    ),
                    "like_count": comment_data.get(
                        "likeCount",
                        0
                    ),
                    "published_at": comment_data.get(
                        "publishedAt",
                        ""
                    ),
                    "updated_at": comment_data.get(
                        "updatedAt",
                        ""
                    ),
                })

        except HttpError as error:
            print(f"Comment extraction error: {error}")

        return comments

    def collect(
        self,
        query: str,
        max_videos: int = 5,
        comments_per_video: int = 20
    ) -> dict[str, Any]:
        """Run the complete YouTube collection pipeline."""

        videos = self.search_videos(
            query=query,
            max_results=max_videos
        )

        collected_videos = []

        for video in videos:

            video_id = video["video_id"]

            details = self.get_video_details(
                video_id
            )

            comments = self.get_comments(
                video_id,
                max_results=comments_per_video
            )

            if details:
                video.update(details)

            video["comments"] = comments

            collected_videos.append(video)

        return {
            "query": query,
            "video_count": len(collected_videos),
            "videos": collected_videos
        }


if __name__ == "__main__":

    import json
    from datetime import datetime
    from pathlib import Path

    collector = YouTubeCollector()

    result = collector.collect(
        query="cybersecurity",
        max_videos=3,
        comments_per_video=10
    )

    output_dir = Path("data/youtube")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    output_file = (
        output_dir /
        f"youtube_{timestamp}.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n" + "=" * 70)
    print("YOUTUBE COLLECTION COMPLETE")
    print("=" * 70)

    print(f"Query: {result['query']}")
    print(f"Videos: {result['video_count']}")
    print(f"Saved to: {output_file}")

    total_comments = sum(
        len(video["comments"])
        for video in result["videos"]
    )

    print(f"Comments: {total_comments}")