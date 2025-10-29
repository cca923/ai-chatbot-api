import uvicorn
import os
from dotenv import load_dotenv


def main():
    """
    Main function to run the Uvicorn server.
    """
    # Load environment variables from .env file
    load_dotenv()

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))

    print(f"Starting server on {host}:{port}")

    # "app.main:app" points to the 'app' instance in 'app/main.py'
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload
        reload_dirs=["app"],  # Watch the 'app' directory
    )


if __name__ == "__main__":
    main()
