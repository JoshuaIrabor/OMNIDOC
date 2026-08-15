from openai import OpenAI
import os
import logging
from typing import List
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("GPT_MODEL", "gpt-3.5-turbo")
MAX_TOKENS = int(os.getenv("GPT_MAX_TOKENS", 500))
TEMPERATURE = float(os.getenv("GPT_TEMPERATURE", 0.3))

logger = logging.getLogger(__name__)

# Fail fast with a clear message instead of an opaque auth error on the first query.
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


async def summarize_answer(query: str, chunks: List[str]) -> str:
    """
    Generates a grounded answer from the retrieved context.
    """
    if not chunks:
        return "I couldn't find anything about that in your documents."

    # Keep strings as-is; stringify anything else honestly (never a fragment).
    safe_chunks = [c if isinstance(c, str) else str(c) for c in chunks]
    context = "\n\n".join(safe_chunks[:5])  # Limit to first 5 chunks

    prompt = f"""You are a document assistant. Answer the question using the context below.

Guidelines:
- Use the context to answer as fully and directly as you can.
- If the context contains partial or related information, give what you can — a partial answer is more useful than declining.
- Only if the context contains nothing relevant to the question, reply exactly: "I couldn't find anything about that in your documents."
- Do not use outside knowledge or invent details the context doesn't support.
- Write in clear, complete sentences. Use bullet points only for genuine lists of key points.

Context:
{context}

Question:
{query}

Answer:"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a document assistant. You answer strictly from the provided context."},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )

        # content can be None (content filter, or a tool-only response) — guard it.
        content = response.choices[0].message.content
        if content is None:
            logger.warning("OpenAI returned no content")
            return "The model returned an empty response. Please try again."
        return content.strip()

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Something went wrong reaching the model. Please try again."


# Alias for routes
async def generate_answer(query: str, chunks: List[str]) -> str:
    return await summarize_answer(query, chunks)