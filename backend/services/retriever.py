import faiss
import numpy as np
import os
import pickle
import logging
from typing import List
from collections import Counter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDEX_PATH = "data/faiss_index/docs.index"
META_PATH = "data/faiss_index/meta.pkl"
os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)


class Retriever:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        # Flat lists that grow in lock-step with the FAISS index:
        # chunks[i] and chunk_files[i] both correspond to FAISS position i.
        self.chunks: List[str] = []
        self.chunk_files: List[str] = []

        # Load index and metadata
        try:
            if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
                self.index = faiss.read_index(INDEX_PATH)
                with open(META_PATH, "rb") as f:
                    meta = pickle.load(f)
                self.chunks = meta["chunks"]
                self.chunk_files = meta["chunk_files"]
                logger.info(
                    f"Loaded FAISS index and metadata from {INDEX_PATH} and {META_PATH}"
                )
        except Exception as e:
            logger.error(f"Failed to load FAISS index or metadata: {e}")
            self.index = faiss.IndexFlatL2(dim)
            self.chunks = []
            self.chunk_files = []

    def add(self, file_name: str, vectors: List[List[float]], chunks: List[str]):
        try:
            vectors_np = np.array(vectors, dtype="float32")
            if vectors_np.shape[1] != self.dim:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.dim}, got {vectors_np.shape[1]}"
                )

            faiss.normalize_L2(vectors_np)
            self.index.add(vectors_np)

            # Keep the flat metadata aligned with FAISS insertion order.
            self.chunks.extend(chunks)
            self.chunk_files.extend([file_name] * len(chunks))

            self.save()
            logger.info(f"Added {len(chunks)} chunks for file {file_name}")
        except Exception as e:
            logger.error(f"Failed to add embeddings for {file_name}: {e}")
            raise RuntimeError(f"Failed to add embeddings: {e}")

    def save(self):
        try:
            faiss.write_index(self.index, INDEX_PATH)
            with open(META_PATH, "wb") as f:
                pickle.dump(
                    {"chunks": self.chunks, "chunk_files": self.chunk_files}, f
                )
            logger.info("FAISS index and metadata saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save FAISS index or metadata: {e}")
            raise RuntimeError(f"Failed to save index or metadata: {e}")

    def search(
        self, query_vector: List[float], file_name: str = None, top_k: int = 5
    ) -> List[str]:
        """
        Returns a list of chunk strings only (distances are discarded).

        FAISS returns global positions into the flat index; chunks[i] and
        chunk_files[i] map those positions back to the right text and source file.
        """
        try:
            query_np = np.array([query_vector], dtype="float32")
            if query_np.shape[1] != self.dim:
                raise ValueError(
                    f"Query vector dimension mismatch: expected {self.dim}, got {query_np.shape[1]}"
                )

            faiss.normalize_L2(query_np)

            # When filtering by file, over-fetch so we still have top_k left
            # after dropping hits that belong to other files.
            k = top_k if file_name is None else min(top_k * 10, len(self.chunks))
            if k == 0:
                return []

            distances, indices = self.index.search(query_np, k)

            results = []
            for i in indices[0]:
                if i < 0:  # FAISS pads with -1 when fewer than k vectors exist
                    continue
                if file_name and self.chunk_files[i] != file_name:
                    continue
                results.append(self.chunks[i])
                if len(results) >= top_k:
                    break

            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []  # safe fallback

    def list_documents(self) -> List[dict]:
        """Return each stored document with its chunk count, preserving upload order."""
        counts = Counter(self.chunk_files)
        seen = []
        for name in self.chunk_files:
            if name not in seen:
                seen.append(name)
        return [{"file_name": name, "chunks": counts[name]} for name in seen]


# Initialize retriever dynamically using embedding dimension
from backend.services.embedder import embed_query

try:
    test_vector = embed_query("test")  # dynamically detect dimension
    _retriever = Retriever(dim=len(test_vector))
except Exception as e:
    logger.error(f"Failed to initialize retriever: {e}")
    _retriever = None


def store_embeddings(file_name: str, vectors: List[List[float]], chunks: List[str]):
    if _retriever is None:
        raise RuntimeError("Retriever not initialized")
    _retriever.add(file_name, vectors, chunks)


def retrieve_relevant_chunks(
    query_vector: List[float], file_name: str = None, top_k: int = 5
):
    if _retriever is None:
        logger.warning("Retriever not initialized, returning empty results")
        return []
    return _retriever.search(query_vector, file_name, top_k)


def list_documents() -> List[dict]:
    if _retriever is None:
        return []
    return _retriever.list_documents()