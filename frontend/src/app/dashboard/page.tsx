'use client';

import { useState, useEffect } from 'react';
import { FileText, CheckCircle, XCircle, Clock } from 'lucide-react';
import { ContractFile } from '@/types/contract';
import { formatFileSize } from '@/lib/utils';
import LoadingSpinner from '@/components/common/LoadingSpinner';

export default function DashboardPage() {
  const [contracts, setContracts] = useState<ContractFile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate loading contracts from API
    const loadContracts = async () => {
      setLoading(true);
      // This would be replaced with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock data for demonstration
      const mockContracts: ContractFile[] = [
        {
          id: '1',
          name: 'Healthcare_Contract_TN_001.pdf',
          size: 2048576,
          type: 'application/pdf',
          state: 'TN',
          uploadedAt: new Date('2025-01-15T10:30:00'),
          status: 'completed',
        },
        {
          id: '2',
          name: 'Medical_Agreement_WA_002.pdf',
          size: 1536000,
          type: 'application/pdf',
          state: 'WA',
          uploadedAt: new Date('2025-01-15T11:15:00'),
          status: 'processing',
        },
      ];
      
      setContracts(mockContracts);
      setLoading(false);
    };

    loadContracts();
  }, []);

  const getStatusIcon = (status: ContractFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'uploading':
        return <LoadingSpinner size="sm" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: ContractFile['status']) => {
    switch (status) {
      case 'completed':
        return 'Analysis Complete';
      case 'processing':
        return 'Processing...';
      case 'error':
        return 'Error';
      case 'uploading':
        return 'Uploading...';
      default:
        return 'Pending';
    }
  };

  const completedContracts = contracts.filter(c => c.status === 'completed').length;
  const processingContracts = contracts.filter(c => c.status === 'processing').length;
  const errorContracts = contracts.filter(c => c.status === 'error').length;

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Dashboard</h1>
        <p className="text-lg text-gray-600">
          Monitor your contract analysis progress and view results.
        </p>
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
        {contracts.length === 0 ? (
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
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">{contract.name}</h3>
                      <p className="text-sm text-gray-500">
                        {formatFileSize(contract.size)} • {contract.state} • 
                        {contract.uploadedAt.toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(contract.status)}
                    <span className="text-sm text-gray-600">{getStatusText(contract.status)}</span>
                    {contract.status === 'completed' && (
                      <button className="ml-4 text-blue-600 hover:text-blue-800 text-sm font-medium">
                        View Results
                      </button>
                    )}
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
