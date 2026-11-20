import re

from qdrant_client import QdrantClient

from .config import (
    COLLECTION_NAME,
    KEYWORD_MATCH_THRESHOLD,
    KEYWORD_WEIGHT,
    MIN_SEMANTIC_SCORE,
    QDRANT_PATH,
    SEMANTIC_CANDIDATES,
    SEMANTIC_WEIGHT,
    TOP_K,
)

from .embedding_service import embedding_model


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "by",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(
    text: str,
) -> list[str]:

    words = re.findall(
        r"[a-zA-Z0-9]+",
        text.lower(),
    )

    return [
        word
        for word in words
        if word not in STOP_WORDS
    ]


# ============================================================
# KEYWORD SCORE
# ============================================================

def keyword_score(
    query: str,
    document: str,
) -> float:

    query_words = set(
        tokenize(query)
    )

    if not query_words:
        return 0.0


    document_words = set(
        tokenize(document)
    )


    matches = (
        query_words
        & document_words
    )


    overlap_score = (
        len(matches)
        / len(query_words)
    )


    # --------------------------------------------------------
    # Exact remaining phrase bonus
    #
    # "What is PaperLab?"
    # becomes roughly:
    # "paperlab"
    # --------------------------------------------------------

    query_phrase = " ".join(
        tokenize(query)
    )


    document_phrase = " ".join(
        tokenize(document)
    )


    exact_score = 0.0


    if (
        query_phrase
        and query_phrase
        in document_phrase
    ):
        exact_score = 1.0


    return min(
        1.0,
        max(
            overlap_score,
            exact_score,
        ),
    )


# ============================================================
# LOAD ALL QDRANT POINTS
# ============================================================

def _scroll_all_points(
    client: QdrantClient,
) -> list:

    points = []

    offset = None


    while True:

        batch, next_offset = client.scroll(

            collection_name=COLLECTION_NAME,

            limit=256,

            offset=offset,

            with_payload=True,

            with_vectors=False,
        )


        points.extend(
            batch
        )


        if next_offset is None:
            break


        offset = next_offset


    return points


# ============================================================
# HYBRID RETRIEVAL
# ============================================================

def hybrid_retrieve(
    question: str,
    history: list[dict] | None = None,
    top_k: int = TOP_K,
) -> list[dict]:

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # rag_service.py already removes invalid/refused history.
    #
    # Therefore retrieval.py must NOT call
    # get_grounded_history().
    # --------------------------------------------------------

    history = history or []

    recent_history = history[-4:]


    # ========================================================
    # BUILD SEMANTIC QUERY
    # ========================================================

    history_text = "\n".join(

        message.get(
            "content",
            "",
        )

        for message in recent_history

        if message.get(
            "content"
        )
    )


    if history_text:

        semantic_query = f"""
Conversation:
{history_text}

Current question:
{question}
""".strip()

    else:

        semantic_query = question


    # ========================================================
    # CREATE QUERY EMBEDDING
    # ========================================================

    query_embedding = (
        embedding_model.encode(
            semantic_query
        )
    )


    # ========================================================
    # OPEN QDRANT
    # ========================================================

    client = QdrantClient(
        path=str(
            QDRANT_PATH
        )
    )


    try:

        # ----------------------------------------------------
        # No indexed document
        # ----------------------------------------------------

        if not client.collection_exists(
            COLLECTION_NAME
        ):

            return []


        # ====================================================
        # SEMANTIC SEARCH
        # ====================================================

        semantic_results = (
            client.query_points(

                collection_name=(
                    COLLECTION_NAME
                ),

                query=(
                    query_embedding
                    .tolist()
                ),

                limit=(
                    SEMANTIC_CANDIDATES
                ),

                with_payload=True,

            ).points
        )


        # ====================================================
        # LOAD ALL CHUNKS FOR KEYWORD MATCHING
        # ====================================================

        all_points = (
            _scroll_all_points(
                client
            )
        )


        candidates = {}


        # ====================================================
        # ADD SEMANTIC CANDIDATES
        # ====================================================

        for result in semantic_results:

            candidates[
                result.id
            ] = {

                "payload": (
                    result.payload
                    or {}
                ),

                "semantic_score": max(
                    0.0,
                    float(
                        result.score
                    ),
                ),
            }


        # ====================================================
        # ADD KEYWORD CANDIDATES
        # ====================================================

        for point in all_points:

            payload = (
                point.payload
                or {}
            )


            text = payload.get(
                "text",
                "",
            )


            lexical_score = (
                keyword_score(
                    question,
                    text,
                )
            )


            # ------------------------------------------------
            # This allows exact names such as PaperLab,
            # CircuitLens, AgentGuard, etc. to enter the
            # candidate pool even if vector search ranked
            # them badly.
            # ------------------------------------------------

            if lexical_score > 0:

                if (
                    point.id
                    not in candidates
                ):

                    candidates[
                        point.id
                    ] = {

                        "payload": payload,

                        "semantic_score": 0.0,

                    }


        # ====================================================
        # COMBINE SCORES
        # ====================================================

        ranked = []


        for point_id, candidate in (
            candidates.items()
        ):

            payload = candidate[
                "payload"
            ]


            text = payload.get(
                "text",
                "",
            )


            semantic_score = float(
                candidate.get(
                    "semantic_score",
                    0.0,
                )
            )


            lexical_score = (
                keyword_score(
                    question,
                    text,
                )
            )


            # ------------------------------------------------
            # Reject weak chunks unless keyword matching
            # strongly supports them.
            # ------------------------------------------------

            if (
                semantic_score
                < MIN_SEMANTIC_SCORE
                and lexical_score
                < KEYWORD_MATCH_THRESHOLD
            ):
                continue


            hybrid_score = (

                SEMANTIC_WEIGHT
                * semantic_score

                +

                KEYWORD_WEIGHT
                * lexical_score
            )


            ranked.append(
                {

                    "id": point_id,

                    "file": payload.get(
                        "source",
                        "Unknown",
                    ),

                    "page": int(
                        payload.get(
                            "page",
                            0,
                        )
                    ),

                    "chunk_id": int(
                        payload.get(
                            "chunk_id",
                            0,
                        )
                    ),

                    "text": text,

                    "semantic_score": (
                        semantic_score
                    ),

                    "keyword_score": (
                        lexical_score
                    ),

                    "score": (
                        hybrid_score
                    ),

                }
            )


        # ====================================================
        # SORT BEST FIRST
        # ====================================================

        ranked.sort(

            key=lambda item: (
                item["score"]
            ),

            reverse=True,
        )


        return ranked[
            :top_k
        ]


    finally:

        client.close()