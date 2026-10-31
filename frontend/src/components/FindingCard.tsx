import React from 'react';
import { AlertTriangle, Clock, HelpCircle, FileCheck, Eye } from 'lucide-react';
import type { Finding, EvidenceRef, Source } from '../types/api';

interface FindingCardProps {
  finding: Finding;
  sourcesMap: Record<string, Source>;
  onSelectEvidence: (evidence: EvidenceRef, source: Source | null) => void;
}

export const FindingCard: React.FC<FindingCardProps> = ({ finding, sourcesMap, onSelectEvidence }) => {
  const getFindingIcon = () => {
    switch (finding.type) {
      case 'potential_conflict':
        return <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />;
      case 'dated_information':
        return <Clock className="w-5 h-5 text-orange-600 flex-shrink-0" />;
      case 'information_gap':
        return <HelpCircle className="w-5 h-5 text-indigo-600 flex-shrink-0" />;
      default:
        return <FileCheck className="w-5 h-5 text-teal-600 flex-shrink-0" />;
    }
  };

  const getBorderColor = () => {
    switch (finding.type) {
      case 'potential_conflict':
        return 'border-amber-200 bg-amber-50/40';
      case 'dated_information':
        return 'border-orange-200 bg-orange-50/40';
      case 'information_gap':
        return 'border-indigo-200 bg-indigo-50/40';
      default:
        return 'border-slate-200 bg-white';
    }
  };

  return (
    <div className={`p-4 rounded-xl border ${getBorderColor()} shadow-xs space-y-3`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          {getFindingIcon()}
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              {finding.type.replace('_', ' ')}
            </span>
            <div className="flex items-center gap-2 mt-0.5">
              <span
                className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                  finding.label === 'potential'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {finding.label === 'potential' ? 'Potential finding' : 'Confirmed'}
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium capitalize">
                Severity: {finding.severity}
              </span>
            </div>
          </div>
        </div>
      </div>

      <p className="text-sm text-slate-800 font-medium leading-relaxed">
        {finding.rationale}
      </p>

      {/* Scope examined for information gaps */}
      {finding.scope_examined && (
        <div className="text-xs text-slate-500 bg-slate-100/60 px-3 py-1.5 rounded-md">
          <span className="font-semibold text-slate-600">Scope Examined:</span> {finding.scope_examined}
        </div>
      )}

      {/* Evidence references */}
      {finding.evidence_refs && finding.evidence_refs.length > 0 && (
        <div className="pt-2 border-t border-slate-200/60 space-y-2">
          <div className="text-xs font-semibold text-slate-500">Supporting Citations:</div>
          <div className="flex flex-wrap gap-2">
            {finding.evidence_refs.map((ref, idx) => {
              const src = sourcesMap[ref.source_id] || null;
              return (
                <button
                  key={`${ref.source_id}-${idx}`}
                  onClick={() => onSelectEvidence(ref, src)}
                  className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-md bg-white border border-slate-300 hover:border-teal-500 hover:text-teal-700 text-slate-700 transition-colors shadow-2xs"
                >
                  <Eye className="w-3.5 h-3.5 text-teal-600" />
                  <span>
                    Quote #{idx + 1} ({src?.title ? src.title.substring(0, 20) + '...' : ref.source_id})
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
