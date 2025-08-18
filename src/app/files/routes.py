from fastapi import APIRouter, Depends, UploadFile, File as F, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_
from ..deps import get_current_user
from ..database import get_session
from ..auth.models import User
from ..common.enums import Visibility, Role
from .models import File as FileModel, FileMetadata
from .schemas import FileOut, FileList, FileMetaOut
from .service import validate_upload, store_file, MAX_SIZE
from ..storage.minio_client import get_presigned_url
from .tasks import extract_metadata_task
router = APIRouter(prefix="/files", tags=["files"])
@router.post("/upload", response_model=FileOut)
async def upload_file(visibility: Visibility = Form(...), file: UploadFile = F(...), user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    validate_upload(user, file, visibility)
    data = await file.read()
    if len(data) > MAX_SIZE[user.role]:
        raise HTTPException(400, f"File too large for role {user.role}")
    key, size = store_file(file, data)
    rec = FileModel(owner_id=user.id, department=user.department, filename=file.filename, content_type=file.content_type or "application/octet-stream", size_bytes=size, visibility=visibility, s3_key=key)
    session.add(rec)
    await session.commit()
    await session.refresh(rec)
    extract_metadata_task.delay(rec.id)
    return rec
@router.get("/", response_model=FileList)
async def list_files(session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    q = select(FileModel)
    if user.role == Role.ADMIN:
        pass
    elif user.role == Role.MANAGER:
        q = q.where(or_(FileModel.visibility == Visibility.PUBLIC, FileModel.visibility == Visibility.DEPARTMENT, FileModel.owner_id == user.id))
    else:
        q = q.where(or_(FileModel.visibility == Visibility.PUBLIC, (FileModel.visibility == Visibility.DEPARTMENT) & (FileModel.department == user.department), FileModel.owner_id == user.id))
    res = await session.execute(q)
    items = res.scalars().all()
    return FileList(items=items, total=len(items))
@router.get("/{file_id}", response_model=FileOut)
async def get_file_info(file_id: int, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    rec = await session.get(FileModel, file_id)
    if not rec:
        raise HTTPException(404, "Not found")
    if user.role != Role.ADMIN:
        if rec.visibility == Visibility.PRIVATE and rec.owner_id != user.id:
            raise HTTPException(403, "Not allowed")
        if rec.visibility == Visibility.DEPARTMENT and user.role == Role.USER and rec.department != user.department:
            raise HTTPException(403, "Not allowed")
    return rec
@router.get("/{file_id}/download")
async def download_file(file_id: int, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    rec = await session.get(FileModel, file_id)
    if not rec:
        raise HTTPException(404, "Not found")
    if user.role != Role.ADMIN:
        if rec.visibility == Visibility.PRIVATE and rec.owner_id != user.id:
            raise HTTPException(403, "Not allowed")
        if rec.visibility == Visibility.DEPARTMENT and user.role == Role.USER and rec.department != user.department:
            raise HTTPException(403, "Not allowed")
    rec.downloads += 1
    await session.commit()
    url = get_presigned_url(rec.s3_key)
    return {"url": url}
@router.get("/{file_id}/metadata", response_model=FileMetaOut)
async def get_metadata(file_id: int, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    rec = await session.get(FileModel, file_id)
    if not rec:
        raise HTTPException(404, "Not found")
    if user.role != Role.ADMIN:
        if rec.visibility == Visibility.PRIVATE and rec.owner_id != user.id:
            raise HTTPException(403, "Not allowed")
        if rec.visibility == Visibility.DEPARTMENT and user.role == Role.USER and rec.department != user.department:
            raise HTTPException(403, "Not allowed")
    m = await session.execute(select(FileMetadata).where(FileMetadata.file_id == file_id))
    meta = m.scalar_one_or_none()
    return FileMetaOut(file_id=file_id, raw=meta.raw if meta else {})
@router.delete("/{file_id}")
async def delete_file(file_id: int, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    rec = await session.get(FileModel, file_id)
    if not rec:
        raise HTTPException(404, "Not found")
    if user.role == Role.ADMIN:
        pass
    elif user.role == Role.MANAGER:
        if rec.department != user.department:
            raise HTTPException(403, "Managers can delete only files of their department")
    else:
        if rec.owner_id != user.id:
            raise HTTPException(403, "Users can delete only their files")
    await session.execute(delete(FileModel).where(FileModel.id == file_id))
    await session.commit()
    return {"status": "deleted"}

