'use client';

import { useRouter } from 'next/navigation';
import { useContractUpload } from '../../hooks/useContractUpload';
import ContractUpload from '../../components/contract/ContractUpload';

export default function UploadPage() {
  const router = useRouter();
  const { contracts, isUploading, uploadProgress, uploadContract, removeContract, error, successMessage } = useContractUpload();

  const handleUpload = async (file: File, state: 'TN' | 'WA') => {
    await uploadContract(file, state, () => {
      setTimeout(() => {
        router.push('/analysis');
      }, 500);  
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Upload Healthcare Contracts
        </h1>
        <p className="text-lg text-gray-600">
          Upload PDF contracts for analysis and classification. Select the appropriate state template for comparison.
        </p>
      </div>

      {successMessage && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-green-800 mb-3">
                {successMessage}
              </p>
              <a
                href="/analysis"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
              >
                <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                View Analysis Dashboard
              </a>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-8">
        <ContractUpload
          onUpload={handleUpload}
          contracts={contracts}
          onRemove={removeContract}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
          error={error}
        />
      </div>

      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Upload Instructions</h3>
        <ul className="space-y-2 text-blue-800">
          <li>• Only PDF files are supported (max 10MB per file)</li>
          <li>• Select the correct state (TN for Tennessee, WA for Washington)</li>
          <li>• Multiple files can be uploaded simultaneously</li>
          <li>• Processing will begin automatically after upload</li>
          <li>• Results will be available in the analysis page once processing is complete</li>
        </ul>
      </div>
    </div>
  );
}
