import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from api.server import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("BRAIN_PORT", 8001))
    host = os.environ.get("BRAIN_HOST", "0.0.0.0")
    
    print(f"Starting Agent Brain on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
