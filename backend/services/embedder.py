from openai import OpenAI
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Load OpenAI key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Fail fast with a clear message instead of a confusing auth error on first call.
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

# Safe startup check — never log any part of the key itself.
print("OpenAI key loaded:", bool(OPENAI_API_KEY))

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Well under the OpenAI 2048-input-per-request cap; keeps per-request token size sane.
BATCH_SIZE = 100


def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """
    Converts a list of text chunks into vector embeddings using OpenAI's embedding API.
    Processes chunks in batches so large documents don't exceed the per-request limit.
    """
    if not chunks:
        return []
    try:
        embeddings: List[List[float]] = []
        for start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[start:start + BATCH_SIZE]
            response = openai_client.embeddings.create(
                input=batch,
                model=EMBEDDING_MODEL,
            )
            # Sort by index so order is guaranteed to match the input batch.
            batch_embeddings = [
                d.embedding for d in sorted(response.data, key=lambda d: d.index)
            ]
            embeddings.extend(batch_embeddings)
        return embeddings
    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {str(e)}")


def embed_query(query: str) -> List[float]:
    """
    Converts a query into a vector embedding using OpenAI's embedding API.
    """
    try:
        response = openai_client.embeddings.create(
            input=query,
            model=EMBEDDING_MODEL,
        )
        return response.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"Query embedding failed: {str(e)}")