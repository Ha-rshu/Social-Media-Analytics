import streamlit as st
import pandas as pd


demo_df = pd.DataFrame(
    {
        "platform": [
            "Instagram",
            "Twitter",
            "Instagram",
            "Facebook",
            "YouTube",
            "Twitter",
            "Instagram",
            "Facebook",
            "YouTube",
        ],
        "sentiment": [
            "POSITIVE",
            "NEGATIVE",
            "NEUTRAL",
            "POSITIVE",
            "NEGATIVE",
            "POSITIVE",
            "NEUTRAL",
            "POSITIVE",
            "NEGATIVE",
        ],
    }
)


def answer_question(question, dataframe):
    q = question.lower().strip()

    total = len(dataframe)
    platforms = dataframe["platform"].nunique()

    if "summary" in q or "summarize" in q:
        sentiment_counts = dataframe["sentiment"].value_counts()

        positive = int(sentiment_counts.get("POSITIVE", 0))
        negative = int(sentiment_counts.get("NEGATIVE", 0))
        neutral = int(sentiment_counts.get("NEUTRAL", 0))

        return (
            f"### 📊 Current Intelligence Summary\n\n"
            f"- **Total analyzed messages:** {total}\n"
            f"- **Platforms:** {platforms}\n"
            f"- **Positive:** {positive}\n"
            f"- **Negative:** {negative}\n"
            f"- **Neutral:** {neutral}\n\n"
            "This is currently a prototype response. "
            "The next version will generate this summary from your real dashboard data."
        )

    if "sentiment" in q:
        counts = dataframe["sentiment"].value_counts()

        return (
            "### 🧠 Sentiment Analysis\n\n"
            f"**Positive:** {int(counts.get('POSITIVE', 0))}\n\n"
            f"**Negative:** {int(counts.get('NEGATIVE', 0))}\n\n"
            f"**Neutral:** {int(counts.get('NEUTRAL', 0))}"
        )

    if "platform" in q:
        counts = dataframe["platform"].value_counts()

        lines = [
            f"- **{platform}:** {count} messages"
            for platform, count in counts.items()
        ]

        return "### 🌐 Platform Activity\n\n" + "\n".join(lines)

    if "hello" in q or "hi" in q:
        return (
            "Hello! 👋 I am your **SIH Social Media Intelligence Copilot**.\n\n"
            "Try asking:\n"
            "- Give me a summary\n"
            "- What is the sentiment?\n"
            "- Which platforms are active?"
        )

    return (
        "I understand that you are asking about the social-media data, "
        "but my full analytical reasoning engine is not connected yet.\n\n"
        "Try asking **\"Give me a summary\"** or **\"What is the sentiment?\"** "
        "for this first prototype."
    )


# ------------------------------------------------------------
# CHAT INTERFACE
# ------------------------------------------------------------

st.divider()

st.subheader("💬 Ask the Intelligence Copilot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


question = st.chat_input(
    "Ask anything about the social-media analysis..."
)

if question:
    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": question,
        }
    )

    response = answer_question(question, demo_df)

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    st.rerun()


# ------------------------------------------------------------
# SUGGESTED QUESTIONS
# ------------------------------------------------------------

st.divider()

st.markdown("### 💡 Suggested Questions")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📊 Analysis**")
    st.caption("Give me a summary")
    st.caption("What is happening in the data?")

with col2:
    st.markdown("**🧠 Sentiment**")
    st.caption("What is the sentiment?")
    st.caption("Are users mostly positive or negative?")

with col3:
    st.markdown("**🌐 Platforms**")
    st.caption("Which platforms are active?")
    st.caption("Compare the platforms")

st.caption("Prototype demo data for SIH Social Media Intelligence Copilot.")
