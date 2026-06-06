"""剧本读写与导出 API。"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.database import ProjectORM, get_db
from app.infrastructure.file_storage import FileStorage
from app.services.export_service import ExportService
from app.services.yaml_handler import YAMLHandler

router = APIRouter(prefix="/api/projects", tags=["scripts"])
storage = FileStorage()
yaml_handler = YAMLHandler()
export_service = ExportService()


class ScriptUpdate(BaseModel):
    """剧本更新请求体。"""

    content: str


class ExportRequest(BaseModel):
    """导出请求体。"""

    format: str = "yaml"


@router.get("/{project_id}/script")
def get_script(project_id: str, db: Session = Depends(get_db)):
    """获取剧本 YAML。"""
    orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not orm:
        raise HTTPException(status_code=404, detail="项目不存在")

    content = storage.load_script_yaml(project_id)
    if content is None:
        raise HTTPException(status_code=404, detail="尚未生成剧本")

    return {"content": content}


@router.put("/{project_id}/script")
def update_script(
    project_id: str,
    body: ScriptUpdate,
    db: Session = Depends(get_db),
):
    """保存编辑后的剧本。"""
    orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not orm:
        raise HTTPException(status_code=404, detail="项目不存在")

    data, errors = yaml_handler.validate_yaml(body.content)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    storage.save_script_yaml(project_id, body.content)
    orm.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.post("/{project_id}/script/validate")
def validate_script(project_id: str, body: ScriptUpdate):
    """校验剧本 YAML。"""
    data, errors = yaml_handler.validate_yaml(body.content)
    return {"valid": len(errors) == 0, "errors": errors, "data": data}


@router.post("/{project_id}/export")
def export_script(
    project_id: str,
    body: ExportRequest,
    db: Session = Depends(get_db),
):
    """导出剧本文件。"""
    orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not orm:
        raise HTTPException(status_code=404, detail="项目不存在")

    content = storage.load_script_yaml(project_id)
    if content is None:
        raise HTTPException(status_code=404, detail="尚未生成剧本")

    try:
        exported, mime, ext = export_service.export(content, body.format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = f"{orm.name or 'script'}.{ext}"
    return Response(
        content=exported.encode("utf-8"),
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
