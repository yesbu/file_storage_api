from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Enum as SAEnum, ForeignKey, JSON, DateTime, BigInteger
from datetime import datetime
from ..common.enums import Visibility
from ..database import Base
class File(Base):
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    department: Mapped[str] = mapped_column(String(100), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    visibility: Mapped[Visibility] = mapped_column(SAEnum(Visibility), default=Visibility.PRIVATE)
    s3_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    owner = relationship("User", back_populates="files")
    metadata_rel = relationship("FileMetadata", uselist=False, back_populates="file", cascade="all, delete-orphan")
class FileMetadata(Base):
    __tablename__ = "file_metadata"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), unique=True)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    file = relationship("File", back_populates="metadata_rel")
