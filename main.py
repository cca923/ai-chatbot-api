import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app instance
app = FastAPI(
    title="AI Chatbot API",
    description="API for the Perplexity-like AI Chatbot",
    version="0.1.0",
)


# Setting up CORS (Cross-Origin Resource Sharing)
origins = [
    "http://localhost:3000",
    # Add more origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create API routes
@app.get("/")
def get_root():
    """Root route for basic testing."""
    return {"message": "Welcome to AI Chatbot API!"}


@app.get("/v1/ping")
def get_ping():
    """Ping route for health checks."""
    return {"message": "pong"}


# Main entry point: Start the server with uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
