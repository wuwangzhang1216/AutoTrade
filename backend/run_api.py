"""
Run FastAPI backend server
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn

if __name__ == "__main__":
    print("Starting AutoTrade AI API server...")
    print("API docs available at: http://localhost:8888/docs")
    print("WebSocket endpoint: ws://localhost:8888/ws")

    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        log_level="info"
    )
