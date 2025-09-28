'use client';

import { useState, useEffect } from 'react';
import { FileText, CheckCircle, XCircle, Clock } from 'lucide-react';
import { ContractFile } from '../../types/contract';
import { formatFileSize } from '../../lib/utils';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ContractResults from '../../components/contract/ContractResults';
import { useContractUpload } from '../../hooks/useContractUpload';
import { apiClient } from '../../lib/api';

export default function AnalysisPage() {
  const { getContractResults } = useContractUpload();
  const [contracts, setContracts] = useState<ContractFile[]>([]);
  const [selectedContract, setSelectedContract] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshingAll, setRefreshingAll] = useState(false);
  const [refreshingContract, setRefreshingContract] = useState<string | null>(null);
  const [deletingContract, setDeletingContract] = useState<string | null>(null);
  const [pollingIntervals, setPollingIntervals] = useState<Map<string, NodeJS.Timeout>>(new Map());

  const getStatusBadge = (status: string) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize";
    
    if (status === 'completed') {
      return (
        <span className={`${baseClasses} bg-green-100 text-green-800`}>
          <CheckCircle className="h-3 w-3 mr-1" />
          {status}
        </span>
      );
    } else if (status === 'failed' || status === 'error') {
      return (
        <span className={`${baseClasses} bg-red-100 text-red-800`}>
          <XCircle className="h-3 w-3 mr-1" />
          {status}
        </span>
      );
    } else {
      return (
        <span className={`${baseClasses} bg-yellow-100 text-yellow-800`}>
          <Clock className="h-3 w-3 mr-1" />
          {status}
        </span>
      );
    }
  };
  const needsPolling = (status: string) => {
    return !['completed', 'failed', 'error'].includes(status);
  };

  // Start polling for a specific contract
  const startPolling = (contractId: string) => {
    // Clear existing interval if any
    const existingInterval = pollingIntervals.get(contractId);
    if (existingInterval) {
      clearInterval(existingInterval);
    }

    const interval = setInterval(async () => {
      try {
        const response = await apiClient.refreshContractStatus(contractId);
        
        if (response.success && response.data) {
          const updatedContract = response.data;
          
          setContracts(prev => {
            const updated = prev.map(contract => {
              if (contract.id === contractId) {
                return {
                  ...contract,
                  status: updatedContract.status,
                  processing_progress: updatedContract.processing_progress,
                  processing_message: updatedContract.processing_message,
                };
              }
              return contract;
            });
            return updated;
          });

          // Stop polling if contract is completed or failed
          if (!needsPolling(updatedContract.status)) {
            clearInterval(interval);
            setPollingIntervals(prev => {
              const newMap = new Map(prev);
              newMap.delete(contractId);
              return newMap;
            });
          }
        } else {
          // If contract not found (404) or other error, stop polling
          clearInterval(interval);
          setPollingIntervals(prev => {
            const newMap = new Map(prev);
            newMap.delete(contractId);
            return newMap;
          });
        }
      } catch (error) {
        // Stop polling on persistent errors (like 404)
        clearInterval(interval);
        setPollingIntervals(prev => {
          const newMap = new Map(prev);
          newMap.delete(contractId);
          return newMap;
        });
      }
    }, 1000); // Poll every 1 second for faster updates

    setPollingIntervals(prev => new Map(prev).set(contractId, interval));
  };

  // Stop polling for a specific contract
  const stopPolling = (contractId: string) => {
    const interval = pollingIntervals.get(contractId);
    if (interval) {
      clearInterval(interval);
      setPollingIntervals(prev => {
        const newMap = new Map(prev);
        newMap.delete(contractId);
        return newMap;
      });
    }
  };

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await apiClient.getAllContracts();
        if (response.success && response.data) {
          const contractFiles: ContractFile[] = response.data.map((contract: any) => ({
            id: contract.id,
            filename: contract.filename,
            original_filename: contract.original_filename,
            file_size: contract.file_size,
            state: contract.state,
            status: contract.status,
            processing_progress: contract.processing_progress,
            processing_message: contract.processing_message,
            created_at: contract.created_at,
            name: contract.original_filename,
            size: contract.file_size,
            type: 'application/pdf',
            uploadedAt: new Date(contract.created_at),
          }));
          setContracts(contractFiles);

          // Start polling for contracts that need it
          contractFiles.forEach(contract => {
            if (needsPolling(contract.status)) {
              startPolling(contract.id);
            }
          });
        }
      } catch (error) {
        console.error('Failed to fetch contracts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchContracts();

    // Cleanup intervals on unmount
    return () => {
      pollingIntervals.forEach(interval => clearInterval(interval));
    };
  }, []);

  // Effect to manage polling when contracts change
  useEffect(() => {
    contracts.forEach(contract => {
      if (needsPolling(contract.status) && !pollingIntervals.has(contract.id)) {
        startPolling(contract.id);
      } else if (!needsPolling(contract.status) && pollingIntervals.has(contract.id)) {
        stopPolling(contract.id);
      }
    });
  }, [contracts]);

  const handleRefreshStatus = async (contractId: string) => {
    try {
      setRefreshingContract(contractId);
      const response = await apiClient.refreshContractStatus(contractId);
      if (response.success && response.data) {
        const updatedContract = response.data;
        const contractFile: ContractFile = {
          id: updatedContract.id,
          filename: updatedContract.filename,
          original_filename: updatedContract.original_filename,
          file_size: updatedContract.file_size,
          state: updatedContract.state,
          status: updatedContract.status,
          processing_progress: updatedContract.processing_progress,
          processing_message: updatedContract.processing_message,
          created_at: updatedContract.created_at,
          name: updatedContract.original_filename,
          size: updatedContract.file_size,
          type: 'application/pdf',
          uploadedAt: new Date(updatedContract.created_at),
        };
        
        // Update only this specific contract in the list
        setContracts(prev => 
          prev.map(contract => 
            contract.id === contractId ? contractFile : contract
          )
        );
      }
    } catch (error) {
      console.error('Failed to refresh contract status:', error);
    } finally {
      setRefreshingContract(null);
    }
  };


  const handleRefreshAll = async () => {
    try {
      setRefreshingAll(true);
      const response = await apiClient.getAllContracts();
      if (response.success && response.data) {
        const contractFiles: ContractFile[] = response.data.map((contract: any) => ({
          id: contract.id,
          filename: contract.filename,
          original_filename: contract.original_filename,
          file_size: contract.file_size,
          state: contract.state,
          status: contract.status,
          processing_progress: contract.processing_progress,
          processing_message: contract.processing_message,
          created_at: contract.created_at,
          name: contract.original_filename,
          size: contract.file_size,
          type: 'application/pdf',
          uploadedAt: new Date(contract.created_at),
        }));
        setContracts(contractFiles);
      }
    } catch (error) {
      console.error('Failed to refresh contracts:', error);
    } finally {
      setRefreshingAll(false);
    }
  };

  const handleDeleteContract = async (contractId: string) => {
    if (!confirm('Are you sure you want to delete this contract? This action cannot be undone.')) {
      return;
    }
    
    try {
      setDeletingContract(contractId);
      const response = await apiClient.deleteContract(contractId);
      
      if (response.success) {
        setContracts(prev => prev.filter(c => c.id !== contractId));
      } else {
        alert('Failed to delete contract: ' + (response.message || 'Unknown error'));
      }
    } catch (error) {
      alert('Failed to delete contract: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setDeletingContract(null);
    }
  };

  const completedContracts = contracts.filter(c => c.status === 'completed').length;
  const processingContracts = contracts.filter(c => 
    c.status === 'processing' || c.status === 'uploaded' || c.status === 'queued' || c.status === 'preprocessed'
  ).length;
  const errorContracts = contracts.filter(c => c.status === 'error' || c.status === 'failed').length;

  if (selectedContract) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-6">
          <button
            onClick={() => setSelectedContract(null)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            ← Back to Analysis
          </button>
        </div>
        <ContractResults
          contractId={selectedContract}
          onGetResults={getContractResults}
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-gray-900">Contract Analysis</h1>
          <button
            onClick={handleRefreshAll}
            disabled={refreshingAll}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {refreshingAll ? (
              <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            {refreshingAll ? 'Refreshing...' : 'Refresh All'}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Contracts</p>
              <p className="text-2xl font-bold text-gray-900">{contracts.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Completed</p>
              <p className="text-2xl font-bold text-gray-900">{completedContracts}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Processing</p>
              <p className="text-2xl font-bold text-gray-900">{processingContracts}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <XCircle className="h-8 w-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Errors</p>
              <p className="text-2xl font-bold text-gray-900">{errorContracts}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Contracts List */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Recent Contracts</h2>
        </div>
        {loading ? (
          <div className="p-12 text-center">
            <LoadingSpinner size="lg" />
            <p className="text-gray-500 mt-4">Loading contracts...</p>
          </div>
        ) : contracts.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No contracts uploaded</h3>
            <p className="text-gray-500 mb-4">Get started by uploading your first contract.</p>
            <a
              href="/upload"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Upload Contract
            </a>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {contracts.map((contract) => (
              <div key={contract.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <FileText className="h-10 w-10 text-blue-600" />
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-2">
                          <h3 className="text-sm font-medium text-gray-900">{contract.name}</h3>
                          {pollingIntervals.has(contract.id) && (
                            <div className="flex items-center">
                              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            </div>
                          )}
                        </div>
                        {getStatusBadge(contract.status)}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {formatFileSize(contract.size)} • {contract.state} • 
                        {contract.uploadedAt.toLocaleDateString()}
                      </p>
                      {(contract.processing_message || contract.processing_progress !== undefined) && (
                        <div className="mt-2">
                          <div className="flex items-center space-x-2">
                            {contract.processing_message && (
                              <div className="text-xs text-blue-600 font-medium">
                                {contract.processing_message}
                              </div>
                            )}
                            {contract.processing_progress !== undefined && contract.processing_progress !== null && (
                              <div className="text-xs text-gray-500">
                                ({contract.processing_progress}%)
                              </div>
                            )}
                          </div>
                          {contract.processing_progress !== undefined && contract.processing_progress !== null && (
                            <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
                              <div 
                                className="bg-blue-600 h-1.5 rounded-full transition-all duration-300" 
                                style={{ width: `${contract.processing_progress}%` }}
                              ></div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <button 
                      onClick={() => handleRefreshStatus(contract.id)}
                      disabled={refreshingContract === contract.id}
                      className="inline-flex items-center px-3 py-1.5 border border-blue-300 text-xs font-medium rounded-md text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {refreshingContract === contract.id ? (
                        <>
                          <svg className="animate-spin h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Refreshing...
                        </>
                      ) : (
                        'Refresh Status'
                      )}
                    </button>
                    <button 
                      onClick={() => setSelectedContract(contract.id)}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    >
                      View Results
                    </button>
                    <button 
                      onClick={() => handleDeleteContract(contract.id)}
                      disabled={deletingContract === contract.id}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {deletingContract === contract.id ? (
                        <>
                          <svg className="animate-spin h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Deleting...
                        </>
                      ) : (
                        'Delete'
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
