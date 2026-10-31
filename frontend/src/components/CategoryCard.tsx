import React from 'react';
import { CheckCircle2, AlertCircle, HelpCircle, Eye, ChevronRight } from 'lucide-react';
import type { AssessmentCategory, CategoryAssessment, Claim, EvidenceRef, Source } from '../types/api';

interface CategoryCardProps {
  category: AssessmentCategory;
  assessment?: CategoryAssessment;
  claimsMap: Record<string, Claim>;
  sourcesMap: Record<string, Source>;
  onSelectEvidence: (evidence: EvidenceRef, source: Source | null) => void;
}

export const CategoryCard: React.FC<CategoryCardProps> = ({
  category,
  assessment,
  claimsMap,
  sourcesMap,
  onSelectEvidence,
}) => {
  const getStatusBadge = () => {
    if (!assessment) {
      return (
        <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
          Pending Analysis
        </span>
      );
    }
    switch (assessment.status) {
      case 'supported':
        return (
          <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Supported
          </span>
        );
      case 'conflicting':
        return (
          <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 font-medium">
            <AlertCircle className="w-3.5 h-3.5" />
            Conflicting
          </span>
        );
      case 'requires_verification':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-medium">
            <HelpCircle className="w-3.5 h-3.5" />
            Requires Verification
          </span>
        );
    }
  };

  const supportingClaims = (assessment?.supporting_claim_ids || [])
    .map((id) => claimsMap[id])
    .filter(Boolean);

  const contraryClaims = (assessment?.contrary_claim_ids || [])
    .map((id) => claimsMap[id])
    .filter(Boolean);

  return (
    <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-xs space-y-4">
      {/* Category Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-base font-semibold text-slate-900">{category.name}</h4>
          <p className="text-xs text-slate-500 mt-0.5">{category.description}</p>
        </div>
        {getStatusBadge()}
      </div>

      {/* Evaluation Question */}
      <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs">
        <span className="font-semibold text-slate-700">Guiding Question:</span>{' '}
        <span className="text-slate-600 italic">{category.evaluation_question}</span>
      </div>

      {/* Rationale if present */}
      {assessment?.rationale && (
        <p className="text-xs text-slate-600 border-l-2 border-slate-300 pl-2.5">
          {assessment.rationale}
        </p>
      )}

      {/* Supporting Claims */}
      {supportingClaims.length > 0 && (
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
            Supporting Claims ({supportingClaims.length})
          </label>
          <div className="space-y-2">
            {supportingClaims.map((claim) => (
              <div
                key={claim.id}
                className="p-2.5 rounded-lg bg-teal-50/40 border border-teal-100 text-xs space-y-1.5"
              >
                <div className="text-slate-800 font-medium flex items-start gap-1.5">
                  <ChevronRight className="w-3.5 h-3.5 text-teal-600 mt-0.5 flex-shrink-0" />
                  <span>{claim.normalized_statement}</span>
                </div>
                {claim.evidence_refs.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {claim.evidence_refs.map((ref, idx) => {
                      const src = sourcesMap[ref.source_id] || null;
                      return (
                        <button
                          key={`${ref.source_id}-${idx}`}
                          onClick={() => onSelectEvidence(ref, src)}
                          className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-white border border-teal-200 text-teal-700 hover:bg-teal-50 font-medium transition-colors"
                        >
                          <Eye className="w-3 h-3 text-teal-600" />
                          <span>Quote #{idx + 1}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contrary / Conflicting Claims */}
      {contraryClaims.length > 0 && (
        <div className="space-y-2">
          <label className="text-xs font-semibold text-amber-700 uppercase tracking-wider">
            Contradictory / Contrasting Claims ({contraryClaims.length})
          </label>
          <div className="space-y-2">
            {contraryClaims.map((claim) => (
              <div
                key={claim.id}
                className="p-2.5 rounded-lg bg-amber-50/60 border border-amber-200 text-xs space-y-1.5"
              >
                <div className="text-slate-800 font-medium flex items-start gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600 mt-0.5 flex-shrink-0" />
                  <span>{claim.normalized_statement}</span>
                </div>
                {claim.evidence_refs.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {claim.evidence_refs.map((ref, idx) => {
                      const src = sourcesMap[ref.source_id] || null;
                      return (
                        <button
                          key={`${ref.source_id}-${idx}`}
                          onClick={() => onSelectEvidence(ref, src)}
                          className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-white border border-amber-300 text-amber-800 hover:bg-amber-50 font-medium transition-colors"
                        >
                          <Eye className="w-3 h-3 text-amber-600" />
                          <span>Quote #{idx + 1}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unanswered Questions */}
      {assessment?.unanswered_questions && assessment.unanswered_questions.length > 0 && (
        <div className="space-y-1 bg-indigo-50/50 p-2.5 rounded-lg border border-indigo-100 text-xs">
          <div className="font-semibold text-indigo-900">Information Gaps:</div>
          <ul className="list-disc list-inside text-indigo-800 space-y-0.5">
            {assessment.unanswered_questions.map((q, idx) => (
              <li key={idx}>{q}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
