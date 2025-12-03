from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import json
import asyncio
from pathlib import Path
from server.config import settings

router = APIRouter()

class FileInfo(BaseModel):
    name: str
    path: str
    type: str
    size: int
    modified: str
    target: Optional[str] = None

class FolderInfo(BaseModel):
    name: str
    path: str
    files: List[FileInfo]
    file_count: int

class FindingsExplorerResponse(BaseModel):
    folders: List[FolderInfo]
    root_files: List[FileInfo]
    total_files: int
    last_updated: str

def get_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == '.json':
        return 'json'
    elif ext == '.txt':
        return 'text'
    elif ext == '.pdf':
        return 'pdf'
    elif ext in ['.html', '.htm']:
        return 'html'
    elif ext == '.log':
        return 'log'
    elif ext == '.csv':
        return 'csv'
    elif ext == '.xml':
        return 'xml'
    else:
        return 'unknown'

def extract_target_from_folder(folder_name: str) -> Optional[str]:
    parts = folder_name.split('_')
    if len(parts) >= 2:
        return parts[0]
    return folder_name

def scan_findings_directory() -> FindingsExplorerResponse:
    findings_dir = Path(settings.FINDINGS_DIR)
    if not findings_dir.exists():
        findings_dir.mkdir(parents=True, exist_ok=True)
    
    folders: List[FolderInfo] = []
    root_files: List[FileInfo] = []
    total_files = 0
    
    for item in findings_dir.iterdir():
        if item.is_dir():
            folder_files = []
            for file in item.iterdir():
                if file.is_file():
                    stat = file.stat()
                    folder_files.append(FileInfo(
                        name=file.name,
                        path=str(file.relative_to(findings_dir)),
                        type=get_file_type(file.name),
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        target=extract_target_from_folder(item.name)
                    ))
                    total_files += 1
            
            folders.append(FolderInfo(
                name=item.name,
                path=str(item.relative_to(findings_dir)),
                files=sorted(folder_files, key=lambda x: x.modified, reverse=True),
                file_count=len(folder_files)
            ))
        elif item.is_file():
            stat = item.stat()
            root_files.append(FileInfo(
                name=item.name,
                path=item.name,
                type=get_file_type(item.name),
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
            ))
            total_files += 1
    
    folders = sorted(folders, key=lambda x: x.name, reverse=True)
    root_files = sorted(root_files, key=lambda x: x.modified, reverse=True)
    
    return FindingsExplorerResponse(
        folders=folders,
        root_files=root_files,
        total_files=total_files,
        last_updated=datetime.now().isoformat()
    )

@router.get("/explorer")
async def get_findings_explorer() -> FindingsExplorerResponse:
    try:
        return scan_findings_directory()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/{file_path:path}")
async def get_file_content(file_path: str):
    try:
        findings_dir = Path(settings.FINDINGS_DIR)
        full_path = findings_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not str(full_path.resolve()).startswith(str(findings_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        file_type = get_file_type(full_path.name)
        
        if file_type == 'json':
            with open(full_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return {"type": "json", "content": content, "filename": full_path.name}
        
        elif file_type in ['text', 'log', 'csv', 'xml']:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"type": file_type, "content": content, "filename": full_path.name}
        
        elif file_type == 'html':
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"type": "html", "content": content, "filename": full_path.name}
        
        elif file_type == 'pdf':
            return FileResponse(
                path=str(full_path),
                media_type="application/pdf",
                filename=full_path.name
            )
        
        else:
            with open(full_path, 'rb') as f:
                content = f.read()
            return Response(content=content, media_type="application/octet-stream")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_agent_logs():
    try:
        log_dir = Path(settings.LOG_DIR)
        if not log_dir.exists():
            return {"logs": [], "total": 0}
        
        log_files = []
        for file in log_dir.iterdir():
            if file.is_file():
                stat = file.stat()
                log_files.append(FileInfo(
                    name=file.name,
                    path=file.name,
                    type=get_file_type(file.name),
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
                ))
        
        log_files = sorted(log_files, key=lambda x: x.modified, reverse=True)
        return {"logs": log_files, "total": len(log_files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{file_name}")
async def get_log_content(file_name: str, tail: int = 500):
    try:
        log_dir = Path(settings.LOG_DIR)
        full_path = log_dir / file_name
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Log file not found")
        
        if not str(full_path.resolve()).startswith(str(log_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if tail > 0:
                lines = lines[-tail:]
            content = ''.join(lines)
        
        return {"filename": file_name, "content": content, "total_lines": len(lines)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

_watch_task = None
_last_broadcast_state = {}

async def watch_findings_directory():
    global _watch_task, _last_broadcast_state
    findings_dir = Path(settings.FINDINGS_DIR)
    
    print("🔍 Findings directory watcher started")
    
    while True:
        try:
            current_state = {}
            if findings_dir.exists():
                for item in findings_dir.rglob('*'):
                    if item.is_file():
                        stat = item.stat()
                        current_state[str(item)] = stat.st_mtime
            
            if current_state != _last_broadcast_state:
                from server.ws import manager
                if manager.active_connections:
                    explorer_data = scan_findings_directory()
                    await manager.broadcast({
                        "type": "findings_explorer_update",
                        "data": explorer_data.dict(),
                        "timestamp": datetime.now().isoformat()
                    })
                    print(f"📁 Findings update broadcast: {len(current_state)} files")
                _last_broadcast_state = current_state.copy()
            
            await asyncio.sleep(2)
        except asyncio.CancelledError:
            print("🛑 Findings watcher stopped")
            break
        except Exception as e:
            print(f"Findings watch error: {e}")
            await asyncio.sleep(5)

def start_findings_watcher():
    global _watch_task
    if _watch_task is None or _watch_task.done():
        _watch_task = asyncio.create_task(watch_findings_directory())

class SummaryInput(BaseModel):
    summary: str
    target: str
    execution_time: str

@router.post("/summary")
async def save_findings_summary(data: SummaryInput):
    try:
        findings_dir = Path(settings.FINDINGS_DIR)
        findings_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = "".join(c if c.isalnum() or c in "._-" else "_" for c in data.target[:30])
        filename = f"mission_summary_{safe_target}_{timestamp}.md"
        
        summary_content = f"""# Mission Summary Report

**Generated:** {datetime.now().isoformat()}
**Target:** {data.target}
**Execution Time:** {data.execution_time}

---

{data.summary}
"""
        
        file_path = findings_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        return {"status": "saved", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
