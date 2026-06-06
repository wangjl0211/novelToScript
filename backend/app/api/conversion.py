"""转换任务 API 与 WebSocket。"""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.domain.models import ConversionStatus
from app.infrastructure.database import ProjectORM, get_db
from app.infrastructure.task_runner import progress_broadcaster
from app.services.conversion_engine import ConversionEngine

router = APIRouter(tags=["conversion"])
engine = ConversionEngine()


async def _run_conversion(project_id: str, db_url: str) -> None:
    """后台执行转换任务。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    eng = create_engine(db_url)
    Session = sessionmaker(bind=eng)

    async def on_progress(progress):
        await progress_broadcaster.broadcast(project_id, progress.model_dump(mode="json"))

    result = await engine.convert_project(project_id, on_progress=on_progress)

    db = Session()
    try:
        orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
        if orm:
            if result.success:
                orm.conversion_status = (
                    ConversionStatus.PARTIAL.value
                    if result.errors
                    else ConversionStatus.COMPLETED.value
                )
            else:
                orm.conversion_status = ConversionStatus.FAILED.value
            orm.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


@router.post("/api/projects/{project_id}/convert")
async def start_conversion(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """启动 AI 转换任务。"""
    orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not orm:
        raise HTTPException(status_code=404, detail="项目不存在")
    if orm.chapter_count < 3:
        raise HTTPException(status_code=400, detail="请先上传至少 3 章的小说")

    orm.conversion_status = ConversionStatus.RUNNING.value
    orm.updated_at = datetime.now(timezone.utc)
    db.commit()

    from app.infrastructure.database import engine as db_engine

    background_tasks.add_task(_run_conversion, project_id, str(db_engine.url))

    return {"ok": True, "message": "转换任务已启动"}


@router.websocket("/ws/projects/{project_id}/progress")
async def conversion_progress(websocket: WebSocket, project_id: str):
    """WebSocket 推送转换进度。"""
    await progress_broadcaster.connect(project_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await progress_broadcaster.disconnect(project_id, websocket)
