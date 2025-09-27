export interface ContractFile {
  id: string;
  name: string;
  size: number;
  type: string;
  state: 'TN' | 'WA';
  uploadedAt: Date;
  status: 'uploading' | 'uploaded' | 'processing' | 'completed' | 'error';
}

export interface ContractUploadResponse {
  success: boolean;
  contractId: string;
  message: string;
}

export interface ContractAnalysis {
  contractId: string;
  totalClauses: number;
  standardClauses: number;
  nonStandardClauses: number;
  confidence: number;
  clauses: ClauseAnalysis[];
}

export interface ClauseAnalysis {
  id: string;
  text: string;
  classification: 'Standard' | 'Non-Standard';
  confidence: number;
  attribute: string;
  reasoning: string;
}
