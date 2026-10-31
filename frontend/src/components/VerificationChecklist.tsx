import React, { useState } from 'react';
import { CheckSquare, Square, ExternalLink, ShieldAlert } from 'lucide-react';
import type { VerificationAction } from '../types/api';

interface VerificationChecklistProps {
  actions: VerificationAction[];
}

export const VerificationChecklist: React.FC<VerificationChecklistProps> = ({ actions }) => {
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());

  const toggleComplete = (id: string) => {
    setCompletedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const getPriorityBadge = (score: number) => {
    if (score >= 0.9) {
      return (
        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800">
          Critical ({score.toFixed(2)})
        </span>
      );
    }
    if (score >= 0.75) {
      return (
        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
          High ({score.toFixed(2)})
        </span>
      );
    }
    return (
      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
        Medium ({score.toFixed(2)})
      </span>
    );
  };

  if (!actions || actions.length === 0) {
    return (
      <div className="p-6 text-center text-slate-400 border border-dashed border-slate-200 rounded-xl">
        No verification actions generated yet. Run analysis to produce a prioritized checklist.
      </div>
    );
  }

  const completedCount = completedIds.size;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-teal-600" />
            Prioritized Verification Checklist
          </h4>
          <p className="text-xs text-slate-500">
            Action items scored deterministically to resolve uncertainty and verify official claims.
          </p>
        </div>
        <div className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md">
          {completedCount} of {actions.length} resolved
        </div>
      </div>

      <div className="space-y-3">
        {actions.map((act, index) => {
          const isDone = completedIds.has(act.id);
          return (
            <div
              key={act.id}
              className={`p-4 rounded-xl border transition-all ${
                isDone
                  ? 'border-slate-200 bg-slate-50/60 opacity-60'
                  : 'border-slate-200 bg-white hover:border-slate-300 shadow-xs'
              }`}
            >
              <div className="flex items-start gap-3">
                <button
                  onClick={() => toggleComplete(act.id)}
                  className="mt-0.5 text-slate-400 hover:text-teal-600 transition-colors"
                  aria-label={isDone ? 'Mark as incomplete' : 'Mark as complete'}
                >
                  {isDone ? (
                    <CheckSquare className="w-5 h-5 text-teal-600" />
                  ) : (
                    <Square className="w-5 h-5" />
                  )}
                </button>

                <div className="flex-1 space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-slate-400">#{index + 1}</span>
                    {getPriorityBadge(act.priority_score)}
                  </div>

                  <p
                    className={`text-sm font-semibold ${
                      isDone ? 'line-through text-slate-500' : 'text-slate-900'
                    }`}
                  >
                    {act.action}
                  </p>

                  <p className="text-xs text-slate-600 leading-relaxed">
                    <span className="font-semibold text-slate-500">Rationale:</span> {act.rationale}
                  </p>

                  {act.recommended_source && (
                    <div className="pt-1">
                      {act.recommended_source.startsWith('http') ? (
                        <a
                          href={act.recommended_source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-teal-700 hover:text-teal-800 font-medium"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Verify at: {act.recommended_source}</span>
                        </a>
                      ) : (
                        <span className="text-xs text-slate-500">
                          <span className="font-medium text-slate-600">Recommended Authority:</span>{' '}
                          {act.recommended_source}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
