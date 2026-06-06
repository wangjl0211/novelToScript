"""项目 API 路由。"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.domain.models import Chapter, ProjectCreate, ProjectResponse
from app.infrastructure.database import ProjectORM, get_db
from app.infrastructure.file_storage import FileStorage, new_project_id
from app.services.import_parser import parse_novel_file

router = APIRouter(prefix="/api/projects", tags=["projects"])
storage = FileStorage()


def _to_response(orm: ProjectORM) -> ProjectResponse:
    return ProjectResponse(
        id=orm.id,
        name=orm.name,
        description=orm.description,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        chapter_count=orm.chapter_count,
        conversion_status=orm.conversion_status,
        has_script=storage.script_exists(orm.id),
    )


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """获取项目列表。"""
    projects = db.query(ProjectORM).order_by(ProjectORM.updated_at.desc()).all()
    return [_to_response(p) for p in projects]


@router.post("", response_model=ProjectResponse)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目。"""
    pid = new_project_id()
    now = datetime.now(timezone.utc)
    orm = ProjectORM(
        id=pid,
        name=body.name,
        description=body.description,
        created_at=now,
        updated_at=now,
    )
    db.add(orm)
    db.commit()
    db.refresh(orm)
    return _to_response(orm)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """获取项目详情。"""
    orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not orm:
        raise HTTPException(status_code=404, detail="项目不存在")
    return _to_response(orm)


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """删除项目。"""
    orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not orm:
        raise HTTPException(status_code=404, detail="项目不存在")
    storage.delete_project_files(project_id)
    db.delete(orm)
    db.commit()
    return {"ok": True}


@router.post("/{project_id}/upload")
async def upload_novel(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传小说文件（TXT/DOCX）。"""
    orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not orm:
        raise HTTPException(status_code=404, detail="项目不存在")

    content = await file.read()
    filename = file.filename or "novel.txt"

    try:
        novel = parse_novel_file(filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    storage.save_upload(project_id, filename, content)
    storage.save_novel(project_id, novel)

    orm.novel_title = novel.title
    orm.novel_author = novel.author
    orm.chapter_count = len(novel.chapters)
    orm.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "title": novel.title,
        "author": novel.author,
        "chapter_count": len(novel.chapters),
        "chapters": [
            {"index": c.index, "title": c.title, "word_count": c.word_count}
            for c in novel.chapters
        ],
    }


@router.get("/{project_id}/chapters")
def get_chapters(project_id: str, db: Session = Depends(get_db)):
    """获取章节列表。"""
    orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not orm:
        raise HTTPException(status_code=404, detail="项目不存在")

    novel = storage.load_novel(project_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="尚未上传小说")

    return {
        "title": novel.title,
        "chapters": [
            {"index": c.index, "title": c.title, "word_count": c.word_count}
            for c in novel.chapters
        ],
    }


@router.put("/{project_id}/chapters")
def update_chapters(
    project_id: str,
    chapters: list[dict],
    db: Session = Depends(get_db),
):
    """手动调整章节边界。"""
    orm = db.query(ProjectORM).filter(ProjectORM.id == project_id).first()
    if not orm:
        raise HTTPException(status_code=404, detail="项目不存在")

    parsed = [
        Chapter(
            index=c["index"],
            title=c["title"],
            content=c["content"],
            word_count=len(c["content"]),
        )
        for c in chapters
    ]
    if len(parsed) < 3:
        raise HTTPException(status_code=400, detail="章节数不能少于 3 章")

    storage.save_chapters_override(project_id, parsed)
    orm.chapter_count = len(parsed)
    orm.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "chapter_count": len(parsed)}
