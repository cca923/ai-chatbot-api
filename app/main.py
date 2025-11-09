from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings

# 1. Create FastAPI App Instance
app = FastAPI(
    title="AI Chatbot API",
    description="API for the Perplexity-like AI Chatbot",
    version="0.1.0",
)

# 2. Set up CORS
if settings.CORS_ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 3. Include the main API router
app.include_router(api_router, prefix="/api")


# 4. Add a simple root endpoint
@app.get("/")
def get_root():
    """Root endpoint for a simple health check."""
    return {"message": "Welcome to Insight AI API!"}
