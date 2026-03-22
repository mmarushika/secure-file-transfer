# Secure File Transfer Platform

A secure file transfer platform that allows users to upload, store, and share files with end-to-end encryption using AES and RSA algorithms.

## Features

- **User Authentication**: Secure login and registration system
- **File Upload/Download**: Upload and download files with AES-256 encryption
- **Secure Sharing**: Share files with other users using RSA encryption
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- **End-to-End Encryption**: Files are encrypted using AES-256, with keys encrypted using RSA-2048

## Security Architecture

### Encryption Process
1. **File Upload**: 
   - Generate a random AES-256 key for each file
   - Encrypt the file content using AES-256 in CFB mode
   - Encrypt the AES key using the owner's RSA public key
   - Store the encrypted file and encrypted AES key

2. **File Sharing**:
   - Decrypt the AES key with the owner's RSA private key
   - Re-encrypt the AES key with the recipient's RSA public key
   - Store the shared file record with the re-encrypted AES key

3. **File Download**:
   - Decrypt the AES key with the user's RSA private key
   - Decrypt the file content using the AES key
   - Stream the decrypted file to the user

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Cryptography**: Python cryptography library for AES and RSA operations
- **SQLite**: Database for development (easily switchable to PostgreSQL/MySQL)
- **JWT**: Token-based authentication

### Frontend
- **React**: Modern JavaScript library for building user interfaces
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Axios**: HTTP client for API requests
- **Lucide React**: Beautiful icons

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r ../requirements.txt
```

4. Set up environment variables:
```bash
cp ../.env.example .env
# Edit .env with your configuration
```

5. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The application will be available at `http://localhost:3000`

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Main Endpoints

- `POST /register` - Register a new user
- `POST /token` - Login and get access token
- `GET /users/me` - Get current user info
- `POST /upload` - Upload a file
- `GET /files` - List user's files
- `GET /files/{file_id}/download` - Download a file
- `POST /files/{file_id}/share` - Share a file with another user
- `GET /shared-files` - List files shared with current user

## Usage

1. **Register**: Create a new account with email, username, and password
2. **Login**: Sign in to your account
3. **Upload Files**: Drag and drop or click to upload files
4. **Manage Files**: View, download, and share your files
5. **Shared Files**: Access files that have been shared with you

## Security Notes

- All files are encrypted using AES-256 with unique keys
- AES keys are encrypted using RSA-2048 public keys
- Private keys are stored encrypted in the database
- JWT tokens are used for authentication
- File sharing uses end-to-end encryption
- No plaintext files are ever stored on disk

## Development

### Project Structure
```
secure-file-transfer/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── auth.py              # Authentication utilities
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── contexts/       # React contexts
│   │   └── utils/          # Utility functions
│   ├── public/
│   └── package.json
├── uploads/                # Encrypted file storage
├── requirements.txt        # Python dependencies
└── README.md
```

### Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=sqlite:///./secure_file_transfer.db
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for educational purposes to demonstrate secure file transfer concepts
- Uses industry-standard encryption algorithms
- Implements modern web development best practices
