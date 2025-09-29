'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { ContractFile } from '../../types/contract';
import { validateFileType, validateFileSize, formatFileSize } from '../../lib/utils';
import { detectStateFromFilename, validateFilesForState } from '../../lib/stateDetection';
import LoadingSpinner from '../common/LoadingSpinner';

interface ContractUploadProps {
  onUpload: (file: File, state: 'TN' | 'WA') => Promise<void>;
  contracts: ContractFile[];
  onRemove: (id: string) => void;
  isUploading: boolean;
  uploadProgress: { [key: string]: number };
  error: string | null;
}

export default function ContractUpload({
  onUpload,
  contracts,
  onRemove,
  isUploading,
  uploadProgress,
  error,
}: ContractUploadProps) {
  const [dragError, setDragError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setDragError(null);
      
      // Validate files for state detection
      const validationResults = validateFilesForState(acceptedFiles);
      
      for (const { file, result } of validationResults) {
        // Check file type and size first
        if (!validateFileType(file)) {
          setDragError('Only PDF files are allowed');
          return;
        }
        
        if (!validateFileSize(file)) {
          setDragError('File size must be less than 10MB');
          return;
        }

        // Check if state could be detected
        if (!result.state) {
          setDragError(result.error || 'Could not detect state from filename');
          return;
        }

        await onUpload(file, result.state);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxSize: 10485760, // 10MB
    multiple: true,
  });

  return (
    <div className="space-y-6">
      {/* Information Banner */}
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h3 className="text-sm font-medium text-blue-900 mb-2">Automatic State Detection</h3>
        <p className="text-sm text-blue-700">
          Contract state (TN/WA) will be automatically detected from your filename. 
          Please ensure your files contain "TN" or "WA" in the name (e.g., "contract_TN.pdf", "WA_agreement.pdf").
        </p>
      </div>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragActive
            ? 'border-blue-400 bg-blue-50 cursor-pointer'
            : 'border-gray-300 hover:border-gray-400 cursor-pointer'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        {isDragActive ? (
          <p className="text-blue-600">Drop the PDF files here...</p>
        ) : (
          <div>
            <p className="text-gray-600 mb-2">
              Drag & drop PDF contracts here, or click to select files
            </p>
            <p className="text-sm text-gray-500">
              Maximum file size: 10MB | State detected from filename
            </p>
          </div>
        )}
      </div>

      {/* Error Messages */}
      {(error || dragError) && (
        <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-md">
          <AlertCircle className="h-5 w-5" />
          <span className="text-sm">{error || dragError}</span>
        </div>
      )}

      {/* Uploaded Files List */}
      {contracts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium">Uploaded Contracts</h3>
          {contracts.map((contract) => (
            <div
              key={contract.id}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <FileText className="h-8 w-8 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900">{contract.name}</p>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(contract.size)} • {contract.state} • {contract.status}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {contract.status === 'uploading' && (
                  <div className="flex items-center space-x-2">
                    <LoadingSpinner size="sm" />
                    {uploadProgress[contract.id] && (
                      <span className="text-sm text-gray-500">
                        {uploadProgress[contract.id]}%
                      </span>
                    )}
                  </div>
                )}
                {contract.status === 'processing' && (
                  <div className="flex items-center space-x-2">
                    <LoadingSpinner size="sm" />
                    <span className="text-sm text-blue-600">Processing...</span>
                  </div>
                )}
                {contract.status === 'completed' && (
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-green-600">Complete</span>
                  </div>
                )}
                {contract.status === 'error' && (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                )}
                <button
                  onClick={() => onRemove(contract.id)}
                  className="text-gray-400 hover:text-red-500"
                  disabled={isUploading}
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
