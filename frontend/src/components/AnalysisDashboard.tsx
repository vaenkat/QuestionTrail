import React, { useState } from 'react';
import {
  ShieldAlert,
  FileText,
  AlertTriangle,
  FileDown,
  RotateCcw,
  Hash,
  Sparkles,
} from 'lucide-react';
import type {
  AnalysisResult,
  AssessmentCategory,
  Claim,
  EvidenceRef,
  Source,
} from '../types/api';
import { CategoryCard } from './CategoryCard';
import { FindingCard } from './FindingCard';
import { VerificationChecklist } from './VerificationChecklist';
import { api } from '../services/api';

interface AnalysisDashboardProps {
  result: AnalysisResult;
  mode: string;
  categories: AssessmentCategory[];
  onSelectEvidence: (evidence: EvidenceRef, source: Source | null) => void;
  onReset: () => void;
}

export const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({
  result,
  mode,
  categories,
  onSelectEvidence,
  onReset,
}) => {
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [activeTab, setActiveTab] = useState<'categories' | 'findings' | 'checklist'>('categories');

  const sourcesMap = React.useMemo(() => {
    const map: Record<string, Source> = {};
    result.sources.forEach((s) => {
      map[s.id] = s;
    });
    return map;
  }, [result.sources]);

  const claimsMap = React.useMemo(() => {
    const map: Record<string, Claim> = {};
    result.claims.forEach((c) => {
      map[c.id] = c;
    });
    return map;
  }, [result.claims]);

  const assessmentMap = React.useMemo(() => {
    const map: Record<string, (typeof result.assessments)[0]> = {};
    result.assessments.forEach((a) => {
      map[a.category_id] = a;
    });
    return map;
  }, [result.assessments]);

  const handleDownloadReport = async () => {
    try {
      setLoadingReport(true);
      const rep = await api.getReport(result.project_id);
      setReportMarkdown(rep.markdown_report);
    } catch (err) {
      alert(`Could not load report: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoadingReport(false);
    }
  };

  const conflictCount = result.findings.filter((f) => f.type === 'potential_conflict').length;
  const datedCount = result.findings.filter((f) => f.type === 'dated_information').length;
  const gapCount = result.findings.filter((f) => f.type === 'information_gap').length;

  return (
    <div className="space-y-6">
      {/* Top Banner: Mode & Provenance Hash */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                mode === 'precomputed'
                  ? 'bg-blue-100 text-blue-800'
                  : mode === 'live'
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-amber-100 text-amber-800 border border-amber-300'
              }`}
            >
              {mode === 'precomputed'
                ? 'Precomputed Analysis'
                : mode === 'live'
                ? 'Live AI Analysis'
                : 'Mock / Demo Analysis'}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <div className="flex items-center gap-1 text-xs text-slate-500 font-mono">
              <Hash className="w-3.5 h-3.5 text-slate-400" />
              <span>Dataset Hash: {result.dataset_hash.substring(0, 16)}...</span>
            </div>
          </div>
          <p className="text-xs text-slate-500">
            {mode === 'precomputed'
              ? 'Exact dataset hash matched curated baseline. Provenance verified against source content.'
              : mode === 'live'
              ? 'Computed using live LLM extraction with strict verbatim quotation verification.'
              : 'Computed using local mock provider for offline development/testing. No external LLM used.'}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleDownloadReport}
            disabled={loadingReport}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
          >
            <FileDown className="w-4 h-4 text-slate-500" />
            {loadingReport ? 'Loading...' : 'View Markdown Report'}
          </button>
          <button
            onClick={onReset}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
            New Research Run
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Curated Sources</span>
            <FileText className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{result.sources.length}</div>
          <div className="text-[11px] text-slate-400">All content hashes verified</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Evidence-linked Claims</span>
            <Sparkles className="w-4 h-4 text-teal-500" />
          </div>
          <div className="text-2xl font-bold text-teal-700">{result.claims.length}</div>
          <div className="text-[11px] text-slate-400">Claims supported by traceable source excerpts.</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Epistemic Signals</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{result.findings.length}</div>
          <div className="text-[11px] text-amber-600 font-medium">
            {conflictCount === 1 ? '1 potential date discrepancy' : `${conflictCount} potential date discrepancies`} · {datedCount} dated · {gapCount} gap
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Verification Checklist</span>
            <ShieldAlert className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-indigo-700">{result.actions.length}</div>
          <div className="text-[11px] text-slate-400">Prioritized for action</div>
        </div>
      </div>

      {/* Executive Summary */}
      {result.summary && (
        <div className="bg-teal-50/50 border border-teal-200/60 rounded-xl p-4 text-sm text-slate-800 leading-relaxed space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-xs font-bold uppercase tracking-wider text-teal-900">
              Executive Synthesis
            </div>
            <div className="text-[11px] text-slate-600 italic bg-white/80 px-2.5 py-0.5 rounded-md border border-teal-200/60">
              Historical application-cycle review — the listed 2026 application dates have passed as of November 1, 2026.
            </div>
          </div>
          <p>{result.summary}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-6 text-sm">
        <button
          onClick={() => setActiveTab('categories')}
          className={`pb-3 font-semibold transition-colors border-b-2 -mb-px ${
            activeTab === 'categories'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Category Evidence ({categories.length})
        </button>
        <button
          onClick={() => setActiveTab('findings')}
          className={`pb-3 font-semibold transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
            activeTab === 'findings'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Findings & Signals
          <span className="text-xs px-2 py-0.2 rounded-full bg-amber-100 text-amber-800">
            {result.findings.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab('checklist')}
          className={`pb-3 font-semibold transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
            activeTab === 'checklist'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Verification Checklist
          <span className="text-xs px-2 py-0.2 rounded-full bg-teal-100 text-teal-800">
            {result.actions.length}
          </span>
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'categories' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {categories.map((cat) => (
            <CategoryCard
              key={cat.id}
              category={cat}
              assessment={assessmentMap[cat.id]}
              claimsMap={claimsMap}
              sourcesMap={sourcesMap}
              onSelectEvidence={onSelectEvidence}
            />
          ))}
        </div>
      )}

      {activeTab === 'findings' && (
        <div className="space-y-4">
          <div className="text-xs text-slate-500">
            Epistemic signals separate potential hypotheses from verified facts. Click any citation to inspect the source quote.
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.findings.map((f) => (
              <FindingCard
                key={f.id}
                finding={f}
                sourcesMap={sourcesMap}
                onSelectEvidence={onSelectEvidence}
              />
            ))}
          </div>
        </div>
      )}

      {activeTab === 'checklist' && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <VerificationChecklist actions={result.actions} />
        </div>
      )}

      {/* Report Modal */}
      {reportMarkdown && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Generated Research Report</h3>
              <button
                onClick={() => setReportMarkdown(null)}
                className="text-xs text-slate-400 hover:text-slate-700 font-semibold"
              >
                Close
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1 font-mono text-xs bg-slate-50 text-slate-800 whitespace-pre-wrap leading-relaxed">
              {reportMarkdown}
            </div>
            <div className="px-6 py-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(reportMarkdown);
                  alert('Markdown report copied to clipboard!');
                }}
                className="px-4 py-2 bg-teal-600 text-white rounded-lg text-xs font-semibold hover:bg-teal-700"
              >
                Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
