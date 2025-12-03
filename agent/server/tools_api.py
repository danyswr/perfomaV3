"""Tools API endpoints"""
from fastapi import APIRouter
try:
    from tools import ALLOWED_TOOLS, ALL_ALLOWED_TOOLS, get_allowed_tools_by_category
except:
    ALLOWED_TOOLS = {}
    ALL_ALLOWED_TOOLS = set()
    def get_allowed_tools_by_category(): return {}

router = APIRouter()

@router.get("/tools")
async def get_tools():
    return {"status": "ok", "total": len(ALL_ALLOWED_TOOLS), "categories": get_allowed_tools_by_category()}

@router.get("/tools/categories")
async def categories():
    return {"categories": list(get_allowed_tools_by_category().keys())}
