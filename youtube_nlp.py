import json
import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# -------------------------------------------------------------------
# SENTIMENT ANALYZER
# -------------------------------------------------------------------

analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of text using VADER.
    Returns sentiment label and sentiment scores.
    """

    if not isinstance(text, str) or not text.strip():
        return {
            "sentiment": "Neutral",
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 1.0,
            "compound_score": 0.0,
        }

    scores = analyzer.polarity_scores(text)

    compound = scores["compound"]

    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"

    return {
        "sentiment": label,
        "positive_score": scores["pos"],
        "negative_score": scores["neg"],
        "neutral_score": scores["neu"],
        "compound_score": compound,
    }


# -------------------------------------------------------------------
# TEXT CLEANING
# -------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Clean a YouTube comment for NLP processing.
    """

    if not isinstance(text, str):
        return ""

    # Remove URLs
    text = re.sub(
        r"https?://\S+|www\.\S+",
        "",
        text,
    )

    # Remove @mentions
    text = re.sub(
        r"@\w+",
        "",
        text,
    )

    # Remove hashtag symbol while preserving the word
    text = re.sub(
        r"#",
        "",
        text,
    )

    # Remove extra whitespace
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# -------------------------------------------------------------------
# LOAD YOUTUBE DATA
# -------------------------------------------------------------------

def load_youtube_data(file_path: str) -> list[dict]:
    """
    Load collected YouTube JSON data.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    return data.get("videos", [])


# -------------------------------------------------------------------
# EXTRACT AND ANALYZE COMMENTS
# -------------------------------------------------------------------

def extract_comments(videos: list[dict]) -> pd.DataFrame:
    """
    Convert nested YouTube comments into a flat DataFrame
    and perform sentiment analysis.
    """

    rows = []

    for video in videos:

        for comment in video.get(
            "comments",
            [],
        ):

            original_text = comment.get(
                "text",
                "",
            )

            cleaned = clean_text(
                original_text,
            )

            # Ignore empty comments
            if not cleaned:
                continue

            # Perform sentiment analysis
            sentiment = analyze_sentiment(
                cleaned,
            )

            rows.append(
                {
                    "video_id": video.get(
                        "video_id",
                        "",
                    ),
                    "video_title": video.get(
                        "title",
                        "",
                    ),
                    "channel": video.get(
                        "channel_title",
                        "",
                    ),
                    "author": comment.get(
                        "author",
                        "",
                    ),
                    "text": original_text,
                    "clean_text": cleaned,
                    "likes": comment.get(
                        "like_count",
                        0,
                    ),
                    "published_at": comment.get(
                        "published_at",
                        "",
                    ),

                    # Sentiment information
                    "sentiment": sentiment[
                        "sentiment"
                    ],
                    "positive_score": sentiment[
                        "positive_score"
                    ],
                    "negative_score": sentiment[
                        "negative_score"
                    ],
                    "neutral_score": sentiment[
                        "neutral_score"
                    ],
                    "compound_score": sentiment[
                        "compound_score"
                    ],
                }
            )

    return pd.DataFrame(rows)


# -------------------------------------------------------------------
# KEYWORD EXTRACTION
# -------------------------------------------------------------------

def extract_keywords(
    comments_df: pd.DataFrame,
    top_n: int = 20,
) -> list[tuple[str, float]]:
    """
    Extract important terms using TF-IDF.
    """

    if comments_df.empty:
        return []

    documents = comments_df[
        "clean_text"
    ].tolist()

    # Need at least one non-empty document
    documents = [
        document
        for document in documents
        if document.strip()
    ]

    if not documents:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=100,
    )

    try:

        matrix = vectorizer.fit_transform(
            documents,
        )

    except ValueError:

        return []

    scores = matrix.sum(
        axis=0,
    ).A1

    terms = vectorizer.get_feature_names_out()

    ranked = sorted(
        zip(terms, scores),
        key=lambda item: item[1],
        reverse=True,
    )

    return ranked[:top_n]


# -------------------------------------------------------------------
# SENTIMENT SUMMARY
# -------------------------------------------------------------------

def print_sentiment_summary(
    comments_df: pd.DataFrame,
) -> None:
    """
    Print sentiment distribution.
    """

    print("\n" + "=" * 70)
    print("SENTIMENT DISTRIBUTION")
    print("=" * 70)

    sentiment_counts = (
        comments_df["sentiment"]
        .value_counts()
    )

    total_comments = len(
        comments_df
    )

    for sentiment, count in (
        sentiment_counts.items()
    ):

        percentage = (
            count / total_comments
        ) * 100

        print(
            f"{sentiment:<10} "
            f"{count:>5} "
            f"({percentage:.1f}%)"
        )


# -------------------------------------------------------------------
# SENTIMENT SAMPLE
# -------------------------------------------------------------------

def print_sentiment_samples(
    comments_df: pd.DataFrame,
) -> None:
    """
    Display sample comments with sentiment results.
    """

    print("\n" + "=" * 70)
    print("COMMENT SENTIMENT SAMPLE")
    print("=" * 70)

    sample = comments_df[
        [
            "text",
            "sentiment",
            "compound_score",
        ]
    ].head(10)

    print(
        sample.to_string(
            index=False,
        )
    )


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

def main() -> None:
    """
    Main YouTube NLP processing pipeline.
    """

    data_directory = Path(
        "data/youtube"
    )

    # Find collected JSON files
    json_files = sorted(
        data_directory.glob(
            "*.json"
        )
    )

    if not json_files:

        print(
            "No YouTube JSON files found."
        )

        print(
            "Run youtube_collector.py first."
        )

        return

    # Use the latest collected dataset
    latest_file = json_files[-1]

    print(
        f"Loading: {latest_file}"
    )

    # Load videos
    videos = load_youtube_data(
        latest_file
    )

    # Extract comments + sentiment
    comments_df = extract_comments(
        videos
    )

    print("\n" + "=" * 70)
    print("YOUTUBE NLP PROCESSING")
    print("=" * 70)

    print(
        f"Videos: {len(videos)}"
    )

    print(
        f"Comments: {len(comments_df)}"
    )

    # Stop if there are no comments
    if comments_df.empty:

        print(
            "No comments available."
        )

        return

    # ---------------------------------------------------------------
    # CLEANED COMMENTS
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SAMPLE CLEANED COMMENTS")
    print("=" * 70)

    print(
        comments_df[
            [
                "text",
                "clean_text",
            ]
        ]
        .head(5)
        .to_string(
            index=False,
        )
    )

    # ---------------------------------------------------------------
    # SENTIMENT
    # ---------------------------------------------------------------

    print_sentiment_summary(
        comments_df
    )

    print_sentiment_samples(
        comments_df
    )

    # ---------------------------------------------------------------
    # KEYWORDS
    # ---------------------------------------------------------------

    keywords = extract_keywords(
        comments_df
    )

    print("\n" + "=" * 70)
    print("TOP KEYWORDS")
    print("=" * 70)

    if keywords:

        for word, score in keywords:

            print(
                f"{word:<25} "
                f"{score:.4f}"
            )

    else:

        print(
            "No keywords could be extracted."
        )

    # ---------------------------------------------------------------
    # SAVE PROCESSED DATA
    # ---------------------------------------------------------------

    output_directory = Path(
        "data/youtube"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_directory
        / "youtube_nlp_processed.csv"
    )

    comments_df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)

    print(
        f"Processed data saved to:"
    )

    print(
        output_file
    )


# -------------------------------------------------------------------
# PROGRAM ENTRY POINT
# -------------------------------------------------------------------

if __name__ == "__main__":
    main()
