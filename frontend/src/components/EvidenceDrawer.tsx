import React from 'react';
import { X, ExternalLink, FileText, MapPin, ShieldCheck, AlertCircle } from 'lucide-react';
import type { EvidenceRef, Source } from '../types/api';

interface EvidenceDrawerProps {
  evidence: EvidenceRef | null;
  source: Source | null;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ evidence, source, onClose }) => {
  if (!evidence) return null;

  return (
    <div
      className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-white border-l border-slate-200 shadow-2xl flex flex-col transform transition-transform duration-300 ease-in-out"
      role="dialog"
      aria-labelledby="evidence-drawer-title"
      aria-modal="true"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/70">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-teal-600" />
          <h3 id="evidence-drawer-title" className="text-base font-semibold text-slate-900">
            Source Evidence Provenance
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Close evidence drawer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Exact Quote */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Exact Verbatim Snippet
          </label>
          <blockquote className="p-4 rounded-lg bg-teal-50/60 border-l-4 border-teal-500 text-slate-800 text-sm font-medium leading-relaxed italic">
            "{evidence.exact_snippet}"
          </blockquote>
          <p className="text-xs text-slate-400">
            This snippet was extracted directly from the recorded source text hash.
          </p>
        </div>

        {/* Source Metadata */}
        <div className="space-y-3 bg-slate-50 p-4 rounded-lg border border-slate-100">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Source Provenance
          </label>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-slate-500 font-medium">Source Title:</span>{' '}
              <span className="text-slate-900 font-semibold">{source?.title || evidence.source_id}</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-500 font-medium">Authority:</span>
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-medium">
                {source?.authority === 'primary_official' ? (
                  <>
                    <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                    Official Primary
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                    {source?.authority || 'Third Party'}
                  </>
                )}
              </span>
            </div>

            {source?.publication_date && (
              <div>
                <span className="text-slate-500 font-medium">Published Date:</span>{' '}
                <span className="text-slate-700">{source.publication_date}</span>
                {source.cycle_or_version && (
                  <span className="text-xs text-slate-400 ml-1">({source.cycle_or_version})</span>
                )}
              </div>
            )}

            {source?.content_hash && (
              <div className="text-xs">
                <span className="text-slate-500 font-medium">Content Hash:</span>{' '}
                <code className="text-slate-600 font-mono bg-slate-200/60 px-1 py-0.5 rounded">
                  {source.content_hash.substring(0, 16)}...
                </code>
              </div>
            )}
          </div>
        </div>

        {/* Location within source */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Location in Document
          </label>
          <div className="flex items-center gap-2 text-sm text-slate-700 bg-slate-100/70 p-3 rounded-lg border border-slate-200">
            <MapPin className="w-4 h-4 text-slate-500 flex-shrink-0" />
            <span>
              <span className="capitalize font-medium">{evidence.location_type}:</span> {evidence.location_value}
            </span>
          </div>
        </div>

        {/* External Link */}
        {source?.url && (
          <div className="pt-2">
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 text-sm font-medium transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Open Original Source Document
            </a>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex justify-end">
        <button
          onClick={onClose}
          className="px-4 py-2 rounded-lg bg-slate-800 text-white text-sm font-medium hover:bg-slate-900 transition-colors"
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
};
