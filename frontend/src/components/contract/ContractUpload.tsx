'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { ContractFile } from '../../types/contract';
import { validateFileType, validateFileSize, formatFileSize } from '../../lib/utils';
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
  const [selectedState, setSelectedState] = useState<'TN' | 'WA'>('TN');
  const [dragError, setDragError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setDragError(null);
      
      for (const file of acceptedFiles) {
        if (!validateFileType(file)) {
          setDragError('Only PDF files are allowed');
          return;
        }
        
        if (!validateFileSize(file)) {
          setDragError('File size must be less than 10MB');
          return;
        }

        await onUpload(file, selectedState);
      }
    },
    [onUpload, selectedState]
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
      {/* State Selection */}
      <div className="flex justify-center space-x-4">
        <label className="flex items-center">
          <input
            type="radio"
            value="TN"
            checked={selectedState === 'TN'}
            onChange={(e) => setSelectedState(e.target.value as 'TN' | 'WA')}
            className="mr-2"
          />
          <span className="text-sm font-medium">Tennessee (TN)</span>
        </label>
        <label className="flex items-center">
          <input
            type="radio"
            value="WA"
            checked={selectedState === 'WA'}
            onChange={(e) => setSelectedState(e.target.value as 'TN' | 'WA')}
            className="mr-2"
          />
          <span className="text-sm font-medium">Washington (WA)</span>
        </label>
      </div>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
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
              Maximum file size: 10MB | State: {selectedState}
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
