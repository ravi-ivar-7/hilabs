'use client';

import { useState, useEffect } from 'react';
import { BarChart3, PieChart, TrendingUp, Shield, AlertCircle, CheckCircle, XCircle, AlertTriangle, FileText } from 'lucide-react';
import { ContractFile } from '../../types/contract';
import { apiClient } from '../../lib/api';
import LoadingSpinner from '../common/LoadingSpinner';

interface CombinedAnalysisProps {
  contracts: ContractFile[];
}

interface AnalysisData {
  totalContracts: number;
  completedContracts: number;
  totalClauses: number;
  standardClauses: number;
  nonStandardClauses: number;
  ambiguousClauses: number;
  stateBreakdown: {
    TN: { contracts: number; clauses: number; standard: number; nonStandard: number; ambiguous: number };
    WA: { contracts: number; clauses: number; standard: number; nonStandard: number; ambiguous: number };
  };
  attributeBreakdown: {
    [key: string]: { standard: number; nonStandard: number; ambiguous: number };
  };
  complianceScore: number;
  riskLevel: 'low' | 'medium' | 'high';
}

export default function CombinedAnalysis({ contracts }: CombinedAnalysisProps) {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const completedContracts = contracts.filter(c => c.status === 'completed');
  const processingContracts = contracts.filter(c => 
    c.status === 'processing' || c.status === 'uploaded' || c.status === 'queued' || 
    c.status === 'preprocessing' || c.status === 'classifying'
  );

  useEffect(() => {
    const fetchCombinedAnalysis = async () => {
      if (completedContracts.length === 0) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const analysisPromises = completedContracts.map(contract => 
          apiClient.getContractResults(contract.id)
        );

        const results = await Promise.all(analysisPromises);
        
        let totalClauses = 0;
        let standardClauses = 0;
        let nonStandardClauses = 0;
        let ambiguousClauses = 0;
        
        const stateBreakdown = {
          TN: { contracts: 0, clauses: 0, standard: 0, nonStandard: 0, ambiguous: 0 },
          WA: { contracts: 0, clauses: 0, standard: 0, nonStandard: 0, ambiguous: 0 }
        };

        const attributeBreakdown: { [key: string]: { standard: number; nonStandard: number; ambiguous: number } } = {};

        results.forEach((result, index) => {
          if (result.success && result.data) {
            const { summary, contract, clauses } = result.data;
            const state = contract.state as 'TN' | 'WA';
            
            totalClauses += summary.total_clauses;
            standardClauses += summary.standard_clauses;
            nonStandardClauses += summary.non_standard_clauses;
            ambiguousClauses += summary.ambiguous_clauses;

            stateBreakdown[state].contracts += 1;
            stateBreakdown[state].clauses += summary.total_clauses;
            stateBreakdown[state].standard += summary.standard_clauses;
            stateBreakdown[state].nonStandard += summary.non_standard_clauses;
            stateBreakdown[state].ambiguous += summary.ambiguous_clauses;

            clauses.forEach((clause: any) => {
              const attr = clause.attribute_name;
              if (!attributeBreakdown[attr]) {
                attributeBreakdown[attr] = { standard: 0, nonStandard: 0, ambiguous: 0 };
              }
              
              if (clause.classification === 'Standard') {
                attributeBreakdown[attr].standard += 1;
              } else if (clause.classification === 'Non-Standard') {
                attributeBreakdown[attr].nonStandard += 1;
              } else if (clause.classification === 'Ambiguous') {
                attributeBreakdown[attr].ambiguous += 1;
              }
            });
          }
        });

        const complianceScore = totalClauses > 0 ? Math.round((standardClauses / totalClauses) * 100) : 0;
        const riskLevel: 'low' | 'medium' | 'high' = 
          complianceScore >= 80 ? 'low' : 
          complianceScore >= 60 ? 'medium' : 'high';

        setAnalysisData({
          totalContracts: completedContracts.length,
          completedContracts: completedContracts.length,
          totalClauses,
          standardClauses,
          nonStandardClauses,
          ambiguousClauses,
          stateBreakdown,
          attributeBreakdown,
          complianceScore,
          riskLevel
        });

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load combined analysis');
      } finally {
        setLoading(false);
      }
    };

    fetchCombinedAnalysis();
  }, [completedContracts.length]);

  if (processingContracts.length > 0) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">

        <h3 className="text-xl font-semibold text-blue-900 mb-2">Analysis in Progress</h3>
        <p className="text-blue-700 mb-4">
          Waiting for {processingContracts.length} contract{processingContracts.length > 1 ? 's' : ''} to complete classification...
        </p>
        <div className="text-sm text-blue-600">
          <p>Completed: {completedContracts.length} / {contracts.length} contracts</p>
        </div>
      </div>
    );
  }

  if (completedContracts.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Available</h3>
        <p className="text-gray-600">Upload and process contracts to see detailed analysis.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8">
        <div className="flex items-center justify-center">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-lg">Loading combined analysis...</span>
        </div>
      </div>
    );
  }

  if (error || !analysisData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <XCircle className="h-6 w-6 text-red-500 mr-3" />
          <div>
            <h3 className="text-lg font-medium text-red-800">Analysis Error</h3>
            <p className="text-red-600 mt-1">{error || 'Failed to load analysis'}</p>
          </div>
        </div>
      </div>
    );
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-700 bg-green-100';
      case 'medium': return 'text-yellow-700 bg-yellow-100';
      case 'high': return 'text-red-700 bg-red-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case 'low': return <Shield className="h-5 w-5 text-green-600" />;
      case 'medium': return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'high': return <AlertCircle className="h-5 w-5 text-red-600" />;
      default: return <Shield className="h-5 w-5 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center mb-6">
          <BarChart3 className="h-6 w-6 text-blue-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">Combined Contract Analysis</h2>
        </div>

        <div className="bg-gray-50 p-6 rounded-lg mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Clause Classification Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {(() => {
              const classifiedTotal = analysisData.standardClauses + analysisData.nonStandardClauses + analysisData.ambiguousClauses;
              return (
                <>
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <PieChart className="h-6 w-6 text-purple-600 mr-2" />
                      <span className="text-sm font-medium text-purple-800">Classified</span>
                    </div>
                    <p className="text-3xl font-bold text-purple-900">{classifiedTotal}</p>
                    <p className="text-xs text-purple-700 mt-1">100%</p>
                  </div>

                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
                      <span className="text-sm font-medium text-green-800">Standard</span>
                    </div>
                    <p className="text-3xl font-bold text-green-900">{analysisData.standardClauses}</p>
                    <p className="text-xs text-green-700 mt-1">
                      {classifiedTotal > 0 ? Math.round((analysisData.standardClauses / classifiedTotal) * 100) : 0}%
                    </p>
                  </div>

                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <XCircle className="h-6 w-6 text-red-600 mr-2" />
                      <span className="text-sm font-medium text-red-800">Non-Standard</span>
                    </div>
                    <p className="text-3xl font-bold text-red-900">{analysisData.nonStandardClauses}</p>
                    <p className="text-xs text-red-700 mt-1">
                      {classifiedTotal > 0 ? Math.round((analysisData.nonStandardClauses / classifiedTotal) * 100) : 0}%
                    </p>
                  </div>

                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <AlertTriangle className="h-6 w-6 text-yellow-600 mr-2" />
                      <span className="text-sm font-medium text-yellow-800">Ambiguous</span>
                    </div>
                    <p className="text-3xl font-bold text-yellow-900">{analysisData.ambiguousClauses}</p>
                    <p className="text-xs text-yellow-700 mt-1">
                      {classifiedTotal > 0 ? Math.round((analysisData.ambiguousClauses / classifiedTotal) * 100) : 0}%
                    </p>
                  </div>
                </>
              );
            })()}
          </div>
       
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-50 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">State Breakdown</h3>
            <div className="space-y-4">
              {Object.entries(analysisData.stateBreakdown).map(([state, data]) => (
                <div key={state} className="bg-white p-4 rounded border">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{state === 'TN' ? 'Tennessee' : 'Washington'}</h4>
                    <span className="text-sm text-gray-500">{data.contracts} contracts</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div className="text-center">
                      <p className="font-medium text-green-600">{data.standard}</p>
                      <p className="text-gray-500">Standard</p>
                    </div>
                    <div className="text-center">
                      <p className="font-medium text-red-600">{data.nonStandard}</p>
                      <p className="text-gray-500">Non-Standard</p>
                    </div>
                    <div className="text-center">
                      <p className="font-medium text-yellow-600">{data.ambiguous}</p>
                      <p className="text-gray-500">Ambiguous</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Attribute Analysis</h3>
            <div className="space-y-3">
              {Object.entries(analysisData.attributeBreakdown).map(([attribute, data]) => {
                const total = data.standard + data.nonStandard + data.ambiguous;
                const standardPct = total > 0 ? Math.round((data.standard / total) * 100) : 0;
                
                return (
                  <div key={attribute} className="bg-white p-3 rounded border">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-900">{attribute}</h4>
                      <span className="text-xs text-gray-500">{total} clauses</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full" 
                          style={{ width: `${standardPct}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-medium text-gray-600">{standardPct}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
