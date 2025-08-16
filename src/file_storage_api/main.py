from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
import uuid
from . import (
    models,
    schemas,
    auth,
    minio_client,
    tasks,
    database,
    dependencies
)
from .config import settings
from .models import User, File, UserRole, VisibilityLevel

app = FastAPI()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Аутентификация
@app.post("/auth/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.User)
async def read_users_me(current_user: User = Depends(auth.get_current_user)):
    return current_user

# Управление файлами
@app.post("/files/upload", response_model=schemas.FileInfo)
async def upload_file(
    file: UploadFile = File(...),
    visibility: VisibilityLevel = Query(...),
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка прав
    if current_user.role == UserRole.USER:
        if visibility != VisibilityLevel.PRIVATE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="USER can only create private files"
            )
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="USER can only upload PDF files"
            )

    # Проверка размера файла
    max_sizes = {
        UserRole.USER: 10 * 1024 * 1024,    # 10MB
        UserRole.MANAGER: 50 * 1024 * 1024, # 50MB
        UserRole.ADMIN: 100 * 1024 * 1024   # 100MB
    }
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > max_sizes[current_user.role]:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large for {current_user.role} role"
        )

    # Сохранение файла
    file_id = str(uuid.uuid4())
    minio_client.upload_file(file.file, file_id, file.content_type)
    
    # Сохранение метаданных в БД
    db_file = models.File(
        name=file.filename,
        path=file_id,
        size=file_size,
        content_type=file.content_type,
        visibility=visibility,
        owner_id=current_user.id,
        department_id=current_user.department_id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Запуск обработки метаданных
    tasks.extract_metadata.delay(db_file.id, file.content_type)
    
    return db_file

@app.get("/files/{file_id}", response_model=schemas.FileInfo)
async def get_file_info(
    file_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(models.File).filter(models.File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Проверка прав доступа
    if not dependencies.check_file_access(file, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return file

@app.get("/files/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(models.File).filter(models.File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not dependencies.check_file_access(file, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        file_obj = minio_client.get_file(file.path)
        return StreamingResponse(
            file_obj,
            media_type=file.content_type,
            headers={"Content-Disposition": f"attachment; filename={file.name}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(models.File).filter(models.File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Проверка прав на удаление
    if current_user.role == UserRole.USER and file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can't delete other users files")
    elif current_user.role == UserRole.MANAGER and file.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="Can't delete files from other departments")
    
    try:
        minio_client.delete_file(file.path)
        db.delete(file)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/", response_model=List[schemas.FileInfo])
async def list_files(
    visibility: Optional[VisibilityLevel] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.File)
    
    # Фильтрация по правам доступа
    if current_user.role == UserRole.USER:
        query = query.filter(
            (models.File.visibility == VisibilityLevel.PUBLIC) |
            ((models.File.visibility == VisibilityLevel.DEPARTMENT) & 
             (models.File.department_id == current_user.department_id)) |
            (models.File.owner_id == current_user.id)
        )
    elif current_user.role == UserRole.MANAGER:
        query = query.filter(
            (models.File.visibility != VisibilityLevel.PRIVATE) |
            (models.File.department_id == current_user.department_id)
        )
    
    # Дополнительные фильтры
    if visibility:
        query = query.filter(models.File.visibility == visibility)
    if department_id:
        if current_user.role == UserRole.ADMIN or current_user.department_id == department_id:
            query = query.filter(models.File.department_id == department_id)
        else:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return query.all()

# Управление пользователями (для админов/менеджеров)
@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: schemas.UserCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if current_user.role == UserRole.MANAGER and user_data.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Can't create ADMIN users")
    
    db_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user_data.password)
    user = models.User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role,
        department_id=user_data.department_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/users/{user_id}", response_model=schemas.User)
async def get_user(
    user_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if current_user.role == UserRole.MANAGER and user.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="Can't access users from other departments")
    
    return user

@app.put("/users/{user_id}/role", response_model=schemas.User)
async def update_user_role(
    user_id: int,
    role_update: schemas.UserRoleUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only ADMIN can change roles")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    return user

@app.get("/users/", response_model=List[schemas.User])
async def list_users(
    department_id: Optional[int] = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.User)
    
    if current_user.role == UserRole.MANAGER:
        query = query.filter(models.User.department_id == current_user.department_id)
    elif current_user.role == UserRole.USER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if department_id:
        if current_user.role == UserRole.ADMIN:
            query = query.filter(models.User.department_id == department_id)
        else:
            raise HTTPException(status_code=403, detail="Can't filter by department")
    
    return query.all()