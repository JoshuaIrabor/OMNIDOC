from typing import List
import re

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def _split_long_sentence(sentence: str, chunk_size: int) -> List[str]:
    """Hard-split a single oversized sentence into <= chunk_size pieces."""
    return [sentence[i:i + chunk_size] for i in range(0, len(sentence), chunk_size)]


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Splits long text into overlapping chunks at sentence boundaries.
    Any single sentence longer than chunk_size is hard-split so no chunk exceeds the limit.
    """
    if not text or not text.strip():
        return []

    # Split text into sentences (simple regex, can replace with nltk.sent_tokenize)
    sentences = re.split(r'(?<=[.!?]) +', text)

    chunks: List[str] = []
    current_chunk = ""

    for sentence in sentences:
        # If one sentence alone exceeds chunk_size, flush and hard-split it
        # so it never becomes a single oversized chunk that fails embedding.
        if len(sentence) > chunk_size:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
            chunks.extend(_split_long_sentence(sentence, chunk_size))
            continue

        # +1 accounts for the trailing space we append, so chunks don't creep over.
        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            # Start new chunk with overlap
            overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
            current_chunk = overlap_text + sentence + " "

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks