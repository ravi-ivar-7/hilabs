import { APIResponse, UploadProgress } from '@/types/api';
import { ContractFile, ContractAnalysis } from '@/types/contract';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async uploadContract(
    file: File,
    state: 'TN' | 'WA',
    onProgress?: (progress: UploadProgress) => void
  ): Promise<APIResponse<ContractFile>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('state', state);

    try {
      const response = await fetch(`${this.baseURL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      return {
        success: false,
        message: 'Upload failed',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  async getAnalysis(contractId: string): Promise<APIResponse<ContractAnalysis>> {
    try {
      const response = await fetch(`${this.baseURL}/api/analysis/${contractId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      return {
        success: false,
        message: 'Failed to get analysis',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  async getContracts(): Promise<APIResponse<ContractFile[]>> {
    try {
      const response = await fetch(`${this.baseURL}/api/contracts`);
      const data = await response.json();
      return data;
    } catch (error) {
      return {
        success: false,
        message: 'Failed to get contracts',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}

export const apiClient = new APIClient();
