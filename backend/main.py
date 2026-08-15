from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.routes import router as api_router

app = FastAPI(title="Chatbot Docs AI")

# CORS config (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API router
app.include_router(api_router, prefix="/api/v1")  # versioning

# Root route
@app.get("/")
def read_root():
    return {"message": "Welcome to Chatbot Docs AI"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"Internal server error: {str(exc)}"},
    )

# Startup event (optional)
@app.on_event("startup")
async def startup_event():
    print("Starting Chatbot Docs AI server...")
