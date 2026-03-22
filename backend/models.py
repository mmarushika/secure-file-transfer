from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    private_key = Column(Text, nullable=False)
    public_key = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owned_files = relationship("File", back_populates="owner")
    shared_files_received = relationship("SharedFile", foreign_keys="SharedFile.shared_with_id", back_populates="shared_with_user")
    shared_files_sent = relationship("SharedFile", foreign_keys="SharedFile.owner_id", back_populates="owner_user")

class File(Base):
    __tablename__ = "files"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    encrypted_aes_key = Column(Text, nullable=False)
    iv = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="owned_files")
    shared_with = relationship("SharedFile", back_populates="file")

class SharedFile(Base):
    __tablename__ = "shared_files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("files.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    encrypted_aes_key = Column(Text, nullable=False)
    shared_at = Column(DateTime, default=datetime.utcnow)
    
    file = relationship("File", back_populates="shared_with")
    owner_user = relationship("User", foreign_keys=[owner_id], back_populates="shared_files_sent")
    shared_with_user = relationship("User", foreign_keys=[shared_with_id], back_populates="shared_files_received")
