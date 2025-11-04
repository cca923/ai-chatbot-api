import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file for local development
print("Loading environment variables from .env...")
load_dotenv()


if __name__ == "__main__":
    # Render Port Configuration
    port_str = os.environ.get("PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        print(f"Warning: Invalid PORT '{port_str}', defaulting to 8000.")
        port = 8000

    host = "0.0.0.0"

    print(f"Starting server on {host}:{port}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for local dev
        reload_dirs=["app"],  # Watch the 'app' directory for changes
    )
