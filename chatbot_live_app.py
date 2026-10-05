import streamlit as st
import pandas as pd

from telegram_adapter import load_telegram_data
from youtube_collector import YouTubeCollector


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Social Media Analytics Copilot",
    page_icon="💬",
    layout="wide",
)


# ============================================================
# YOUTUBE
# ============================================================

@st.cache_resource
def get_youtube_collector():
    return YouTubeCollector()


@st.cache_data(ttl=60)
def collect_youtube_data(
    query,
    max_videos=5,
    comments_per_video=50,
):
    collector = get_youtube_collector()

    return collector.collect(
        query=query,
        max_videos=max_videos,
        comments_per_video=comments_per_video,
    )


# ============================================================
# DATA COMBINATION
# ============================================================

def combine_data(telegram_df, youtube_df):
    frames = []

    if telegram_df is not None and not telegram_df.empty:
        frames.append(telegram_df)

    if youtube_df is not None and not youtube_df.empty:
        frames.append(youtube_df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    return combined


# ============================================================
# CHATBOT ANALYTICS
# ============================================================

def answer_question(question, df):
    """
    Rule-based analytics chatbot.
    Answers only from the connected raw dataset.
    """

    if df is None or df.empty:
        return (
            "I don't have any raw data yet. "
            "Please connect Telegram or fetch YouTube comments first."
        )

    q = question.lower().strip()

    # --------------------------------------------------------
    # TOTAL RECORDS
    # --------------------------------------------------------

    if (
        "how many messages" in q
        or "how many records" in q
        or "total messages" in q
        or "total records" in q
        or "how much data" in q
    ):
        return (
            f"📊 There are **{len(df):,} records** "
            "in the connected raw dataset."
        )

    # --------------------------------------------------------
    # PLATFORM COUNT
    # --------------------------------------------------------

    if (
        "platform" in q
        and (
            "how many" in q
            or "count" in q
            or "distribution" in q
        )
    ):
        if "platform" not in df.columns:
            return "Platform information is not available in the current dataset."

        platform_counts = df["platform"].value_counts()

        result = "### 📱 Platform Distribution\n\n"

        for platform, count in platform_counts.items():
            result += f"- **{platform}**: {count:,} records\n"

        return result

    # --------------------------------------------------------
    # MOST ACTIVE PLATFORM
    # --------------------------------------------------------

    if (
        "most active platform" in q
        or "which platform is more active" in q
        or "which platform is most active" in q
    ):
        if "platform" not in df.columns:
            return "Platform information is not available."

        counts = df["platform"].value_counts()

        if counts.empty:
            return "No platform data is available."

        platform = counts.index[0]
        count = counts.iloc[0]

        return (
            f"📱 Based on the connected raw data, "
            f"**{platform}** has the highest number of records "
            f"with **{count:,} records**."
        )

    # --------------------------------------------------------
    # YOUTUBE COUNT
    # --------------------------------------------------------

    if (
        "youtube" in q
        and (
            "how many" in q
            or "count" in q
            or "comments" in q
        )
    ):
        if "platform" not in df.columns:
            return "Platform information is not available."

        youtube_count = (
            df["platform"]
            .astype(str)
            .str.lower()
            .eq("youtube")
            .sum()
        )

        return (
            f"▶️ The connected dataset contains "
            f"**{youtube_count:,} YouTube records/comments**."
        )

    # --------------------------------------------------------
    # TELEGRAM COUNT
    # --------------------------------------------------------

    if (
        "telegram" in q
        and (
            "how many" in q
            or "count" in q
            or "messages" in q
        )
    ):
        if "platform" not in df.columns:
            return "Platform information is not available."

        telegram_count = (
            df["platform"]
            .astype(str)
            .str.lower()
            .eq("telegram")
            .sum()
        )

        return (
            f"✈️ The connected dataset contains "
            f"**{telegram_count:,} Telegram records/messages**."
        )

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    if (
        "user" in q
        or "users" in q
        or "authors" in q
        or "authors" in q
    ):
        if "user_id" not in df.columns:
            return "User information is not available."

        users = (
            df["user_id"]
            .dropna()
            .astype(str)
        )

        users = users[users != ""]

        if users.empty:
            return "No user information is available."

        counts = users.value_counts().head(10)

        result = "### 👥 Most Active Users / Authors\n\n"

        for user, count in counts.items():
            result += f"- **{user}** — {count:,} records\n"

        return result

    # --------------------------------------------------------
    # LATEST RECORDS
    # --------------------------------------------------------

    if (
        "latest" in q
        or "recent" in q
        or "newest" in q
    ):
        columns = [
            col
            for col in [
                "timestamp",
                "platform",
                "user_id",
                "text",
            ]
            if col in df.columns
        ]

        if not columns:
            return "No suitable fields are available for displaying recent records."

        latest = df.tail(5)[columns]

        return (
            "### 🕐 Latest Records\n\n"
            + latest.to_markdown(
                index=False
            )
        )

    # --------------------------------------------------------
    # RAW TEXT / MESSAGES
    # --------------------------------------------------------

    if (
        "show messages" in q
        or "show text" in q
        or "show posts" in q
        or "show comments" in q
        or "raw data" in q
    ):
        if "text" not in df.columns:
            return "Text data is not available."

        records = df["text"].dropna().astype(str).tail(10)

        if records.empty:
            return "No text records are available."

        result = "### 📝 Recent Text Records\n\n"

        for i, text in enumerate(records, start=1):
            result += f"**{i}.** {text[:500]}\n\n"

        return result

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    if (
        "summary" in q
        or "summarize" in q
        or "overview" in q
        or "give me a summary" in q
    ):
        result = "### 📊 Raw Data Summary\n\n"

        result += f"- **Total records:** {len(df):,}\n"

        if "platform" in df.columns:
            platform_counts = df["platform"].value_counts()

            result += "\n**Platforms:**\n"

            for platform, count in platform_counts.items():
                result += f"- {platform}: {count:,}\n"

        if "user_id" in df.columns:
            unique_users = df["user_id"].nunique()

            result += (
                f"\n- **Unique users/authors:** "
                f"{unique_users:,}\n"
            )

        if "text" in df.columns:
            text_count = df["text"].notna().sum()

            result += (
                f"- **Records containing text:** "
                f"{text_count:,}\n"
            )

        return result

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    return (
        "🤖 I can currently answer questions about the connected "
        "raw data such as:\n\n"
        "- Total number of records\n"
        "- Platform distribution\n"
        "- Most active platform\n"
        "- Telegram/YouTube record counts\n"
        "- Most active users/authors\n"
        "- Latest records\n"
        "- Raw messages/comments\n"
        "- Dataset summary\n\n"
        "Try asking one of these questions."
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Data Source")

source = st.sidebar.radio(
    "Choose source",
    [
        "Telegram Live",
        "YouTube API",
        "Combined Telegram + YouTube",
    ],
)


# ============================================================
# YOUTUBE SETTINGS
# ============================================================

youtube_df = pd.DataFrame()

if source in [
    "YouTube API",
    "Combined Telegram + YouTube",
]:

    st.sidebar.markdown("---")
    st.sidebar.subheader("▶️ YouTube")

    youtube_query = st.sidebar.text_input(
        "Search query",
        value="cybersecurity",
    )

    max_videos = st.sidebar.slider(
        "Videos",
        min_value=1,
        max_value=10,
        value=3,
    )

    comments_per_video = st.sidebar.slider(
        "Comments per video",
        min_value=10,
        max_value=100,
        value=30,
    )

    fetch_youtube = st.sidebar.button(
        "🔄 Fetch YouTube Data"
    )

    if fetch_youtube:
        with st.spinner("Fetching YouTube comments..."):
            try:
                youtube_df = collect_youtube_data(
                    youtube_query,
                    max_videos,
                    comments_per_video,
                )

                st.session_state.youtube_df = youtube_df

            except Exception as e:
                st.sidebar.error(
                    f"YouTube error: {e}"
                )

    elif "youtube_df" in st.session_state:
        youtube_df = st.session_state.youtube_df


# ============================================================
# TELEGRAM DATA
# ============================================================

telegram_df = pd.DataFrame()

if source in [
    "Telegram Live",
    "Combined Telegram + YouTube",
]:

    try:
        telegram_df = load_telegram_data()

    except Exception as e:
        st.sidebar.error(
            f"Telegram error: {e}"
        )


# ============================================================
# SELECT RAW DATA
# ============================================================

if source == "Telegram Live":

    raw_dataframe = telegram_df.copy()

elif source == "YouTube API":

    raw_dataframe = youtube_df.copy()

else:

    raw_dataframe = combine_data(
        telegram_df,
        youtube_df,
    )


# ============================================================
# PAGE HEADER
# ============================================================

st.title("💬 Social Media Analytics Copilot")

st.caption(
    "Ask questions about the real connected Telegram + YouTube raw data."
)


# ============================================================
# RAW DATA STATUS
# ============================================================

st.divider()

if raw_dataframe.empty:

    st.warning(
        "⚠️ No raw data is available yet."
    )

    st.info(
        "For Telegram, send messages to the connected source. "
        "For YouTube, enter a search query and fetch comments."
    )

    st.stop()


st.success(
    f"🟢 Real raw data connected — "
    f"{len(raw_dataframe):,} records loaded."
)


# ============================================================
# METRICS
# ============================================================

c1, c2, c3 = st.columns(3)

c1.metric(
    "Raw Records",
    len(raw_dataframe),
)

if "platform" in raw_dataframe.columns:

    c2.metric(
        "Platforms",
        raw_dataframe["platform"].nunique(),
    )

else:

    c2.metric(
        "Platforms",
        0,
    )


if "user_id" in raw_dataframe.columns:

    c3.metric(
        "Users / Authors",
        raw_dataframe["user_id"].nunique(),
    )

else:

    c3.metric(
        "Users / Authors",
        0,
    )


# ============================================================
# RAW DATA TABLE
# ============================================================

with st.expander("📋 View Raw Data"):

    st.dataframe(
        raw_dataframe,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# CHATBOT
# ============================================================

st.divider()

st.subheader("💬 Ask the Raw Data")

st.caption(
    "This version answers from the actual connected "
    "Telegram/YouTube raw dataset — not demo data."
)


# ============================================================
# CHAT HISTORY
# ============================================================

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []


for message in st.session_state.chat_history:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input(
    "Ask about the connected Telegram + YouTube data..."
)


if question:

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": question,
        }
    )

    answer = answer_question(
        question,
        raw_dataframe,
    )

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    st.rerun()


# ============================================================
# SUGGESTED QUESTIONS
# ============================================================

st.markdown("### 💡 Try these")

q1, q2, q3 = st.columns(3)


with q1:

    st.markdown(
        "**Data**\n\n"
        "• How many messages are there?\n\n"
        "• Give me a summary."
    )


with q2:

    st.markdown(
        "**Platforms**\n\n"
        "• Which platform is more active?\n\n"
        "• How many YouTube comments?"
    )


with q3:

    st.markdown(
        "**Users**\n\n"
        "• Who are the most active users?\n\n"
        "• Show me the latest records."
    )


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "Stage 2 prototype: real raw-data connection. "
    "Advanced sentiment, trend, network, and cybersecurity "
    "reasoning will be connected next."
)
