export interface ContractResponse {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  state: string;
  status: string;
  processing_progress?: number;
  processing_message?: string;
  created_at: string;
  processing_started_at?: string;
  processing_completed_at?: string;
  total_clauses?: number;
  standard_clauses?: number;
  non_standard_clauses?: number;
  error_message?: string;
}

export interface ContractStatusResponse {
  id: string;
  status: string;
  processing_progress?: number;
  processing_message?: string;
  created_at: string;
  processing_started_at?: string;
  processing_completed_at?: string;
}

export interface ClauseResponse {
  id: string;
  clause_number: number;
  attribute_name: string;
  clause_text: string;
  classification?: string;
  confidence_score?: number;
  template_match_text?: string;
  similarity_score?: number;
  match_type?: string;
  classification_steps?: string; // JSON string of classification steps
  template_attribute?: string;
  extraction_method?: string;
}

export interface ContractResultsResponse {
  contract: ContractResponse;
  clauses: ClauseResponse[];
  summary: {
    total_clauses: number;
    standard_clauses: number;
    non_standard_clauses: number;
    ambiguous_clauses: number;
    processing_time?: number;
    accuracy_score?: number;
  };
}

// Legacy interfaces for backward compatibility
export interface ContractFile extends ContractResponse {
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  processing_progress?: number;
  processing_message?: string;
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
