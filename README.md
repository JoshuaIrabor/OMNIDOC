Marginalia — Document Q&A

A full-stack Retrieval-Augmented Generation (RAG) application that lets you upload documents and ask questions about them in natural language. Every answer is grounded in the passages actually retrieved from your files, rather than the model's general knowledge.

Upload a PDF, DOCX, or TXT file, ask a question, and the app parses and chunks the document, embeds it, retrieves the most relevant passages by semantic similarity, and generates a grounded answer.

How it works

The backend is a RAG pipeline built from small, decoupled services:

Upload → Parse → Chunk → Embed → Store (FAISS)
                                      │
Question → Embed query → Retrieve top-k chunks → Generate grounded answer
Parse — extract text from PDF (PyMuPDF), DOCX (python-docx, including table cells), or TXT (with encoding fallback).
Chunk — split text into overlapping, sentence-aware chunks; oversized sentences are hard-split so no chunk exceeds the size limit.
Embed — convert chunks to vector embeddings via the OpenAI embeddings API, batched to stay within request limits.
Store — index vectors in a FAISS store, with parallel metadata tracking which file each chunk came from.
Retrieve — embed the query and pull the most similar chunks from the index.
Generate — pass the retrieved passages as context to the LLM, which answers strictly from that context.
Tech stack

Backend

Python + FastAPI
OpenAI API (embeddings + chat completion)
FAISS (vector similarity search)
PyMuPDF, python-docx (document parsing)

Frontend

React + Vite
axios (API calls)
react-markdown (answer rendering)
Project structure
.
├── backend/
│   ├── services/
│   │   ├── parser.py       # PDF / DOCX / TXT text extraction
│   │   ├── chunker.py      # sentence-aware overlapping chunking
│   │   ├── embedder.py     # OpenAI embeddings (batched)
│   │   ├── retriever.py    # FAISS index + metadata + search
│   │   └── generator.py    # grounded answer generation
│   ├── api/                # FastAPI routes (upload / ask / documents)
│   └── main.py             # app entrypoint
├── data/
│   └── faiss_index/        # persisted index + metadata (generated at runtime)
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── App.css
├── .env                    # not committed
├── .gitignore
└── README.md

Adjust paths to match your actual layout — this reflects the service-oriented structure the pipeline is organized around.

Setup
1. Backend
bash
# from the project root
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

Create a .env file in the project root:

env
OPENAI_API_KEY=sk-your-key-here
EMBEDDING_MODEL=text-embedding-3-small
GPT_MODEL=gpt-3.5-turbo
GPT_MAX_TOKENS=800
GPT_TEMPERATURE=0.3

Run the API:

bash
uvicorn backend.main:app --reload --port 8000
2. Frontend
bash
cd frontend
npm install
npm run dev

The app runs at http://localhost:5173 and talks to the backend at http://127.0.0.1:8000.

API endpoints
Method	Endpoint	Description
POST	/api/v1/upload	Upload and ingest a document
POST	/api/v1/ask	Ask a question (question query param)
GET	/api/v1/documents	List documents currently in the index
Notes
The FAISS index and its metadata persist to data/faiss_index/, so uploaded documents survive server restarts.
If you change the index metadata format, delete data/faiss_index/ and re-upload so the store rebuilds cleanly.
Answers are generated strictly from retrieved context. Positional questions ("what is the first sentence?") are a known limitation of semantic retrieval, since chunks are matched by meaning, not document order.
Roadmap
Per-document delete (rebuild index without a file's chunks)
Show source passages alongside each answer
Support additional file types
