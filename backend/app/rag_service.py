import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from .config import (
    BACKEND_DIR,
    GROQ_MODEL,
)

from .retrieval import hybrid_retrieve


# ============================================================
# STANDARD REFUSAL MESSAGE
# ============================================================

REFUSAL = (
    "The provided documents do not "
    "contain enough information to "
    "answer this question."
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(
    dotenv_path=(
        BACKEND_DIR
        / ".env"
    )
)


groq_api_key = os.getenv(
    "GROQ_API_KEY"
)


if not groq_api_key:

    raise ValueError(
        "GROQ_API_KEY was not found "
        "in backend/.env"
    )


# ============================================================
# GROQ CLIENT
# ============================================================

llm_client = OpenAI(

    api_key=groq_api_key,

    base_url=(
        "https://api.groq.com/openai/v1"
    ),

)


# ============================================================
# CHECK IF AN ASSISTANT MESSAGE IS A REFUSAL
# ============================================================

def is_refusal(
    content: str,
) -> bool:

    return (
        content.strip()
        == REFUSAL
    )


# ============================================================
# BUILD ONLY VALID / GROUNDED CHAT HISTORY
# ============================================================

def get_grounded_history(
    history: list[dict],
) -> list[dict]:

    """
    Keep only successful user -> assistant pairs.

    If the assistant refused because the document
    did not contain enough information, that entire
    Q&A pair is removed from usable conversation
    history.

    This prevents failed questions from contaminating
    later follow-up retrieval.
    """

    grounded_history = []

    pending_user = None


    for message in history:

        role = message.get(
            "role"
        )

        content = (
            message
            .get(
                "content",
                ""
            )
            .strip()
        )


        # ----------------------------------------------------
        # Ignore empty messages
        # ----------------------------------------------------

        if not content:
            continue


        # ----------------------------------------------------
        # Remember latest user question
        # ----------------------------------------------------

        if role == "user":

            pending_user = {
                "role": "user",
                "content": content,
            }


        # ----------------------------------------------------
        # Assistant answer
        # ----------------------------------------------------

        elif role == "assistant":

            # ----------------------------------------------
            # Only keep pair if:
            #
            # 1. There was a user question
            # 2. Assistant did NOT refuse
            # ----------------------------------------------

            if (
                pending_user
                and not is_refusal(
                    content
                )
            ):

                grounded_history.append(
                    pending_user
                )


                grounded_history.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )


            # ----------------------------------------------
            # Whether valid or refused,
            # this pair is now finished.
            # ----------------------------------------------

            pending_user = None


    # --------------------------------------------------------
    # Only preserve recent grounded context
    # --------------------------------------------------------

    return grounded_history[-4:]


# ============================================================
# DETECT AMBIGUOUS FOLLOW-UP QUESTIONS
# ============================================================

def is_referential_question(
    question: str,
) -> bool:

    """
    Detect questions that rely on previous conversation
    context instead of explicitly naming the subject.

    Examples:

    - Why is that useful?
    - How does it work?
    - What about that?
    - Why would that matter?
    - Can it do this?
    """

    normalized = (
        question
        .strip()
        .lower()
    )


    if not normalized:
        return False


    # --------------------------------------------------------
    # Explicit phrases that strongly depend on prior context
    # --------------------------------------------------------

    patterns = [

        r"\bwhy is that\b",

        r"\bwhy was that\b",

        r"\bwhy would that\b",

        r"\bwhy does that\b",

        r"\bhow does that\b",

        r"\bhow would that\b",

        r"\bwhat about that\b",

        r"\bwhat about it\b",

        r"\bwhat does it do\b",

        r"\bhow does it work\b",

        r"\bwhy is it useful\b",

        r"\bwhy would it be useful\b",

        r"\bwhy does it matter\b",

        r"\bwhat are its benefits\b",

        r"\bwhat are its limitations\b",

        r"\bwhat are its features\b",

        r"\bwho would use it\b",

        r"\bwho uses it\b",

        r"\bcan it\b",

        r"\bdoes it\b",

        r"\bwhat about them\b",

        r"\bhow do they work\b",

        r"\bwhy are they useful\b",

    ]


    for pattern in patterns:

        if re.search(
            pattern,
            normalized,
        ):

            return True


    return False


# ============================================================
# ASK DOCUMENT
# ============================================================

def ask_document(
    question: str,
    history: list[dict] | None = None,
) -> dict:

    # --------------------------------------------------------
    # Default history
    # --------------------------------------------------------

    history = history or []


    # --------------------------------------------------------
    # Remove failed / ungrounded previous turns
    # --------------------------------------------------------

    recent_history = (
        get_grounded_history(
            history
        )
    )


    # ========================================================
    # BLOCK AMBIGUOUS FOLLOW-UP WITHOUT VALID HISTORY
    # ========================================================

    if (
        is_referential_question(
            question
        )
        and not recent_history
    ):

        return {

            "answer": (
                "I do not have a previous "
                "document-grounded answer to "
                "resolve that reference. "
                "Please ask the question again "
                "with the subject named explicitly."
            ),

            "sources": [],

        }


    # ========================================================
    # RETRIEVE DOCUMENT CHUNKS
    # ========================================================

    retrieved = (
        hybrid_retrieve(

            question=question,

            history=(
                recent_history
            ),

        )
    )


    # --------------------------------------------------------
    # No useful retrieval
    # --------------------------------------------------------

    if not retrieved:

        return {

            "answer": REFUSAL,

            "sources": [],

        }


    # ========================================================
    # BUILD DOCUMENT CONTEXT
    # ========================================================

    context_parts = []


    for item in retrieved:

        context_parts.append(
            f"""
[SOURCE: {item["file"]} | PAGE: {item["page"]} | CHUNK: {item["chunk_id"]}]
{item["text"]}
""".strip()
        )


    context = "\n\n".join(
        context_parts
    )


    # ========================================================
    # BUILD GROUNDED PROMPT
    # ========================================================

    user_prompt = f"""
Answer the current question using only the
information explicitly supported by the
DOCUMENT CONTEXT below.

Do not use outside knowledge.

Do not invent examples, names, definitions,
explanations, or facts that are missing from
the document context.

Conversation history may only help you
understand references such as:

"that"
"it"
"why?"
"the previous point"
"the second one"

Conversation history must NOT be treated as
a factual source.

All factual information must be supported by
the DOCUMENT CONTEXT.

Cite factual claims using:

[Source: filename, Page: number]

Only cite a source when that source actually
supports the statement.

If the document context is insufficient,
respond exactly:

"{REFUSAL}"

DOCUMENT CONTEXT:

{context}

CURRENT QUESTION:

{question}
"""


    # ========================================================
    # BUILD LLM MESSAGES
    # ========================================================

    messages = [

        {
            "role": "system",

            "content": (
                "You are a document-grounded "
                "question-answering assistant. "
                "Use only retrieved document "
                "evidence for factual answers. "
                "Conversation history may only "
                "be used to resolve references "
                "in follow-up questions."
            ),
        }

    ]


    # --------------------------------------------------------
    # Add ONLY grounded history
    # --------------------------------------------------------

    for message in recent_history:

        role = message.get(
            "role"
        )

        content = message.get(
            "content"
        )


        if (
            role
            in {
                "user",
                "assistant",
            }
            and content
        ):

            messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )


    # --------------------------------------------------------
    # Current RAG question
    # --------------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": (
                user_prompt
            ),
        }
    )


    # ========================================================
    # CALL GROQ
    # ========================================================

    response = (
        llm_client
        .chat
        .completions
        .create(

            model=(
                GROQ_MODEL
            ),

            messages=messages,

            temperature=0.2,

            max_tokens=500,

        )
    )


    # ========================================================
    # EXTRACT ANSWER
    # ========================================================

    answer = (
        response
        .choices[0]
        .message
        .content
        or REFUSAL
    ).strip()


    # ========================================================
    # IF LLM REFUSES, DO NOT SHOW MISLEADING SOURCES
    # ========================================================

    if is_refusal(
        answer
    ):

        return {

            "answer": REFUSAL,

            "sources": [],

        }


    # ========================================================
    # BUILD PROGRAMMATIC SOURCES
    # ========================================================

    sources = [

        {
            "file": (
                item["file"]
            ),

            "page": (
                item["page"]
            ),

            "chunk_id": (
                item["chunk_id"]
            ),

            "score": round(
                item["score"],
                4,
            ),

            "semantic_score": round(
                item[
                    "semantic_score"
                ],
                4,
            ),

            "keyword_score": round(
                item[
                    "keyword_score"
                ],
                4,
            ),

        }

        for item in retrieved

    ]


    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "answer": answer,

        "sources": sources,

    }