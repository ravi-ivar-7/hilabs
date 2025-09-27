import { useState, useCallback } from 'react';
import { ContractFile } from '@/types/contract';
import { apiClient } from '@/lib/api';
import { generateId } from '@/lib/utils';

export interface UseContractUploadReturn {
  contracts: ContractFile[];
  isUploading: boolean;
  uploadContract: (file: File, state: 'TN' | 'WA') => Promise<void>;
  removeContract: (id: string) => void;
  error: string | null;
}

export function useContractUpload(): UseContractUploadReturn {
  const [contracts, setContracts] = useState<ContractFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadContract = useCallback(async (file: File, state: 'TN' | 'WA') => {
    const contractId = generateId();
    const newContract: ContractFile = {
      id: contractId,
      name: file.name,
      size: file.size,
      type: file.type,
      state,
      uploadedAt: new Date(),
      status: 'uploading',
    };

    setContracts(prev => [...prev, newContract]);
    setIsUploading(true);
    setError(null);

    try {
      const response = await apiClient.uploadContract(file, state);
      
      if (response.success) {
        setContracts(prev =>
          prev.map(contract =>
            contract.id === contractId
              ? { ...contract, status: 'uploaded' }
              : contract
          )
        );
      } else {
        setContracts(prev =>
          prev.map(contract =>
            contract.id === contractId
              ? { ...contract, status: 'error' }
              : contract
          )
        );
        setError(response.message || 'Upload failed');
      }
    } catch (err) {
      setContracts(prev =>
        prev.map(contract =>
          contract.id === contractId
            ? { ...contract, status: 'error' }
            : contract
        )
      );
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }, []);

  const removeContract = useCallback((id: string) => {
    setContracts(prev => prev.filter(contract => contract.id !== id));
  }, []);

  return {
    contracts,
    isUploading,
    uploadContract,
    removeContract,
    error,
  };
}
