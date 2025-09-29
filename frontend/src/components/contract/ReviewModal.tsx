'use client';

import { useState } from 'react';
import { X, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { ClauseResponse } from '../../types/contract';
import { ReviewFeedback } from '../../types/review';

interface ReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  clause: ClauseResponse;
  onSubmitFeedback: (feedback: ReviewFeedback) => Promise<void>;
  existingFeedback?: ReviewFeedback;
}

const classificationOptions = [
  { value: 'Standard', label: 'Standard', icon: CheckCircle, color: 'text-green-600' },
  { value: 'Non-Standard', label: 'Non-Standard', icon: XCircle, color: 'text-red-600' },
  { value: 'Ambiguous', label: 'Still Ambiguous', icon: AlertTriangle, color: 'text-yellow-600' }
];

export default function ReviewModal({ isOpen, onClose, clause, onSubmitFeedback, existingFeedback }: ReviewModalProps) {
  const [selectedClassification, setSelectedClassification] = useState<'Standard' | 'Non-Standard' | 'Ambiguous'>(
    existingFeedback?.user_classification || 'Standard'
  );
  const [comments, setComments] = useState(existingFeedback?.user_comments || '');
  const [confidence, setConfidence] = useState(existingFeedback?.confidence_rating || 3);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const feedback: ReviewFeedback = {
        clause_id: clause.id,
        original_classification: clause.classification || 'Ambiguous',
        user_classification: selectedClassification,
        user_comments: comments.trim() || undefined,
        confidence_rating: confidence
      };

      await onSubmitFeedback(feedback);
      onClose();
      
      setSelectedClassification('Standard');
      setComments('');
      setConfidence(3);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-gray-300 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-6 w-6 text-yellow-500" />
            <h2 className="text-xl font-semibold text-gray-900">Review Ambiguous Clause</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Clause Information */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-2">
              Clause {clause.clause_number}: {clause.attribute_name}
            </h3>
            <div className="text-sm text-gray-600 mb-3">
              <span className="font-medium">Current Classification:</span> 
              <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs">
                {clause.classification}
              </span>
              {clause.confidence_score && (
                <span className="ml-2 text-gray-500">
                  ({clause.confidence_score}% confidence)
                </span>
              )}
            </div>
            <div className="bg-white p-3 rounded border">
              <p className="text-sm text-gray-700">
                {clause.clause_text || 'No clause text available'}
              </p>
            </div>
            {clause.template_match_text && (
              <div className="mt-3">
                <p className="text-sm font-medium text-gray-700 mb-1">Template Match:</p>
                <div className="bg-blue-50 p-3 rounded border">
                  <p className="text-sm text-gray-700">{clause.template_match_text}</p>
                </div>
              </div>
            )}
          </div>

          {/* Classification Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              What should this clause be classified as?
            </label>
            <div className="space-y-2">
              {classificationOptions.map((option) => {
                const IconComponent = option.icon;
                return (
                  <label
                    key={option.value}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedClassification === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="classification"
                      value={option.value}
                      checked={selectedClassification === option.value}
                      onChange={(e) => setSelectedClassification(e.target.value as any)}
                      className="sr-only"
                    />
                    <IconComponent className={`h-5 w-5 ${option.color} mr-3`} />
                    <span className="font-medium text-gray-900">{option.label}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Confidence Rating */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              How confident are you in this classification? (1 = Not confident, 5 = Very confident)
            </label>
            <div className="flex items-center space-x-2">
              {[1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  type="button"
                  onClick={() => setConfidence(rating)}
                  className={`w-10 h-10 rounded-full border-2 font-medium transition-colors ${
                    confidence >= rating
                      ? 'border-blue-500 bg-blue-500 text-white'
                      : 'border-gray-300 text-gray-500 hover:border-gray-400'
                  }`}
                >
                  {rating}
                </button>
              ))}
            </div>
          </div>

          {/* Comments */}
          <div>
            <label htmlFor="comments" className="block text-sm font-medium text-gray-700 mb-2">
              Additional Comments (Optional)
            </label>
            <textarea
              id="comments"
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Explain your reasoning or provide additional context..."
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Review'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
