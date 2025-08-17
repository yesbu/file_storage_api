from pydantic import BaseModel
from ..common.enums import Visibility
class FileOut(BaseModel):
    id: int
    filename: str
    content_type: str
    size_bytes: int
    visibility: Visibility
    department: str
    downloads: int
    class Config:
        from_attributes = True
class FileMetaOut(BaseModel):
    file_id: int
    raw: dict
class FileList(BaseModel):
    items: list[FileOut]
    total: int
