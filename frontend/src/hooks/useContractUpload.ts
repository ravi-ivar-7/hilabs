import { useState, useCallback } from 'react';
import { ContractFile, ContractResponse } from '../types/contract';
import { apiClient } from '../lib/api';
import { UploadProgress } from '../types/api';

export interface UseContractUploadReturn {
  contracts: ContractFile[];
  isUploading: boolean;
  uploadProgress: { [key: string]: number };
  uploadContract: (file: File, state: 'TN' | 'WA') => Promise<void>;
  removeContract: (id: string) => void;
  error: string | null;
  successMessage: string | null;
  getContractStatus: (contractId: string) => Promise<void>;
  getContractResults: (contractId: string) => Promise<any>;
}

function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}

function convertToContractFile(response: ContractResponse): ContractFile {
  return {
    ...response,
    name: response.original_filename,
    size: response.file_size,
    type: 'application/pdf',
    uploadedAt: new Date(response.created_at),
  };
}

export function useContractUpload(): UseContractUploadReturn {
  const [contracts, setContracts] = useState<ContractFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const uploadContract = useCallback(async (file: File, state: 'TN' | 'WA') => {
    const tempId = generateId();
    const newContract: ContractFile = {
      id: tempId,
      filename: file.name,
      original_filename: file.name,
      file_size: file.size,
      state,
      status: 'uploading',
      created_at: new Date().toISOString(),
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date(),
    };

    setContracts(prev => [...prev, newContract]);
    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);
    setUploadProgress(prev => ({ ...prev, [tempId]: 0 }));

    try {
      const result = await apiClient.uploadContract(file, state);
      
      if (result.success && result.data) {
        const contractData = result.data as ContractResponse;
        const updatedContract = convertToContractFile(contractData);
        
        setContracts(prev =>
          prev.map(contract =>
            contract.id === tempId ? updatedContract : contract
          )
        );
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[tempId];
          return newProgress;
        });
        
        setIsUploading(false);
        const allUploaded = contracts.every(c => c.status === 'uploaded' || c.status === 'error');
        if (allUploaded) {
          setSuccessMessage('All files uploaded successfully! Check the Analysis page to monitor processing status.');
        }
      } else {
        setContracts(prev =>
          prev.map(contract =>
            contract.id === tempId
              ? { ...contract, status: 'error' }
              : contract
          )
        );
        const errorMessage = result.details 
          ? `${result.message}: ${result.details}` 
          : result.message || 'Upload failed';
        setError(errorMessage);
      }
    } catch (err) {
      setContracts(prev =>
        prev.map(contract =>
          contract.id === tempId
            ? { ...contract, status: 'error' }
            : contract
        )
      );
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }, []);

  const getContractStatus = useCallback(async (contractId: string) => {
    try {
      const response = await apiClient.refreshContractStatus(contractId);
      if (response.success && response.data) {
        setContracts(prev =>
          prev.map(contract =>
            contract.id === contractId
              ? { 
                  ...contract, 
                  status: response.data.status,
                  processing_progress: response.data.processing_progress,
                  processing_message: response.data.processing_message
                }
              : contract
          )
        );
      }
    } catch (err) {
      console.error('Failed to get contract status:', err);
    }
  }, []);

  const getContractResults = useCallback(async (contractId: string) => {
    try {
      const response = await apiClient.getContractResults(contractId);
      if (response.success) {
        return response.data;
      }
      throw new Error(response.message || 'Failed to get results');
    } catch (err) {
      console.error('Failed to get contract results:', err);
      throw err;
    }
  }, []);

  const removeContract = useCallback((id: string) => {
    setContracts(prev => prev.filter(contract => contract.id !== id));
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[id];
      return newProgress;
    });
  }, []);

  return {
    contracts,
    isUploading,
    uploadProgress,
    uploadContract,
    removeContract,
    error,
    successMessage,
    getContractStatus,
    getContractResults,
  };
}
