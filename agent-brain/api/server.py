from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="Agent Brain - Intelligence Service",
        description="AI Intelligence service for autonomous security agent. Handles reasoning, decision making, and cognitive processing.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router, prefix="/brain", tags=["brain"])
    
    @app.get("/")
    async def root():
        return {
            "service": "Agent Brain",
            "description": "AI Intelligence Service for Autonomous Security Agent",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/brain/health",
                "status": "/brain/status",
                "think": "/brain/think",
                "classify": "/brain/classify",
                "evaluate": "/brain/evaluate",
                "strategy": "/brain/strategy",
                "reason": "/brain/reason",
                "docs": "/docs"
            }
        }
    
    @app.on_event("startup")
    async def startup_event():
        print("=" * 60)
        print("Agent Brain - Intelligence Service Starting...")
        print("=" * 60)
        print("This service provides AI reasoning capabilities for the agent")
        print("Endpoints available at /brain/*")
        print("API documentation at /docs")
        print("=" * 60)
    
    return app
