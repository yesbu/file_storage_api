from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(Enum("USER", "MANAGER", "ADMIN", name="user_roles"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    department = relationship("Department", back_populates="users")
    files = relationship("File", back_populates="owner")

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    filepath = Column(String)
    visibility = Column(Enum("PRIVATE", "DEPARTMENT", "PUBLIC", name="visibility_levels"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="files")
    file_metadata = relationship("FileMetadata", uselist=False, back_populates="file")

class FileMetadata(Base):
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True)
    pages = Column(Integer)
    author = Column(String)
    title = Column(String)
    file_id = Column(Integer, ForeignKey("files.id"))
    
    file = relationship("File", back_populates="file_metadata")

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    users = relationship("User", back_populates="department")