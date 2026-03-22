from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import os
import shutil
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import json
import uuid

from database import get_db, engine, Base
from models import User, File as FileModel, SharedFile
from schemas import UserCreate, UserResponse, Token, FileResponse, ShareRequest
from auth import authenticate_user, create_access_token, get_current_user, get_password_hash

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure File Transfer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

UPLOAD_DIR = "../uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class EncryptionService:
    @staticmethod
    def generate_rsa_keys():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem.decode('utf-8'), public_pem.decode('utf-8')
    
    @staticmethod
    def generate_aes_key():
        return os.urandom(32)
    
    @staticmethod
    def encrypt_with_aes(data: bytes, key: bytes) -> tuple:
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        return encrypted_data, iv
    
    @staticmethod
    def decrypt_with_aes(encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_data) + decryptor.finalize()
    
    @staticmethod
    def encrypt_with_rsa(data: bytes, public_key_pem: str) -> bytes:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted
    
    @staticmethod
    def decrypt_with_rsa(encrypted_data: bytes, private_key_pem: str) -> bytes:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        decrypted = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted

@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    private_key, public_key = EncryptionService.generate_rsa_keys()
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        private_key=private_key,
        public_key=public_key
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(id=db_user.id, email=db_user.email, username=db_user.username)

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email, username=current_user.username)

@app.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_id = str(uuid.uuid4())
    aes_key = EncryptionService.generate_aes_key()
    
    file_content = await file.read()
    encrypted_content, iv = EncryptionService.encrypt_with_aes(file_content, aes_key)
    
    encrypted_aes_key = EncryptionService.encrypt_with_rsa(aes_key, current_user.public_key)
    
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.enc")
    with open(file_path, "wb") as f:
        f.write(encrypted_content)
    
    db_file = FileModel(
        id=file_id,
        filename=file.filename,
        original_filename=file.filename,
        file_size=len(file_content),
        mime_type=file.content_type,
        owner_id=current_user.id,
        encrypted_aes_key=base64.b64encode(encrypted_aes_key).decode('utf-8'),
        iv=base64.b64encode(iv).decode('utf-8')
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return FileResponse(
        id=db_file.id,
        filename=db_file.filename,
        original_filename=db_file.original_filename,
        file_size=db_file.file_size,
        mime_type=db_file.mime_type,
        created_at=db_file.created_at
    )

@app.get("/files", response_model=List[FileResponse])
async def list_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    files = db.query(FileModel).filter(FileModel.owner_id == current_user.id).all()
    return [
        FileResponse(
            id=f.id,
            filename=f.filename,
            original_filename=f.original_filename,
            file_size=f.file_size,
            mime_type=f.mime_type,
            created_at=f.created_at
        )
        for f in files
    ]

@app.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_record.owner_id != current_user.id:
        shared_file = db.query(SharedFile).filter(
            SharedFile.file_id == file_id,
            SharedFile.shared_with_id == current_user.id
        ).first()
        if not shared_file:
            raise HTTPException(status_code=403, detail="Access denied")
        # Use the shared file's encrypted AES key
        encrypted_aes_key = base64.b64decode(shared_file.encrypted_aes_key)
    else:
        # Owner downloading their own file
        encrypted_aes_key = base64.b64decode(file_record.encrypted_aes_key)
    
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.enc")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    with open(file_path, "rb") as f:
        encrypted_content = f.read()
    
    iv = base64.b64decode(file_record.iv)
    
    try:
        aes_key = EncryptionService.decrypt_with_rsa(encrypted_aes_key, current_user.private_key)
        decrypted_content = EncryptionService.decrypt_with_aes(encrypted_content, aes_key, iv)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to decrypt file")
    
    from fastapi.responses import Response
    return Response(
        content=decrypted_content,
        media_type=file_record.mime_type,
        headers={"Content-Disposition": f"attachment; filename={file_record.original_filename}"}
    )

@app.post("/files/{file_id}/share")
async def share_file(
    file_id: str,
    share_request: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can share files")
    
    target_user = db.query(User).filter(User.email == share_request.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_share = db.query(SharedFile).filter(
        SharedFile.file_id == file_id,
        SharedFile.shared_with_id == target_user.id
    ).first()
    
    if existing_share:
        raise HTTPException(status_code=400, detail="File already shared with this user")
    
    encrypted_aes_key = base64.b64decode(file_record.encrypted_aes_key)
    aes_key = EncryptionService.decrypt_with_rsa(encrypted_aes_key, current_user.private_key)
    
    reencrypted_aes_key = EncryptionService.encrypt_with_rsa(aes_key, target_user.public_key)
    
    shared_file = SharedFile(
        file_id=file_id,
        owner_id=current_user.id,
        shared_with_id=target_user.id,
        encrypted_aes_key=base64.b64encode(reencrypted_aes_key).decode('utf-8')
    )
    db.add(shared_file)
    db.commit()
    
    return {"message": f"File shared successfully with {target_user.email}"}

@app.get("/shared-files", response_model=List[FileResponse])
async def list_shared_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    shared_files = db.query(SharedFile).filter(SharedFile.shared_with_id == current_user.id).all()
    files = []
    for sf in shared_files:
        file_record = db.query(FileModel).filter(FileModel.id == sf.file_id).first()
        if file_record:
            files.append(FileResponse(
                id=file_record.id,
                filename=file_record.filename,
                original_filename=file_record.original_filename,
                file_size=file_record.file_size,
                mime_type=file_record.mime_type,
                created_at=file_record.created_at
            ))
    return files

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
