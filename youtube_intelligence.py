import re
from collections import Counter
from pathlib import Path

import pandas as pd
import spacy

# -------------------------------------------------------------------
# LOAD NLP MODEL
# -------------------------------------------------------------------

try:
    nlp = spacy.load("en_core_web_sm")

except OSError:

    print(
        "spaCy English model not found."
    )

    print(
        "Run:"
    )

    print(
        "python -m spacy download en_core_web_sm"
    )

    raise SystemExit(1)


# -------------------------------------------------------------------
# ENTITY EXTRACTION
# -------------------------------------------------------------------

def extract_entities(text: str) -> list[dict]:
    """
    Extract named entities from text using spaCy.
    """

    if not isinstance(text, str):
        return []

    doc = nlp(text)

    entities = []

    for entity in doc.ents:

        entities.append(
            {
                "text": entity.text,
                "label": entity.label_,
            }
        )

    return entities


# -------------------------------------------------------------------
# KEYWORD EXTRACTION
# -------------------------------------------------------------------

def extract_topic_terms(
    text: str,
    top_n: int = 10,
) -> list[str]:
    """
    Extract noun-based topic terms from text.
    """

    if not isinstance(text, str):
        return []

    doc = nlp(text)

    terms = []

    for token in doc:

        # Ignore punctuation, spaces and stop words
        if (
            token.is_stop
            or token.is_punct
            or token.is_space
        ):
            continue

        # Focus on nouns/proper nouns/adjectives
        if token.pos_ in {
            "NOUN",
            "PROPN",
            "ADJ",
        }:

            word = token.lemma_.lower()

            # Basic quality filtering
            if (
                len(word) >= 3
                and word.isalpha()
            ):
                terms.append(word)

    counts = Counter(terms)

    return [
        word
        for word, _ in counts.most_common(
            top_n
        )
    ]


# -------------------------------------------------------------------
# PROCESS DATASET
# -------------------------------------------------------------------

def process_dataset(
    input_file: str,
) -> pd.DataFrame:
    """
    Add entity and topic information
    to the processed YouTube dataset.
    """

    df = pd.read_csv(
        input_file
    )

    if df.empty:
        return df

    entity_results = []
    topic_results = []

    for text in df["clean_text"].fillna(""):

        # Entities
        entities = extract_entities(
            text
        )

        entity_text = [
            entity["text"]
            for entity in entities
        ]

        entity_labels = [
            entity["label"]
            for entity in entities
        ]

        entity_results.append(
            "; ".join(entity_text)
        )

        # Topics
        topics = extract_topic_terms(
            text
        )

        topic_results.append(
            ", ".join(topics)
        )

    df["entities"] = entity_results

    df["topics"] = topic_results

    return df


# -------------------------------------------------------------------
# ENTITY SUMMARY
# -------------------------------------------------------------------

def print_entity_summary(
    df: pd.DataFrame,
) -> None:
    """
    Print frequently detected entities.
    """

    print("\n" + "=" * 70)
    print("ENTITY SUMMARY")
    print("=" * 70)

    all_entities = []

    for value in df["entities"].fillna(""):

        if not value:
            continue

        entities = [
            entity.strip()
            for entity in value.split(";")
            if entity.strip()
        ]

        all_entities.extend(
            entities
        )

    if not all_entities:

        print(
            "No named entities detected."
        )

        return

    counts = Counter(
        all_entities
    )

    for entity, count in (
        counts.most_common(20)
    ):

        print(
            f"{entity:<30} {count}"
        )


# -------------------------------------------------------------------
# TOPIC SUMMARY
# -------------------------------------------------------------------

def print_topic_summary(
    df: pd.DataFrame,
) -> None:
    """
    Print frequently detected topic terms.
    """

    print("\n" + "=" * 70)
    print("TOPIC SUMMARY")
    print("=" * 70)

    all_topics = []

    for value in df["topics"].fillna(""):

        if not value:
            continue

        topics = [
            topic.strip()
            for topic in value.split(",")
            if topic.strip()
        ]

        all_topics.extend(
            topics
        )

    if not all_topics:

        print(
            "No topic terms detected."
        )

        return

    counts = Counter(
        all_topics
    )

    for topic, count in (
        counts.most_common(20)
    ):

        print(
            f"{topic:<30} {count}"
        )


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

def main() -> None:

    data_directory = Path(
        "data/youtube"
    )

    input_file = (
        data_directory
        / "youtube_nlp_processed.csv"
    )

    if not input_file.exists():

        print(
            "Processed YouTube dataset "
            "not found."
        )

        print(
            "Run youtube_nlp.py first."
        )

        return

    print(
        f"Loading: {input_file}"
    )

    df = process_dataset(
        str(input_file)
    )

    if df.empty:

        print(
            "Dataset is empty."
        )

        return

    print("\n" + "=" * 70)
    print("YOUTUBE INTELLIGENCE PROCESSING")
    print("=" * 70)

    print(
        f"Comments processed: {len(df)}"
    )

    # ---------------------------------------------------------------
    # ENTITY SUMMARY
    # ---------------------------------------------------------------

    print_entity_summary(
        df
    )

    # ---------------------------------------------------------------
    # TOPIC SUMMARY
    # ---------------------------------------------------------------

    print_topic_summary(
        df
    )

    # ---------------------------------------------------------------
    # SAMPLE RESULTS
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SAMPLE INTELLIGENCE RESULTS")
    print("=" * 70)

    sample_columns = [
        "text",
        "sentiment",
        "entities",
        "topics",
    ]

    print(
        df[
            sample_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    # ---------------------------------------------------------------
    # SAVE OUTPUT
    # ---------------------------------------------------------------

    output_file = (
        data_directory
        / "youtube_intelligence.csv"
    )

    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 70)
    print("INTELLIGENCE PROCESSING COMPLETE")
    print("=" * 70)

    print(
        f"Saved to: {output_file}"
    )


# -------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------

if __name__ == "__main__":
    main()
