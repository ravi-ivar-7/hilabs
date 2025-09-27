'use client';

import { useContractUpload } from '@/hooks/useContractUpload';
import ContractUpload from '@/components/contract/ContractUpload';

export default function UploadPage() {
  const { contracts, isUploading, uploadContract, removeContract, error } = useContractUpload();

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

      <div className="bg-white rounded-lg shadow-sm p-8">
        <ContractUpload
          onUpload={uploadContract}
          contracts={contracts}
          onRemove={removeContract}
          isUploading={isUploading}
          error={error}
        />
      </div>

      {/* Instructions */}
      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Upload Instructions</h3>
        <ul className="space-y-2 text-blue-800">
          <li>• Only PDF files are supported (max 10MB per file)</li>
          <li>• Select the correct state (TN for Tennessee, WA for Washington)</li>
          <li>• Multiple files can be uploaded simultaneously</li>
          <li>• Processing will begin automatically after upload</li>
          <li>• Results will be available in the dashboard once analysis is complete</li>
        </ul>
      </div>
    </div>
  );
}
