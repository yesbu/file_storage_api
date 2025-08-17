import uuid
from fastapi import HTTPException, UploadFile
from ..common.enums import Visibility, Role
from ..auth.models import User
from ..storage.s3 import put_object
ALLOWED_TYPES_USER = {"application/pdf"}
ALLOWED_TYPES_MANAGER = {"application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_SIZE = {
    Role.USER: 10 * 1024 * 1024,
    Role.MANAGER: 50 * 1024 * 1024,
    Role.ADMIN: 100 * 1024 * 1024,
}
def validate_upload(user: User, file: UploadFile, visibility: Visibility):
    if user.role == Role.USER:
        if visibility != Visibility.PRIVATE:
            raise HTTPException(403, "USER can create only PRIVATE files")
        if file.content_type not in ALLOWED_TYPES_USER:
            raise HTTPException(400, "USER can upload only PDF")
    else:
        if file.content_type not in ALLOWED_TYPES_MANAGER and user.role != Role.ADMIN:
            raise HTTPException(400, "Unsupported file type")
    return
def store_file(file: UploadFile, content: bytes) -> tuple[str, int]:
    size = len(content)
    key = f"{uuid.uuid4().hex}_{file.filename}"
    put_object(key, content, file.content_type or "application/octet-stream")
    return key, size
