'use client';

import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Eye, MessageSquare, Clock, FileText, ChevronDown, ChevronRight, Edit3 } from 'lucide-react';
import { ContractAnalysis, ClauseResponse } from '../../types/contract';
import ReviewModal from './ReviewModal';
import { ReviewFeedback } from '../../types/review';
import { apiClient } from '../../lib/api';
import { ContractResultsResponse } from '../../types/contract';
import LoadingSpinner from '../common/LoadingSpinner';

interface ContractResultsProps {
  contractId: string;
  onGetResults: (contractId: string) => Promise<ContractResultsResponse>;
}

export default function ContractResults({ contractId, onGetResults }: ContractResultsProps) {
  const [results, setResults] = useState<ContractResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedClauses, setExpandedClauses] = useState<Set<string>>(new Set());
  const [expandedClauseTexts, setExpandedClauseTexts] = useState<Set<string>>(new Set());
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedClauseForReview, setSelectedClauseForReview] = useState<ClauseResponse | null>(null);
  const [submittedFeedback, setSubmittedFeedback] = useState<Map<string, ReviewFeedback>>(new Map());

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await onGetResults(contractId);
        setResults(data);
        
        if (data?.clauses && data.clauses.length > 0) {
          setExpandedClauses(new Set([data.clauses[0].id]));
        }

        try {
          const feedbackResponse = await apiClient.getContractFeedback(contractId);
          if (feedbackResponse.success && feedbackResponse.data) {
            const feedbackMap = new Map<string, ReviewFeedback>();
            Object.entries(feedbackResponse.data).forEach(([clauseId, feedback]) => {
              feedbackMap.set(clauseId, feedback);
            });
            setSubmittedFeedback(feedbackMap);
          }
        } catch (feedbackError) {
          console.warn('Failed to load existing feedback:', feedbackError);
          // Don't fail the entire component if feedback loading fails
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load results');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [contractId, onGetResults]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-lg">Loading contract analysis...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <XCircle className="h-6 w-6 text-red-500 mr-3" />
          <div>
            <h3 className="text-lg font-medium text-red-800">Error Loading Results</h3>
            <p className="text-red-600 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-center">
          <Clock className="h-6 w-6 text-yellow-500 mr-3" />
          <div>
            <h3 className="text-lg font-medium text-yellow-800">Processing In Progress</h3>
            <p className="text-yellow-600 mt-1">Contract analysis is still being processed. Results will appear here once completed.</p>
          </div>
        </div>
      </div>
    );
  }

  const { contract, clauses, summary } = results;

  const getClassificationIcon = (classification: string | undefined) => {
    switch (classification?.toLowerCase()) {
      case 'standard':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'non-standard':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'ambiguous':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getClassificationColor = (classification: string | undefined) => {
    switch (classification?.toLowerCase()) {
      case 'standard':
        return 'text-green-700 bg-green-100';
      case 'non-standard':
        return 'text-red-700 bg-red-100';
      case 'ambiguous':
        return 'text-yellow-700 bg-yellow-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const toggleClause = (clauseId: string) => {
    setExpandedClauses(prev => {
      const newSet = new Set(prev);
      if (newSet.has(clauseId)) {
        newSet.delete(clauseId);
      } else {
        newSet.add(clauseId);
      }
      return newSet;
    });
  };

  const toggleClauseText = (clauseId: string) => {
    setExpandedClauseTexts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(clauseId)) {
        newSet.delete(clauseId);
      } else {
        newSet.add(clauseId);
      }
      return newSet;
    });
  };


  const truncateText = (text: string, maxLength: number = 150) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const handleReviewClick = (clause: ClauseResponse) => {
    setSelectedClauseForReview(clause);
    setReviewModalOpen(true);
  };

  const handleSubmitFeedback = async (feedback: ReviewFeedback) => {
    try {
      const result = await apiClient.submitClauseFeedback(feedback);
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to submit feedback');
      }

      // Store the feedback for this clause
      setSubmittedFeedback(prev => new Map(prev.set(feedback.clause_id, feedback)));
      
      setReviewModalOpen(false);
      setSelectedClauseForReview(null);
       
      const toast = document.createElement('div');
      toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center space-x-2';
      toast.innerHTML = `
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
        <span>Feedback submitted successfully!</span>
      `;
      document.body.appendChild(toast);
      
      setTimeout(() => {
        toast.remove();
      }, 3000);
      
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert('Failed to submit feedback: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  return (
    <div className="space-y-6">
      {/* Contract Summary */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <FileText className="h-6 w-6 text-blue-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">Contract Analysis Results</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">Total Clauses</h3>
            <p className="text-2xl font-bold text-blue-900">{summary.total_clauses}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-green-800">Standard Clauses</h3>
            <p className="text-2xl font-bold text-green-900">{summary.standard_clauses}</p>
          </div>
          <div className="bg-red-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-red-800">Non-Standard Clauses</h3>
            <p className="text-2xl font-bold text-red-900">{summary.non_standard_clauses}</p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-yellow-800">Ambiguous Clauses</h3>
            <p className="text-2xl font-bold text-yellow-900">{summary.ambiguous_clauses}</p>
          </div>
        </div>

        <div className="text-sm text-gray-600">
          <p><strong>File:</strong> {contract.original_filename}</p>
          <p><strong>State:</strong> {contract.state}</p>
          <p><strong>Status:</strong> {contract.status}</p>
          {contract.processing_completed_at && (
            <p><strong>Completed:</strong> {new Date(contract.processing_completed_at).toLocaleString()}</p>
          )}
        </div>
      </div>

      {/* Clauses Analysis */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Clause Analysis</h3>
        
        {clauses.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No clauses analyzed yet.</p>
        ) : (
          <div className="space-y-4">
            {clauses.map((clause: ClauseResponse) => {
              const isExpanded = expandedClauses.has(clause.id);
              return (
                <div key={clause.id} className="border border-gray-200 rounded-lg">
                  <div 
                    className="p-4 cursor-pointer hover:bg-gray-50"
                    onClick={() => toggleClause(clause.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 text-gray-400" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-gray-400" />
                        )}
                        {getClassificationIcon(clause.classification)}
                        <span className="font-medium text-gray-900">
                          Clause {clause.clause_number}: {clause.attribute_name}
                        </span>
                        {clause.classification && (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getClassificationColor(clause.classification)}`}>
                            {clause.classification}
                          </span>
                        )}
                        {clause.classification === 'Ambiguous' && (
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleReviewClick(clause);
                              }}
                              className="flex items-center space-x-1 px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 transition-colors"
                            >
                              <Edit3 className="h-3 w-3" />
                              <span>Review</span>
                            </button>
                            {submittedFeedback.has(clause.id) && (
                              <div title="Feedback submitted">
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {clause.confidence_score && (
                          <span className="text-sm text-gray-500">
                            {clause.confidence_score}% confidence
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {isExpanded && (
                    <div className="px-4 pb-4 border-t border-gray-100 mt-3">
                      <div className="text-sm text-gray-700 mb-3">
                        <div 
                          className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-2 rounded"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleClauseText(clause.id);
                          }}
                        >
                          <p className="font-medium">
                            {expandedClauseTexts.has(clause.id) ? 'Clause Text (Click to collapse)' : 'Clause Text (Click to expand)'}
                          </p>
                          {expandedClauseTexts.has(clause.id) ? (
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-gray-400" />
                          )}
                        </div>
                        {!expandedClauseTexts.has(clause.id) && (
                          <p 
                            className="bg-gray-50 p-3 rounded border mt-2 text-gray-600 cursor-pointer hover:bg-gray-100"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleClauseText(clause.id);
                            }}
                          >
                            {clause.clause_text ? truncateText(clause.clause_text) : 'No text found'}
                          </p>
                        )}
                        {expandedClauseTexts.has(clause.id) && (
                          <p className="bg-gray-50 p-3 rounded border mt-2">
                            {clause.clause_text || 'No text found'}
                          </p>
                        )}
                      </div>

                      {clause.template_match_text && (
                        <div className="text-sm text-gray-700 mb-3">
                          <p className="font-medium mb-2">Template Match:</p>
                          <p className="bg-blue-50 p-3 rounded border">
                            {clause.template_match_text}
                          </p>
                        </div>
                      )}

                      {/* Classification Steps */}
                      <div className="text-sm text-gray-700 mb-3">
                        <p className="font-medium mb-2">Classification Steps:</p>
                        {clause.classification_steps ? (
                          <div className="bg-gray-50 p-3 rounded border">
                            {(() => {
                              try {
                                const steps = JSON.parse(clause.classification_steps);
                                return (
                                  <div className="space-y-2">
                                    {steps.map((step: any, index: number) => (
                                      <div key={index} className="flex items-center justify-between text-xs">
                                        <span className="font-medium">{step.step_name}</span>
                                        <div className="flex items-center space-x-2">
                                          <span className={`px-2 py-1 rounded ${step.passed ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            {step.passed ? 'PASS' : 'FAIL'}
                                          </span>
                                          {step.score && <span className="text-gray-500">Score: {step.score}</span>}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                );
                              } catch (e) {
                                return <span className="text-gray-500">Invalid classification steps data</span>;
                              }
                            })()}
                          </div>
                        ) : (
                          <div className="bg-yellow-50 p-3 rounded border text-yellow-700">
                            No classification steps available
                          </div>
                        )}
                      </div>

                      {/* Extraction Method */}
                      <div className="text-xs text-gray-500 mb-2">
                        <span className="font-medium">Extraction Method:</span> {clause.extraction_method || 'spacy_nlp'}
                      </div>

                      <div className="flex items-center justify-between text-xs text-gray-500">
                        {clause.similarity_score && (
                          <span>Similarity: {clause.similarity_score}%</span>
                        )}
                        {clause.match_type && (
                          <span>Match Type: {clause.match_type}</span>
                        )}
                        {clause.template_attribute && (
                          <span>Template Attribute: {clause.template_attribute}</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {selectedClauseForReview && (
        <ReviewModal
          isOpen={reviewModalOpen}
          onClose={() => {
            setReviewModalOpen(false);
            setSelectedClauseForReview(null);
          }}
          clause={selectedClauseForReview}
          onSubmitFeedback={handleSubmitFeedback}
          existingFeedback={submittedFeedback.get(selectedClauseForReview.id)}
        />
      )}
    </div>
  );
}
