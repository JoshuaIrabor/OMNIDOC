from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.parser import parse_file
from backend.utils.chunker import split_text
from backend.services.embedder import embed_chunks, embed_query
from backend.services.retriever import store_embeddings, retrieve_relevant_chunks
from backend.services.summarizer import generate_answer
from backend.services.retriever import list_documents

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        raw_text = await parse_file(file)
        chunks = split_text(raw_text)
        embeddings = embed_chunks(chunks)
        store_embeddings(file.filename, embeddings, chunks)
        return {"message": f"Successfully processed and stored: {file.filename}"}
    except ValueError as e:
        # Client error (e.g., unsupported file type)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def ask_question(question: str):
    try:
        query_vector = embed_query(question)
        relevant_chunks = retrieve_relevant_chunks(query_vector)

        # Ensure only strings are passed to the summarizer
        relevant_texts = [c for c in relevant_chunks if isinstance(c, str)]

        answer = await generate_answer(question, relevant_texts)
        return {"answer": answer, "relevant_chunks": relevant_texts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def get_documents():
    return {"documents": list_documents()}
