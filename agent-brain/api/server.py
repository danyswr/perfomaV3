from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router as brain_router
from .mission_routes import router as mission_router
from .agent_routes import router as agent_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="Performa Agent Brain - Intelligence Service",
        description="AI Intelligence service for autonomous security agent. Handles reasoning, decision making, cognitive processing, mission config, and agent management.",
        version="2.0.0",
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
    
    app.include_router(brain_router, prefix="/brain", tags=["brain"])
    app.include_router(mission_router, prefix="/api", tags=["mission", "config", "session"])
    app.include_router(agent_router, prefix="/api", tags=["agents"])
    
    @app.get("/")
    async def root():
        return {
            "service": "Performa Agent Brain",
            "description": "AI Intelligence Service for Autonomous Security Agent",
            "version": "2.0.0",
            "status": "running",
            "endpoints": {
                "brain": {
                    "health": "/brain/health",
                    "status": "/brain/status",
                    "think": "/brain/think",
                    "classify": "/brain/classify",
                    "evaluate": "/brain/evaluate",
                    "strategy": "/brain/strategy",
                    "reason": "/brain/reason"
                },
                "mission": {
                    "config": "/api/config",
                    "mission": "/api/mission",
                    "session": "/api/session"
                },
                "agents": {
                    "list": "/api/agents",
                    "create": "/api/agents"
                },
                "docs": "/docs"
            }
        }
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "agent-brain"}
    
    @app.on_event("startup")
    async def startup_event():
        print("=" * 60)
        print("Performa Agent Brain - Intelligence Service Starting...")
        print("=" * 60)
        print("This service provides:")
        print("  - AI reasoning capabilities")
        print("  - Mission configuration management")
        print("  - Agent lifecycle management")
        print("  - Session management")
        print("=" * 60)
        print("Brain endpoints: /brain/*")
        print("API endpoints: /api/*")
        print("Documentation: /docs")
        print("=" * 60)
    
    return app
