export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  message: string;
  error?: string;
  details?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface APIEndpoints {
  uploadContract: '/api/upload';
  getAnalysis: '/api/analysis';
  getContracts: '/api/contracts';
}
