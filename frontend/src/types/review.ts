export interface ReviewFeedback {
  clause_id: string;
  original_classification: string;
  user_classification: 'Standard' | 'Non-Standard' | 'Ambiguous';
  confidence_rating: number;
  user_comments?: string;
}
