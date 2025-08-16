from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .models import User
from .database import SessionLocal
from datetime import timedelta
from fastapi import UploadFile, File

app = FastAPI()

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    print(f"Поиск пользователя: {form_data.username}")  # Логирование
    user = authenticate_user(db, form_data.username, form_data.password)
    print(f"Найден пользователь: {user}")  # Логирование
    db.close()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # Теперь status будет определен
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
# Защищённый эндпоинт (пример)
@app.get("/auth/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
        "department": current_user.department.name
    }

@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "USER" and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="USERs can upload only PDF files"
        )
    # Логика загрузки файла
    return {"filename": file.filename}