import { APIResponse, UploadProgress } from '../types/api';
import { ContractFile, ContractAnalysis } from '../types/contract';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async uploadContract(
    file: File,
    state: 'TN' | 'WA'
  ): Promise<APIResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('state', state);

    try {
      const response = await fetch(`${this.baseURL}/api/v1/contracts/upload`, {
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

  async getContractResults(contractId: string): Promise<APIResponse<any>> {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/contracts/${contractId}/results`);
      const data = await response.json();
      return data;
    } catch (error) {
      return {
        success: false,
        message: 'Failed to get contract results',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  async refreshContractStatus(contractId: string): Promise<APIResponse<any>> {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/contracts/${contractId}/status`);
      const data = await response.json();
      return data;
    } catch (error) {
      return {
        success: false,
        message: 'Failed to refresh contract status',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  async deleteContract(contractId: string): Promise<APIResponse<any>> {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/contracts/${contractId}`, {
        method: 'DELETE',
      });
      const data = await response.json();
      return data;
    } catch (error) {
      return {
        success: false,
        message: 'Failed to delete contract',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  async getAllContracts(skip: number = 0, limit: number = 100, state?: string, status?: string): Promise<APIResponse<any>> {
    try {
      const params = new URLSearchParams();
      if (skip > 0) params.append('skip', skip.toString());
      if (limit !== 100) params.append('limit', limit.toString());
      if (state) params.append('state', state);
      if (status) params.append('status', status);
      
      const queryString = params.toString();
      const url = `${this.baseURL}/api/v1/contracts/${queryString ? '?' + queryString : ''}`;
      
      const response = await fetch(url);
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

  async healthCheck(): Promise<APIResponse<any>> {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/health`);
      const data = await response.json();
      return data;
    } catch (error) {
      return {
        success: false,
        message: 'Health check failed',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}

export const apiClient = new APIClient();
