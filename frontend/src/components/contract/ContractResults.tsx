'use client';

import { useState, useEffect } from 'react';
import { FileText, CheckCircle, XCircle, AlertTriangle, Clock, ChevronDown, ChevronRight } from 'lucide-react';
import { ContractResultsResponse, ClauseResponse } from '../../types/contract';
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
  const [expandedTemplateTexts, setExpandedTemplateTexts] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await onGetResults(contractId);
        setResults(data);
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

  const toggleTemplateText = (clauseId: string) => {
    setExpandedTemplateTexts(prev => {
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

  return (
    <div className="space-y-6">
      {/* Contract Summary */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <FileText className="h-6 w-6 text-blue-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">Contract Analysis Results</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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
                      </div>
                      {clause.confidence_score && (
                        <span className="text-sm text-gray-500">
                          {clause.confidence_score}% confidence
                        </span>
                      )}
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
                          <div 
                            className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-2 rounded"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleTemplateText(clause.id);
                            }}
                          >
                            <p className="font-medium">
                              {expandedTemplateTexts.has(clause.id) ? 'Template Match (Click to collapse)' : 'Template Match (Click to expand)'}
                            </p>
                            {expandedTemplateTexts.has(clause.id) ? (
                              <ChevronDown className="h-4 w-4 text-gray-400" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-gray-400" />
                            )}
                          </div>
                          {!expandedTemplateTexts.has(clause.id) && (
                            <p 
                              className="bg-blue-50 p-3 rounded border mt-2 text-gray-600 cursor-pointer hover:bg-blue-100"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleTemplateText(clause.id);
                              }}
                            >
                              {clause.template_match_text ? truncateText(clause.template_match_text) : 'No text found'}
                            </p>
                          )}
                          {expandedTemplateTexts.has(clause.id) && (
                            <p className="bg-blue-50 p-3 rounded border mt-2">
                              {clause.template_match_text || 'No text found'}
                            </p>
                          )}
                        </div>
                      )}

                      <div className="flex items-center justify-between text-xs text-gray-500">
                        {clause.similarity_score && (
                          <span>Similarity: {clause.similarity_score}%</span>
                        )}
                        {clause.match_type && (
                          <span>Match Type: {clause.match_type}</span>
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
    </div>
  );
}
