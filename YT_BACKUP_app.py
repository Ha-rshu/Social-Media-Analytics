import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st  
from streamlit_autorefresh import st_autorefresh
from transformers import pipeline

from telegram_adapter import load_telegram_data
from youtube_collector import YouTubeCollector

from modules.cybersecurity.threat_detection import analyze_threat
from modules.cybersecurity.url_analyzer import analyze_text_urls
from modules.cybersecurity.anomaly_detection import detect_anomalies

from modules.blockchain.hasher import generate_hash
from modules.blockchain.ledger import add_evidence, get_ledger
from modules.blockchain.verifier import verify_evidence, verify_chain


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Social Media Intelligence Framework",
    page_icon="🚀",
    layout="wide",
)


# ============================================================
# CUSTOM UI
# ============================================================

st.markdown(
    """
    <style>
        .main {
            background-color: #0B0F19;
            color: #E2E8F0;
        }

        h1 {
            color: #00F2FE !important;
            font-family: "Courier New", monospace;
        }

        h2, h3 {
            color: #FF007F !important;
            font-family: "Courier New", monospace;
        }

        div[data-testid="stMetricValue"] {
            color: #00F2FE !important;
            font-family: "Courier New", monospace;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    "📡 AI-DRIVEN SOCIAL MEDIA INTELLIGENCE & SECURITY FRAMEWORK"
)

st.caption(
    "SIH 2026 • Problem Statement 26152 • "
    "Social Media Analytics • NTRO"
)


# ============================================================
# AI SENTIMENT MODEL
# ============================================================

@st.cache_resource
def load_sentiment_model():
    """Load the local sentiment-analysis model."""
    return pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
    )


sentiment_model = load_sentiment_model()


def analyze_sentiment(text: str) -> str:
    """Analyze sentiment of a text string."""

    if not isinstance(text, str) or not text.strip():
        return "UNKNOWN"

    try:
        result = sentiment_model(text[:512])[0]
        return result["label"]

    except Exception:
        return "UNKNOWN"


# ============================================================
# DATA VALIDATION
# ============================================================

def validate_dataset(
    dataframe: pd.DataFrame,
) -> tuple[bool, list[str]]:

    required_columns = {
        "timestamp",
        "platform",
        "user_id",
        "text",
    }

    missing_columns = sorted(
        required_columns.difference(
            dataframe.columns
        )
    )

    return (
        len(missing_columns) == 0,
        missing_columns,
    )


# ============================================================
# DATA NORMALIZATION
# ============================================================

def normalize_dataset(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    result = dataframe.copy()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        errors="coerce",
        utc=True,
    )

    result["text"] = (
        result["text"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    result["platform"] = (
        result["platform"]
        .fillna("Unknown")
        .astype(str)
    )
    
    result["user_id"] = (
        result["user_id"]
        .fillna("unknown_user")
        .astype(str)
    )

    if "target_user" not in result.columns:
        result["target_user"] = None

    if "language" not in result.columns:
        result["language"] = "Unknown"

    if "region" not in result.columns:
        result["region"] = "Unknown"

    result = result.dropna(
        subset=["timestamp"]
    )

    return result.reset_index(drop=True)


# ============================================================
# AI PROCESSING
# ============================================================
def calculate_unified_risk_score(
    url_risk_score: float,
    threat_score: float,
    anomaly_score: float,
) -> int:
    """
    Combine cybersecurity signals into an explainable 0–100
    priority score.

    This is a prioritization signal, not a claim that an
    account or message is malicious.
    """

    score = (
        (url_risk_score * 0.30)
        + (threat_score * 0.40)
        + (anomaly_score * 0.30)
    )

    return int(round(min(100, max(0, score))))

def process_social_data(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    result = normalize_dataset(dataframe)

    result["sentiment"] = (
        result["text"].apply(analyze_sentiment)
    )

# --------------------------------------------------------
# CYBERSECURITY: URL ANALYSIS
# --------------------------------------------------------
    url_analysis = (
        result["text"]
        .apply(analyze_text_urls)
    )

    result["urls_found"] = url_analysis.apply(
        lambda item: ", ".join(item["urls"])
    )

    result["suspicious_urls"] = url_analysis.apply(
        lambda item: ", ".join(item["suspicious_urls"])
    )

    result["url_risk_score"] = url_analysis.apply(
        lambda item: item["url_risk_score"]
    )

    result["url_reasons"] = url_analysis.apply(
        lambda item: "; ".join(item["url_reasons"])
    )

# --------------------------------------------------------
# CYBERSECURITY: THREAT SCORING
# --------------------------------------------------------
    threat_analysis = result.apply(
        lambda row: analyze_threat(
            row["text"],
            {
                "url_risk_score": row["url_risk_score"],
            },
        ),
        axis=1,
    )

    result["threat_score"] = threat_analysis.apply(
        lambda item: item["threat_score"]
    )

    result["threat_level"] = threat_analysis.apply(
        lambda item: item["threat_level"]
    )

    result["threat_reasons"] = threat_analysis.apply(
        lambda item: "; ".join(item["threat_reasons"])
    )

# --------------------------------------------------------
# CYBERSECURITY: BEHAVIOURAL ANOMALIES DETECTION
# --------------------------------------------------------
    result = detect_anomalies(result)

    result["unified_risk_score"] = result.apply(
        lambda row: calculate_unified_risk_score(
            row["url_risk_score"],
            row["threat_score"],
            row["anomaly_score"],
        ),
        axis=1,
    )

    def classify_risk(score: int) -> str:
        if score >= 70:
            return "HIGH"
        if score >= 40:
            return "MEDIUM"
        return "LOW"

    result["risk_level"] = result["unified_risk_score"].apply(
        classify_risk
    )

# --------------------------------------------------------
# EVIDENCE INTEGRITY 
# --------------------------------------------------------
    evidence_hashes = []
    evidence_ids = []
    ledger_block_hashes = []

    for _, row in result.iterrows():
        evidence_payload = {
            "timestamp": str(row["timestamp"]),
            "platform": str(row["platform"]),
            "user_id": str(row["user_id"]),
            "text": str(row["text"]),
            "sentiment": str(row["sentiment"]),
            "threat_score": int(row["threat_score"]),
            "threat_level": str(row["threat_level"]),
            "url_risk_score": int(row["url_risk_score"]),
            "anomaly_score": float(row["anomaly_score"]),
            "unified_risk_score": int(row["unified_risk_score"]),
            "risk_level": str(row["risk_level"]),
        }

        evidence_hash = generate_hash(evidence_payload)
        evidence_id = f"EV-{evidence_hash[:12].upper()}"

        ledger_record = add_evidence(
            evidence_id=evidence_id,
            evidence_hash=evidence_hash,
            metadata={
                "platform": str(row["platform"]),
                "user_id": str(row["user_id"]),
                "threat_level": str(row["threat_level"]),
            },
        )

        evidence_hashes.append(evidence_hash)
        evidence_ids.append(evidence_id)
        ledger_block_hashes.append(
            ledger_record.get("block_hash", "")
        )

    result["evidence_hash"] = evidence_hashes
    result["evidence_id"] = evidence_ids
    result["ledger_block_hash"] = ledger_block_hashes

    return result

# ============================================================
# ADVANCED TREND DETECTION ENGINE
# ============================================================

def extract_trends(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    columns = [
        "keyword",
        "early_mentions",
        "recent_mentions",
        "growth",
        "platforms",
        "unique_users",
        "momentum_score",
        "trend_status",
    ]

    if dataframe.empty:
        return pd.DataFrame(columns=columns)

    working_df = dataframe.copy()

    working_df["timestamp"] = pd.to_datetime(
        working_df["timestamp"],
        errors="coerce",
        utc=True,
    )

    working_df = working_df.dropna(
        subset=["timestamp"]
    )

    if working_df.empty:
        return pd.DataFrame(columns=columns)

    stop_words = {
        "this",
        "that",
        "with",
        "from",
        "about",
        "there",
        "their",
        "have",
        "been",
        "will",
        "would",
        "could",
        "should",
        "people",
        "information",
        "latest",
        "today",
        "more",
        "very",
        "many",
        "some",
        "what",
        "when",
        "where",
        "which",
        "into",
        "than",
        "then",
        "they",
        "them",
        "your",
        "also",
        "just",
        "like",
        "because",
        "across",
        "discussion",
        "users",
        "user",
        "public",
        "development",
    }

    earliest_time = working_df["timestamp"].min()
    latest_time = working_df["timestamp"].max()

    time_range = latest_time - earliest_time

    midpoint = (
        earliest_time
        + time_range / 2
    )

    early_df = working_df[
        working_df["timestamp"] <= midpoint
    ]

    recent_df = working_df[
        working_df["timestamp"] > midpoint
    ]

    def extract_words(
        source_df: pd.DataFrame,
    ) -> list[str]:

        words = []

        for text in source_df["text"]:

            if not isinstance(text, str):
                continue

            tokens = text.lower().split()

            for token in tokens:

                cleaned = token.strip(
                    ".,!?;:\"'()[]{}#@"
                )

                if (
                    len(cleaned) >= 4
                    and cleaned.isalpha()
                    and cleaned not in stop_words
                ):
                    words.append(cleaned)

        return words

    early_words = extract_words(early_df)
    recent_words = extract_words(recent_df)

    if not recent_words:
        return pd.DataFrame(columns=columns)

    early_counts = pd.Series(
        early_words
    ).value_counts()

    recent_counts = pd.Series(
        recent_words
    ).value_counts()

    all_keywords = (
        set(early_counts.index)
        | set(recent_counts.index)
    )

    trend_records = []

    for keyword in all_keywords:

        early_mentions = int(
            early_counts.get(keyword, 0)
        )

        recent_mentions = int(
            recent_counts.get(keyword, 0)
        )

        if recent_mentions == 0:
            continue

        if early_mentions == 0:
            growth = 200.0
        else:
            growth = (
                (
                    recent_mentions
                    - early_mentions
                )
                / early_mentions
            ) * 100.0

        growth = max(
            -100.0,
            min(growth, 500.0),
        )

        keyword_pattern = rf"\b{keyword}\b"

        keyword_rows = working_df[
            working_df["text"]
            .str.lower()
            .str.contains(
                keyword_pattern,
                regex=True,
                na=False,
            )
        ]

        platform_count = (
            keyword_rows["platform"].nunique()
        )

        user_count = (
            keyword_rows["user_id"].nunique()
        )

        growth_component = (
            min(
                max(growth, 0) / 100.0,
                5.0,
            )
            * 50
        )

        frequency_component = (
            min(
                recent_mentions / 10.0,
                1.0,
            )
            * 25
        )

        platform_component = (
            min(
                platform_count / 2.0,
                1.0,
            )
            * 15
        )

        user_component = (
            min(
                user_count / 10.0,
                1.0,
            )
            * 10
        )

        momentum_score = (
            growth_component
            + frequency_component
            + platform_component
            + user_component
        )

        momentum_score = min(
            momentum_score,
            100.0,
        )

        if (
            momentum_score >= 70
            and growth >= 100
        ):
            trend_status = "🚨 RAPIDLY RISING"

        elif (
            momentum_score >= 50
            and growth >= 50
        ):
            trend_status = "📈 RISING"

        elif growth <= -50:
            trend_status = "📉 DECLINING"

        else:
            trend_status = "➡️ STABLE"

        trend_records.append(
            {
                "keyword": keyword,
                "early_mentions": early_mentions,
                "recent_mentions": recent_mentions,
                "growth": round(growth, 1),
                "platforms": platform_count,
                "unique_users": user_count,
                "momentum_score": round(
                    momentum_score,
                    1,
                ),
                "trend_status": trend_status,
            }
        )

    if not trend_records:
        return pd.DataFrame(columns=columns)

    trends_df = pd.DataFrame(
        trend_records
    )

    trends_df = trends_df.sort_values(
        by=[
            "momentum_score",
            "growth",
            "recent_mentions",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    )

    return trends_df.head(15).reset_index(
        drop=True
    )


# ============================================================
# NETWORK ANALYSIS
# ============================================================

def build_network(
    dataframe: pd.DataFrame,
) -> nx.DiGraph:

    graph = nx.DiGraph()

    for _, row in dataframe.iterrows():

        source = row["user_id"]
        target = row["target_user"]

        if (
            isinstance(target, str)
            and target
            and source != target
        ):
            graph.add_edge(
                source,
                target,
            )

    return graph

# ============================================================
# SECURITY-AWARE NODE PROFILES
# ============================================================

def build_security_node_profiles(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    required_columns = {
        "user_id",
        "threat_score",
        "anomaly_score",
        "url_risk_score",
        "unified_risk_score",
    }

    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        return pd.DataFrame()

    profiles = (
        dataframe.groupby("user_id", dropna=False)
        .agg(
            posts=("user_id", "size"),
            threat_score=("threat_score", "mean"),
            anomaly_score=("anomaly_score", "mean"),
            url_risk_score=("url_risk_score", "mean"),
            unified_risk_score=("unified_risk_score", "mean"),
        )
        .reset_index()
    )

    profiles["threat_score"] = profiles["threat_score"].round(2)
    profiles["anomaly_score"] = profiles["anomaly_score"].round(2)
    profiles["url_risk_score"] = profiles["url_risk_score"].round(2)
    profiles["unified_risk_score"] = (
        profiles["unified_risk_score"].round(2)
    )

    profiles["risk_level"] = profiles["unified_risk_score"].apply(
        lambda score: (
            "HIGH"
            if score >= 70
            else "MEDIUM"
            if score >= 40
            else "LOW"
        )
    )

    return profiles

# ============================================================
# NETWORK SECURITY METRICS
# ============================================================

def add_network_metrics(
    profiles: pd.DataFrame,
    graph: nx.DiGraph,
) -> pd.DataFrame:
    """
    Add network-level metrics to security-aware user profiles.

    Network importance is descriptive. It does not imply
    malicious behaviour.
    """

    if profiles.empty or graph.number_of_nodes() == 0:
        return profiles

    result = profiles.copy()

    result["in_degree"] = (
        result["user_id"]
        .map(dict(graph.in_degree()))
        .fillna(0)
        .astype(int)
    )

    result["out_degree"] = (
        result["user_id"]
        .map(dict(graph.out_degree()))
        .fillna(0)
        .astype(int)
    )

    result["total_connections"] = (
        result["in_degree"]
        + result["out_degree"]
    )

    pagerank = nx.pagerank(graph)

    result["pagerank"] = (
        result["user_id"]
        .map(pagerank)
        .fillna(0)
        .round(4)
    )

    return result


# ============================================================
# AGGREGATE PROFILE
# ============================================================
def build_demographic_profile(
    dataframe: pd.DataFrame,
) -> dict:
    """Build only fields that are actually present in source data.

    The framework does not invent age or interest values because neither
    Telegram nor YouTube provides reliable demographic attributes here.
    """
    return {
        "regional_distribution": (
            dataframe["region"].value_counts().to_dict()
            if "region" in dataframe.columns
            else {}
        ),
        "language_distribution": (
            dataframe["language"].value_counts().to_dict()
            if "language" in dataframe.columns
            else {}
        ),
    }


# ============================================================
# YOUTUBE INGESTION
# ============================================================
@st.cache_resource
def get_youtube_collector() -> YouTubeCollector:
    """Create and cache the YouTube API client."""
    return YouTubeCollector()


@st.cache_data(ttl=60, show_spinner=False)
def collect_youtube_data(
    query: str,
    max_videos: int,
    comments_per_video: int,
) -> pd.DataFrame:
    """Collect YouTube comments and map them to the common schema."""
    collector = get_youtube_collector()
    result = collector.collect(
        query=query,
        max_videos=max_videos,
        comments_per_video=comments_per_video,
    )

    records = []
    for video in result.get("videos", []):
        video_id = video.get("video_id", "")
        channel_id = video.get("channel_id", "")
        channel_title = video.get("channel_title", "")

        for comment in video.get("comments", []):
            records.append({
                "id": comment.get("comment_id", ""),
                "timestamp": comment.get("published_at", ""),
                "platform": "YouTube",
                "user_id": comment.get("author", "Unknown"),
                "target_user": (
                    f"channel:{channel_id}" if channel_id else None
                ),
                "text": comment.get("text", ""),
                "language": "Unknown",
                "region": "Unknown",
                "video_id": video_id,
                "video_title": video.get("title", ""),
                "channel_title": channel_title,
                "channel_id": channel_id,
                "comment_like_count": comment.get("like_count", 0),
            })

    return pd.DataFrame(records)


def combine_source_dataframes(
    telegram_df: pd.DataFrame,
    youtube_df: pd.DataFrame,
) -> pd.DataFrame:
    """Combine source data while preserving the common schema."""
    frames = [df for df in (telegram_df, youtube_df) if not df.empty]
    if not frames:
        return pd.DataFrame(
            columns=[
                "id", "timestamp", "platform", "user_id",
                "target_user", "text", "language", "region",
            ]
        )
    return pd.concat(frames, ignore_index=True, sort=False)


# ============================================================
# SIDEBAR
# ============================================================

data_source = st.sidebar.radio(
    "Select data source",
    [
        "Telegram Live",
        "YouTube API",
        "Combined: Telegram + YouTube",
    ],
)

# Telegram can refresh automatically; YouTube collection is cached to
# avoid unnecessary API quota consumption.
if data_source in {
    "Telegram Live",
    "Combined: Telegram + YouTube",
}:
    st_autorefresh(
        interval=5000,
        key="telegram_live_refresh",
    )

# ============================================================
# DATA SOURCE
# ============================================================
if data_source == "Telegram Live":
    raw_dataframe = load_telegram_data()
    if raw_dataframe.empty:
        st.warning("No Telegram messages found yet.")
        st.info(
            "Send a new message to your Telegram channel "
            "and refresh the dashboard."
        )
        st.stop()
    ingestion_status = "Live Telegram data successfully ingested"

elif data_source == "YouTube API":
    st.sidebar.markdown("### ▶️ YouTube Collection")
    youtube_query = st.sidebar.text_input(
        "Search query",
        value="cybersecurity",
    ).strip()
    max_videos = st.sidebar.slider(
        "Videos to search",
        min_value=1,
        max_value=10,
        value=5,
    )
    comments_per_video = st.sidebar.slider(
        "Comments per video",
        min_value=5,
        max_value=100,
        value=20,
    )

    if not youtube_query:
        st.info("Enter a YouTube search query in the sidebar.")
        st.stop()

    st.sidebar.caption(
        "YouTube results are cached for 60 seconds to reduce API quota usage."
    )
    if st.sidebar.button("🔄 Fetch YouTube Data", use_container_width=True):
        collect_youtube_data.clear()

    try:
        raw_dataframe = collect_youtube_data(
            youtube_query,
            max_videos,
            comments_per_video,
        )
    except Exception as exc:
        st.error(f"YouTube ingestion failed: {exc}")
        st.info(
            "Check that YOUTUBE_API_KEY is present in your .env file "
            "and that the YouTube Data API v3 is enabled."
        )
        st.stop()

    if raw_dataframe.empty:
        st.warning(
            "YouTube returned no comments for the selected search results."
        )
        st.stop()

    ingestion_status = (
        f"YouTube API data successfully ingested "
        f"({len(raw_dataframe)} comments)"
    )

else:
    telegram_dataframe = load_telegram_data()

    st.sidebar.markdown("### ▶️ YouTube Collection")
    youtube_query = st.sidebar.text_input(
        "YouTube search query",
        value="cybersecurity",
    ).strip()
    max_videos = st.sidebar.slider(
        "YouTube videos",
        min_value=1,
        max_value=10,
        value=5,
    )
    comments_per_video = st.sidebar.slider(
        "YouTube comments/video",
        min_value=5,
        max_value=100,
        value=20,
    )

    if not youtube_query:
        st.info("Enter a YouTube search query in the sidebar.")
        st.stop()

    if st.sidebar.button("🔄 Refresh YouTube Data", use_container_width=True):
        collect_youtube_data.clear()

    try:
        youtube_dataframe = collect_youtube_data(
            youtube_query,
            max_videos,
            comments_per_video,
        )
    except Exception as exc:
        st.error(f"YouTube ingestion failed: {exc}")
        st.stop()

    raw_dataframe = combine_source_dataframes(
        telegram_dataframe,
        youtube_dataframe,
    )

    if raw_dataframe.empty:
        st.warning("No Telegram or YouTube data is available yet.")
        st.stop()

    ingestion_status = (
        "Combined Telegram + YouTube data successfully ingested"
    )

# ============================================================
# PROCESS DATA
# ============================================================

with st.spinner(
    "Running AI processing..."
):

    df = process_social_data(
        raw_dataframe
    )

# ============================================================
# TELEGRAM LIVE FEED
# ============================================================

if data_source == "Telegram Live":

    st.subheader("📡 Telegram Live Feed")

    # --------------------------------------------------------
    # LIVE STATUS
    # --------------------------------------------------------

    feed_col1, feed_col2, feed_col3 = st.columns(3)

    feed_col1.metric(
        "🟢 Live Status",
        "CONNECTED",
    )

    feed_col2.metric(
        "Messages Collected",
        len(raw_dataframe),
    )

    if not raw_dataframe.empty:

        latest_timestamp = raw_dataframe[
            "timestamp"
        ].max()

        latest_timestamp = latest_timestamp.tz_convert(
            "Asia/Kolkata"
        )

        feed_col3.metric(
            "Latest Message",
            latest_timestamp.strftime(
                "%H:%M:%S"
            ),
        )

    else:

        feed_col3.metric(
            "Latest Message",
            "—",
        )

    # --------------------------------------------------------
    # RECENT MESSAGES
    # --------------------------------------------------------

    st.markdown("### 📨 Recent Messages")

    if raw_dataframe.empty:

        st.info(
            "Waiting for Telegram messages..."
        )

    else:

        # Use processed dataframe so sentiment is included
        recent_messages = (
            df
            .sort_values(
                "timestamp",
                ascending=False,
            )
            .head(10)
            .copy()
        )

        recent_messages = recent_messages[
            [
                "timestamp",
                "platform",
                "user_id",
                "text",
                "sentiment",
            ]
        ]

        # Convert UTC → Indian Standard Time
        recent_messages["timestamp"] = (
            recent_messages["timestamp"]
            .dt.tz_convert("Asia/Kolkata")
            .dt.strftime("%H:%M:%S")
        )

        recent_messages = (
            recent_messages.rename(
                columns={
                    "timestamp": "Time",
                    "platform": "Platform",
                    "user_id": "User / Channel",
                    "text": "Message",
                    "sentiment": "AI Sentiment",
                }
            )
        )

        st.dataframe(
            recent_messages,
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "Live feed automatically refreshes every 5 seconds."
    )
# ============================================================
# YOUTUBE FEED
# ============================================================
if data_source == "YouTube API":
    st.subheader("▶️ YouTube Intelligence Feed")

    feed_col1, feed_col2, feed_col3 = st.columns(3)
    feed_col1.metric("🟢 API Status", "CONNECTED")
    feed_col2.metric("Comments Collected", len(raw_dataframe))

    latest_timestamp = pd.to_datetime(
        raw_dataframe["timestamp"], errors="coerce", utc=True
    ).max()
    feed_col3.metric(
        "Latest Comment",
        latest_timestamp.tz_convert("Asia/Kolkata").strftime("%H:%M:%S")
        if pd.notna(latest_timestamp)
        else "—",
    )

    recent_youtube = (
        df.sort_values("timestamp", ascending=False)
        .head(10)
        .copy()
    )

    youtube_columns = [
        column for column in [
            "timestamp", "user_id", "text", "sentiment",
            "video_title", "channel_title", "comment_like_count",
        ]
        if column in recent_youtube.columns
    ]

    st.dataframe(
        recent_youtube[youtube_columns],
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "YouTube comments are collected through YouTube Data API v3. "
        "The dashboard analyzes the returned comments; it does not stream "
        "all YouTube activity globally."
    )

# ============================================================
# ANALYTICS
# ============================================================

trends = extract_trends(df)

graph = build_network(df)

security_profiles = build_security_node_profiles(df)

security_profiles = add_network_metrics(
    security_profiles,
    graph,
)

demographic_profile = (
    build_demographic_profile(df)
)


# ============================================================
# HEADER STATUS
# ============================================================

st.success(
    "🟢 " + ingestion_status
)

st.info(
    "Data Flow: "
    "Ingestion → Validation → Normalization → "
    "AI Processing → Intelligence Analytics"
)


# ============================================================
# KPI SECTION
# ============================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Analyzed Posts",
    len(df),
)

col2.metric(
    "Platforms",
    df["platform"].nunique(),
)

col3.metric(
    "Unique Users",
    df["user_id"].nunique(),
)

col4.metric(
    "Network Connections",
    graph.number_of_edges(),
)


st.divider()


# ============================================================
# TABS
# ============================================================

(
    tab_overview,
    tab_sentiment,
    tab_demographics,
    tab_trends,
    tab_network,
    tab_security,
    tab_evidence,
) = st.tabs(
    [
        "📊 Overview",
        "🧠 Sentiment Analysis",
        "👥 Demographics",
        "📈 Trend Detection",
        "🕸️ Network Analysis",
        "🛡️ Cybersecurity",
        "⛓️ Evidence Integrity",
    ]
)

# ============================================================
# OVERVIEW
# ============================================================

with tab_overview:

    st.subheader(
        "📊 Cross-Platform Activity"
    )

    platform_counts = (
        df["platform"]
        .value_counts()
        .reset_index()
    )

    platform_counts.columns = [
        "platform",
        "posts",
    ]

    platform_fig = px.bar(
        platform_counts,
        x="platform",
        y="posts",
        title="Activity by Platform",
    )

    st.plotly_chart(
        platform_fig,
        width="stretch",
        key="platform_activity_chart",
    )

    st.subheader(
        "⏱️ Conversation Timeline"
    )

    timeline = (
        df.groupby(
            pd.Grouper(
                key="timestamp",
                freq="15min",
            )
        )
        .size()
        .reset_index(
            name="activity"
        )
    )

    timeline_fig = px.line(
        timeline,
        x="timestamp",
        y="activity",
        markers=True,
        title=(
            "Social Conversation "
            "Activity Timeline"
        ),
    )

    st.plotly_chart(
        timeline_fig,
        width="stretch",
        key="conversation_timeline_chart",
    )


# ============================================================
# SENTIMENT
# ============================================================

with tab_sentiment:

    st.subheader(
        "🧠 AI-Based Sentiment Inference"
    )

    sentiment_counts = (
        df["sentiment"]
        .value_counts()
        .reset_index()
    )

    sentiment_counts.columns = [
        "sentiment",
        "count",
    ]

    sentiment_col1, sentiment_col2 = (
        st.columns(2)
    )

    with sentiment_col1:

        sentiment_fig = px.pie(
            sentiment_counts,
            names="sentiment",
            values="count",
            hole=0.45,
            title="Sentiment Distribution",
        )

        st.plotly_chart(
            sentiment_fig,
            width="stretch",
            key="sentiment_distribution_chart",
        )

    with sentiment_col2:

        st.dataframe(
            df[
                [
                    "timestamp",
                    "platform",
                    "user_id",
                    "text",
                    "sentiment",
                ]
            ]
            .sort_values(
                "timestamp",
                ascending=False,
            ),
            width="stretch",
            hide_index=True,
        )


# ============================================================
# DEMOGRAPHICS / SOURCE ATTRIBUTES
# ============================================================
with tab_demographics:
    st.subheader("👥 Source & Audience Attributes")
    st.caption(
        "Only attributes actually supplied by the connected sources are "
        "shown. Age and interest are not fabricated from prototype values."
    )

    region_col, language_col = st.columns(2)

    with region_col:
        region_data = pd.DataFrame(
            {
                "Region": list(
                    demographic_profile["regional_distribution"].keys()
                ),
                "Posts": list(
                    demographic_profile["regional_distribution"].values()
                ),
            }
        )
        if region_data.empty:
            st.info("Region information is not available from the current sources.")
        else:
            region_fig = px.bar(
                region_data,
                x="Region",
                y="Posts",
                title="Regional Activity Distribution",
            )
            st.plotly_chart(
                region_fig,
                width="stretch",
                key="regional_activity_chart",
            )

    with language_col:
        language_data = pd.DataFrame(
            {
                "Language": list(
                    demographic_profile["language_distribution"].keys()
                ),
                "Posts": list(
                    demographic_profile["language_distribution"].values()
                ),
            }
        )
        if language_data.empty:
            st.info("Language information is not available from the current sources.")
        else:
            language_fig = px.bar(
                language_data,
                x="Language",
                y="Posts",
                title="Language Distribution",
            )
            st.plotly_chart(
                language_fig,
                width="stretch",
                key="language_distribution_chart",
            )

    st.warning(
        "Age and interest inference is intentionally disabled until a "
        "validated, privacy-compliant inference layer is added."
    )


# ============================================================
# ADVANCED TREND DETECTION
# ============================================================

with tab_trends:

    st.subheader(
        "📈 Real-Time Trend & Topic Intelligence"
    )

    st.caption(
        "The framework compares historical and recent "
        "conversation activity to identify emerging "
        "topics and measure their momentum."
    )

    if not trends.empty:

        rapid_count = len(
            trends[
                trends["trend_status"]
                == "🚨 RAPIDLY RISING"
            ]
        )

        rising_count = len(
            trends[
                trends["trend_status"]
                == "📈 RISING"
            ]
        )

        highest_momentum = float(
            trends["momentum_score"].max()
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "🚨 Rapidly Rising",
            rapid_count,
        )

        c2.metric(
            "📈 Rising Topics",
            rising_count,
        )

        c3.metric(
            "🔎 Topics Tracked",
            len(trends),
        )

        c4.metric(
            "⚡ Highest Momentum",
            f"{highest_momentum:.1f}/100",
        )

        st.divider()

        st.markdown(
            "### 🔥 Emerging Topic Momentum"
        )

        chart_data = (
            trends
            .sort_values(
                "momentum_score",
                ascending=True,
            )
            .tail(10)
        )

        momentum_fig = px.bar(
            chart_data,
            x="momentum_score",
            y="keyword",
            orientation="h",
            title="Topic Momentum Score",
            labels={
                "momentum_score": "Momentum Score",
                "keyword": "Detected Topic",
            },
        )

        momentum_fig.update_layout(
            xaxis_range=[0, 100]
        )

        st.plotly_chart(
            momentum_fig,
            width="stretch",
            key="topic_momentum_chart",
        )

        st.markdown(
            "### 🧠 Detected Topic Intelligence"
        )

        display_trends = trends.copy()

        display_trends["growth"] = (
            display_trends["growth"]
            .map(lambda value: f"{value:.1f}%")
        )

        display_trends["momentum_score"] = (
            display_trends["momentum_score"]
            .map(lambda value: f"{value:.1f}")
        )

        st.dataframe(
            display_trends[
                [
                    "keyword",
                    "early_mentions",
                    "recent_mentions",
                    "growth",
                    "platforms",
                    "unique_users",
                    "momentum_score",
                    "trend_status",
                ]
            ],
            width="stretch",
            hide_index=True,
        )

        st.markdown(
            "### 🚨 Intelligence Alert"
        )

        top_topic = trends.iloc[0]

        if (
            top_topic["trend_status"]
            == "🚨 RAPIDLY RISING"
        ):

            st.error(
                f"Potential rapidly emerging "
                f"narrative detected: "
                f"**{top_topic['keyword']}** "
                f"with a momentum score of "
                f"**{top_topic['momentum_score']:.1f}/100**."
            )

        elif (
            top_topic["trend_status"]
            == "📈 RISING"
        ):

            st.warning(
                f"Emerging topic detected: "
                f"**{top_topic['keyword']}** "
                f"with "
                f"**{top_topic['growth']:.1f}%** "
                f"growth."
            )

        else:

            st.info(
                "No rapidly accelerating topic "
                "was detected in the current "
                "observation window."
            )

        st.markdown(
            "### 🌐 Cross-Platform Topic Spread"
        )

        spread_data = (
            trends[
                [
                    "keyword",
                    "platforms",
                    "unique_users",
                ]
            ]
            .sort_values(
                "platforms",
                ascending=False,
            )
            .head(10)
        )

        spread_fig = px.bar(
            spread_data,
            x="keyword",
            y=[
                "platforms",
                "unique_users",
            ],
            barmode="group",
            title=(
                "Platform & User Spread "
                "of Detected Topics"
            ),
        )

        st.plotly_chart(
            spread_fig,
            width="stretch",
            key="cross_platform_spread_chart",
        )

    else:

        st.info(
            "Insufficient conversation data "
            "for trend detection."
        )


# ============================================================
# NETWORK ANALYSIS
# ============================================================

with tab_network:

    st.subheader(
        "🕸️ Information & Influence Network"
    )

    if graph.number_of_nodes() > 0:

        centrality = nx.degree_centrality(graph)

        top_nodes = sorted(
            centrality.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:5]

        st.markdown(
            "### 🔗 High-Connectivity Nodes"
        )

        metric_columns = st.columns(
            len(top_nodes)
        )

        for column, (node, score) in zip(
            metric_columns,
            top_nodes,
        ):

            column.metric(
                label=node,
                value=f"{score:.3f}",
            )

        positions = nx.spring_layout(
            graph,
            seed=42,
        )

        edge_x = []
        edge_y = []

        for source, target in graph.edges():

            x0, y0 = positions[source]
            x1, y1 = positions[target]

            edge_x.extend(
                [
                    x0,
                    x1,
                    None,
                ]
            )

            edge_y.extend(
                [
                    y0,
                    y1,
                    None,
                ]
            )

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={
                "width": 1,
            },
            hoverinfo="none",
        )

        node_x = [
            positions[node][0]
            for node in graph.nodes()
        ]

        node_y = [
            positions[node][1]
            for node in graph.nodes()
        ]

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=list(graph.nodes()),
            textposition="top center",
            marker={
                "size": 12,
            },
        )

        network_fig = go.Figure(
            data=[
                edge_trace,
                node_trace,
            ]
        )

        network_fig.update_layout(
            showlegend=False,
            height=600,
            plot_bgcolor="#0B0F19",
            paper_bgcolor="#0B0F19",
            font={
                "color": "#E2E8F0",
            },
            xaxis={
                "visible": False,
            },
            yaxis={
                "visible": False,
            },
        )

        st.plotly_chart(
            network_fig,
            width="stretch",
            key="network_topology_chart",
        )

    else:

        st.warning(
            "No interaction relationships available."
        )

    st.divider()

    st.markdown("### 🛡️ Security-Aware Node Profiles")

    if security_profiles.empty:
        st.info("Security node profiles are not available.")
    else:
        st.dataframe(
            security_profiles.sort_values(
                "unified_risk_score",
                ascending=False,
            ).head(20),
            width="stretch",
            hide_index=True,
        )


# ============================================================
# CYBERSECURITY
# ============================================================

with tab_security:

    st.subheader("🛡️ Cybersecurity Intelligence")
    st.caption(
        "Explainable local indicators for suspicious URLs, "
        "threat patterns, and unusual activity."
    )

    threat_count = int((df["threat_level"] != "LOW").sum())
    high_threat_count = int((df["threat_level"] == "HIGH").sum())
    suspicious_url_count = int(
        (df["url_risk_score"] >= 30).sum()
    )
    anomaly_count = int(df["anomaly_flag"].sum())

    security_col1, security_col2, security_col3, security_col4 = (
        st.columns(4)
    )

    security_col1.metric(
        "Messages Analyzed",
        len(df),
    )

    security_col2.metric(
        "Threat Indicators",
        threat_count,
    )

    security_col3.metric(
        "Suspicious URLs",
        suspicious_url_count,
    )

    security_col4.metric(
        "Anomalies",
        anomaly_count,
    )

    st.divider()

    st.markdown("### 🚨 Threat Intelligence")

    threat_display = (
        df[
            [
                "timestamp",
                "platform",
                "user_id",
                "threat_level",
                "threat_score",
                "threat_reasons",
                "unified_risk_score",
                "risk_level",
                "text",
            ]
        ]
        .sort_values(
            "threat_score",
            ascending=False,
        )
        .head(20)
        .copy()
    )

    st.dataframe(
        threat_display,
        width="stretch",
        hide_index=True,
    )

    st.markdown("### 🔗 URL Security")

    url_display = (
        df[
            [
                "platform",
                "user_id",
                "urls_found",
                "suspicious_urls",
                "url_risk_score",
                "url_reasons",
            ]
        ]
        .loc[df["urls_found"].astype(bool)]
        .sort_values(
            "url_risk_score",
            ascending=False,
        )
        .head(20)
    )

    if url_display.empty:
        st.info(
            "No URLs were found in the current dataset."
        )
    else:
        st.dataframe(
            url_display,
            width="stretch",
            hide_index=True,
        )

    st.markdown("### 📊 Behavioural Anomalies")

    anomaly_display = (
        df[
            [
                "timestamp",
                "platform",
                "user_id",
                "anomaly_score",
                "anomaly_flag",
                "anomaly_reasons",
                "text",
            ]
        ]
        .loc[df["anomaly_flag"]]
        .sort_values(
            "anomaly_score",
            ascending=False,
        )
        .head(20)
    )

    if anomaly_display.empty:
        st.success(
            "No high-confidence activity anomalies were detected "
            "by the current prototype rules."
        )
    else:
        st.dataframe(
            anomaly_display,
            width="stretch",
            hide_index=True,
        )


# ============================================================
# EVIDENCE INTEGRITY
# ============================================================

with tab_evidence:

    st.subheader("⛓️ Blockchain-Style Evidence Integrity")
    st.caption(
        "A local append-only hash chain provides tamper-evident "
        "evidence records for the prototype."
    )

    ledger_entries = get_ledger()
    chain_status = verify_chain()

    evidence_col1, evidence_col2, evidence_col3 = st.columns(3)

    evidence_col1.metric(
        "Evidence Records",
        len(ledger_entries),
    )

    evidence_col2.metric(
        "Chain Status",
        "VERIFIED" if chain_status["verified"] else "FAILED",
    )

    evidence_col3.metric(
        "Latest Block",
        (
            ledger_entries[-1]["block_index"]
            if ledger_entries
            else 0
        ),
    )

    if chain_status["verified"]:
        st.success(
            "✅ " + chain_status["message"]
        )
    else:
        st.error(
            "⚠️ " + chain_status["message"]
        )

    st.markdown("### 🔐 Evidence Records")

    if ledger_entries:
        ledger_display = pd.DataFrame(ledger_entries)

        display_columns = [
            "block_index",
            "evidence_id",
            "evidence_hash",
            "timestamp",
            "previous_block_hash",
            "block_hash",
        ]

        st.dataframe(
            ledger_display[display_columns],
            width="stretch",
            hide_index=True,
        )

        st.markdown("### 🔎 Verify Evidence")

        selected_evidence = st.selectbox(
            "Select an evidence ID",
            [
                entry["evidence_id"]
                for entry in ledger_entries
            ],
        )

        selected_entry = next(
            entry
            for entry in ledger_entries
            if entry["evidence_id"] == selected_evidence
        )

        if st.button(
            "Verify Selected Evidence",
            key="verify_selected_evidence",
        ):
            verification = verify_evidence(
                selected_entry["evidence_hash"]
            )

            if verification["verified"]:
                st.success(
                    "✅ " + verification["message"]
                )
            else:
                st.error(
                    "⚠️ " + verification["message"]
                )

    else:
        st.info(
            "No evidence has been recorded yet."
        )
# ============================================================
# PROCESSED DATA
# ============================================================

with st.expander(
    "📋 View Processed Social Data"
):

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# PROTOTYPE DISCLAIMER
# ============================================================

st.divider()

st.caption(
    "Data-source note: This dashboard uses connected Telegram data and "
    "YouTube Data API comments. Generated/demo social-media records and "
    "manual CSV ingestion have been removed from this version. X, Instagram, "
    "Facebook, and Reddit are not connected yet."
)
