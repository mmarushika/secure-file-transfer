import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fileAPI, FileData } from '../services/api';
import { Upload, Download, Share2, Trash2, File as FileIcon } from 'lucide-react';

const MyFiles: React.FC = () => {
  const [files, setFiles] = useState<FileData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [shareEmail, setShareEmail] = useState('');
  const [sharingFileId, setSharingFileId] = useState<string | null>(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const response = await fileAPI.getFiles();
      setFiles(response.data);
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await fileAPI.upload(file);
      loadFiles();
    } catch (error) {
      console.error('Failed to upload file:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (fileId: string, filename: string) => {
    try {
      const response = await fileAPI.downloadFile(fileId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download file:', error);
    }
  };

  const handleShare = async (fileId: string) => {
    if (!shareEmail) return;

    try {
      await fileAPI.shareFile(fileId, shareEmail);
      setShareEmail('');
      setSharingFileId(null);
      alert('File shared successfully!');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to share file');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/dashboard" className="text-blue-600 hover:text-blue-800">
                ← Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">My Files</h1>
            <p className="mt-2 text-gray-600">Manage and share your uploaded files</p>
          </div>

          <div className="mb-8">
            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <Upload className="w-8 h-8 mb-4 text-gray-500" />
                <p className="mb-2 text-sm text-gray-500">
                  <span className="font-semibold">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-gray-500">Any file type</p>
              </div>
              <input
                type="file"
                className="hidden"
                onChange={handleFileUpload}
                disabled={uploading}
              />
            </label>
            {uploading && (
              <div className="mt-2 text-sm text-blue-600">Uploading file...</div>
            )}
          </div>

          {files.length === 0 ? (
            <div className="text-center py-12">
              <FileIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No files</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by uploading a file.
              </p>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {files.map((file) => (
                  <li key={file.id}>
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <FileIcon className="h-8 w-8 text-gray-400 mr-3" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {file.original_filename}
                            </p>
                            <p className="text-sm text-gray-500">
                              {formatFileSize(file.file_size)} • {formatDate(file.created_at)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleDownload(file.id, file.original_filename)}
                            className="p-2 text-gray-600 hover:text-blue-600"
                            title="Download"
                          >
                            <Download className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => setSharingFileId(sharingFileId === file.id ? null : file.id)}
                            className="p-2 text-gray-600 hover:text-green-600"
                            title="Share"
                          >
                            <Share2 className="h-5 w-5" />
                          </button>
                        </div>
                      </div>
                      
                      {sharingFileId === file.id && (
                        <div className="mt-4 flex items-center space-x-2">
                          <input
                            type="email"
                            placeholder="Enter email to share with"
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            value={shareEmail}
                            onChange={(e) => setShareEmail(e.target.value)}
                          />
                          <button
                            onClick={() => handleShare(file.id)}
                            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                          >
                            Share
                          </button>
                          <button
                            onClick={() => {
                              setSharingFileId(null);
                              setShareEmail('');
                            }}
                            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                          >
                            Cancel
                          </button>
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default MyFiles;
