import React, { useState } from 'react';
import {
  Sparkles,
  Database,
  Play,
  Plus,
  Trash2,
  CheckCircle,
  FileText,
  Globe,
  Upload,
  FileCode,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react';
import type { AssessmentCategory, Source } from '../types/api';

const DEFAULT_SCHOLARSHIP_OBJECTIVE =
  'Assess whether the available sources provide consistent and sufficiently current information about the Reliance Foundation Undergraduate Scholarship 2026–27. Identify outdated information, conflicting claims, unanswered questions and what should be verified using official sources.';

interface ProjectSetupProps {
  objective: string;
  setObjective: (val: string) => void;
  categories: AssessmentCategory[];
  setCategories: React.Dispatch<React.SetStateAction<AssessmentCategory[]>>;
  sources: Source[];
  onProposeCategories: () => Promise<void>;
  onLoadCuratedDemo: () => Promise<void>;
  onIngestUrl: (url: string) => Promise<void>;
  onIngestPdf: (file: File) => Promise<void>;
  onIngestText: (title: string, content: string, url?: string, pubDate?: string) => Promise<void>;
  onRunAnalysis: () => Promise<void>;
  isProposing: boolean;
  isLoadingDemo: boolean;
  isIngestingUrl: boolean;
  isIngestingPdf: boolean;
  isAnalyzing: boolean;
}

export const ProjectSetup: React.FC<ProjectSetupProps> = ({
  objective,
  setObjective,
  categories,
  setCategories,
  sources,
  onProposeCategories,
  onLoadCuratedDemo,
  onIngestUrl,
  onIngestPdf,
  onIngestText,
  onRunAnalysis,
  isProposing,
  isLoadingDemo,
  isIngestingUrl,
  isIngestingPdf,
  isAnalyzing,
}) => {
  const [newCatName, setNewCatName] = useState('');
  const [newCatQuestion, setNewCatQuestion] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  // Ingestion form states
  const [ingestTab, setIngestTab] = useState<'demo' | 'url' | 'pdf' | 'text'>('demo');
  const [inputUrl, setInputUrl] = useState('');
  const [textTitle, setTextTitle] = useState('');
  const [textContent, setTextContent] = useState('');
  const [textPubDate, setTextPubDate] = useState('');
  const [isSubmittingText, setIsSubmittingText] = useState(false);

  const toggleCategory = (id: string) => {
    setCategories((prev) =>
      prev.map((c) => (c.id === id ? { ...c, enabled: !c.enabled } : c))
    );
  };

  const removeCategory = (id: string) => {
    setCategories((prev) => prev.filter((c) => c.id !== id));
  };

  const handleAddCategory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCatName.trim() || !newCatQuestion.trim()) return;
    const slug = newCatName.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    const newCat: AssessmentCategory = {
      id: `cat-${slug}-${Date.now().toString().slice(-4)}`,
      name: newCatName.trim(),
      description: 'Custom evaluation category.',
      evaluation_question: newCatQuestion.trim(),
      enabled: true,
      is_ai_suggested: false,
    };
    setCategories((prev) => [...prev, newCat]);
    setNewCatName('');
    setNewCatQuestion('');
    setShowAddForm(false);
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputUrl.trim()) return;
    await onIngestUrl(inputUrl.trim());
    setInputUrl('');
  };

  const handlePdfFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await onIngestPdf(file);
    e.target.value = '';
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textTitle.trim() || !textContent.trim()) return;
    try {
      setIsSubmittingText(true);
      await onIngestText(textTitle.trim(), textContent.trim(), undefined, textPubDate.trim() || undefined);
      setTextTitle('');
      setTextContent('');
      setTextPubDate('');
    } finally {
      setIsSubmittingText(false);
    }
  };

  const enabledCount = categories.filter((c) => c.enabled).length;
  const canAnalyze = objective.trim().length > 3 && sources.length > 0 && enabledCount > 0;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
      {/* Step 1: Research Objective */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor="objective-input" className="text-sm font-bold text-slate-900">
            1. Research Objective
          </label>
          <button
            type="button"
            onClick={() => setObjective(DEFAULT_SCHOLARSHIP_OBJECTIVE)}
            className="text-xs text-teal-700 hover:text-teal-800 font-semibold underline underline-offset-2"
          >
            Fill Demo Scholarship Objective
          </button>
        </div>
        <textarea
          id="objective-input"
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          rows={3}
          placeholder="Enter a free-text research objective (e.g. Assess eligibility, deadlines, and renewal policies for...)"
          className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-sm text-slate-800 placeholder-slate-400 resize-y"
        />
        <div className="flex items-center justify-between pt-1">
          <p className="text-xs text-slate-500">
            Any domain is supported. Domain logic is strictly domain-agnostic.
          </p>
          <button
            type="button"
            onClick={onProposeCategories}
            disabled={isProposing || objective.trim().length < 3}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 border border-teal-200 text-xs font-semibold disabled:opacity-50 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {isProposing ? 'Proposing...' : 'Generate Categories'}
          </button>
        </div>
      </div>

      {/* Step 2: Assessment Categories */}
      <div className="space-y-3 pt-2 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <div>
            <label className="text-sm font-bold text-slate-900">
              2. Evaluation Categories ({enabledCount} active)
            </label>
            <p className="text-xs text-slate-500">
              Categories guide claim extraction and highlight information gaps.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowAddForm(!showAddForm)}
            className="inline-flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900 font-medium"
          >
            <Plus className="w-3.5 h-3.5" />
            {showAddForm ? 'Cancel' : 'Add Category'}
          </button>
        </div>

        {showAddForm && (
          <form onSubmit={handleAddCategory} className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
            <input
              type="text"
              placeholder="Category Name (e.g. Application Fees)"
              value={newCatName}
              onChange={(e) => setNewCatName(e.target.value)}
              className="w-full px-3 py-1.5 rounded-md border border-slate-300 text-xs"
            />
            <input
              type="text"
              placeholder="Evaluation Question (e.g. Is there any fee required to apply?)"
              value={newCatQuestion}
              onChange={(e) => setNewCatQuestion(e.target.value)}
              className="w-full px-3 py-1.5 rounded-md border border-slate-300 text-xs"
            />
            <button
              type="submit"
              className="px-3 py-1 bg-teal-600 text-white rounded-md text-xs font-medium hover:bg-teal-700"
            >
              Save Category
            </button>
          </form>
        )}

        {categories.length === 0 ? (
          <div className="text-xs text-slate-400 p-4 text-center border border-dashed border-slate-200 rounded-xl">
            No categories defined. Click "Generate Categories" above to automatically propose criteria.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {categories.map((cat) => (
              <div
                key={cat.id}
                className={`p-3 rounded-xl border transition-all text-xs flex items-start justify-between gap-2 ${
                  cat.enabled
                    ? 'border-slate-300 bg-white shadow-2xs'
                    : 'border-slate-200 bg-slate-50/70 opacity-60'
                }`}
              >
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id={`chk-${cat.id}`}
                      checked={cat.enabled}
                      onChange={() => toggleCategory(cat.id)}
                      className="rounded text-teal-600 focus:ring-teal-500 w-3.5 h-3.5"
                    />
                    <label htmlFor={`chk-${cat.id}`} className="font-semibold text-slate-800 cursor-pointer">
                      {cat.name}
                    </label>
                  </div>
                  <p className="text-slate-500 italic pl-5">{cat.evaluation_question}</p>
                </div>
                <button
                  onClick={() => removeCategory(cat.id)}
                  className="text-slate-300 hover:text-rose-500 p-1"
                  title="Remove category"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Step 3: Sources & Ingestion */}
      <div className="space-y-4 pt-2 border-t border-slate-100">
        <div>
          <label className="text-sm font-bold text-slate-900">
            3. Source Corpus & Ingestion ({sources.length} sources loaded)
          </label>
          <p className="text-xs text-slate-500">
            Ingest live public URLs (with SSRF protection), upload PDFs with page provenance, or load the curated scholarship corpus.
          </p>
        </div>

        {/* Ingestion mode selector */}
        <div className="flex items-center gap-2 border-b border-slate-200 pb-2 text-xs">
          <button
            type="button"
            onClick={() => setIngestTab('demo')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 ${
              ingestTab === 'demo' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            Curated Demo
          </button>
          <button
            type="button"
            onClick={() => setIngestTab('url')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 ${
              ingestTab === 'url' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            Live URL
          </button>
          <button
            type="button"
            onClick={() => setIngestTab('pdf')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 ${
              ingestTab === 'pdf' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            Upload PDF
          </button>
          <button
            type="button"
            onClick={() => setIngestTab('text')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 ${
              ingestTab === 'text' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <FileCode className="w-3.5 h-3.5" />
            Paste Text
          </button>
        </div>

        {/* Panel: Curated Demo */}
        {ingestTab === 'demo' && (
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-4">
            <div className="space-y-1 text-xs">
              <span className="font-semibold text-slate-800">Reliance Foundation Scholarship 2026–27 Corpus</span>
              <p className="text-slate-500">
                Loads 5 reviewed sources: official release, application portal, 2024–25 archive FAQ (stale date), Buddy4Study, and Unstop.
              </p>
            </div>
            <button
              type="button"
              onClick={onLoadCuratedDemo}
              disabled={isLoadingDemo}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 text-white hover:bg-slate-800 text-xs font-semibold transition-colors disabled:opacity-50 flex-shrink-0"
            >
              <Database className="w-3.5 h-3.5" />
              {isLoadingDemo ? 'Loading...' : 'Load Curated Demo Corpus'}
            </button>
          </div>
        )}

        {/* Panel: Live URL */}
        {ingestTab === 'url' && (
          <form onSubmit={handleUrlSubmit} className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
            <div className="text-xs text-slate-600">
              Enter any public HTTP/HTTPS URL. Safe SSRF protection blocks local and internal IP ranges.
            </div>
            <div className="flex gap-2">
              <input
                type="url"
                required
                placeholder="https://example.com/research-article"
                value={inputUrl}
                onChange={(e) => setInputUrl(e.target.value)}
                className="flex-1 px-3.5 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
              />
              <button
                type="submit"
                disabled={isIngestingUrl || !inputUrl.trim()}
                className="px-4 py-2 bg-teal-600 text-white rounded-lg text-xs font-semibold hover:bg-teal-700 transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                <Globe className="w-3.5 h-3.5" />
                {isIngestingUrl ? 'Fetching & Extracting...' : 'Ingest URL'}
              </button>
            </div>
          </form>
        )}

        {/* Panel: Upload PDF */}
        {ingestTab === 'pdf' && (
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
            <div className="text-xs text-slate-600">
              Upload any PDF document (up to 10MB). Text is extracted with page-level provenance.
            </div>
            <label className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-slate-300 rounded-xl hover:border-teal-500 cursor-pointer bg-white transition-colors">
              <Upload className="w-6 h-6 text-slate-400 mb-1" />
              <span className="text-xs font-semibold text-slate-700">
                {isIngestingPdf ? 'Extracting PDF text...' : 'Click to select PDF document'}
              </span>
              <span className="text-[11px] text-slate-400">PDF documents only</span>
              <input
                type="file"
                accept="application/pdf,.pdf"
                disabled={isIngestingPdf}
                onChange={handlePdfFileChange}
                className="hidden"
              />
            </label>
          </div>
        )}

        {/* Panel: Paste Text */}
        {ingestTab === 'text' && (
          <form onSubmit={handleTextSubmit} className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5">
            <div className="text-xs text-slate-600">
              Paste custom text or research notes directly into the source corpus.
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <input
                type="text"
                required
                placeholder="Source Title (e.g. Internal Whitepaper 2026)"
                value={textTitle}
                onChange={(e) => setTextTitle(e.target.value)}
                className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs"
              />
              <input
                type="text"
                placeholder="Publication Date (Optional, e.g. 2026-05-15)"
                value={textPubDate}
                onChange={(e) => setTextPubDate(e.target.value)}
                className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs"
              />
            </div>
            <textarea
              required
              rows={3}
              placeholder="Paste substantive article or document text here..."
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isSubmittingText || !textTitle.trim() || !textContent.trim()}
                className="px-4 py-1.5 bg-teal-600 text-white rounded-lg text-xs font-semibold hover:bg-teal-700 disabled:opacity-50"
              >
                {isSubmittingText ? 'Adding...' : 'Add Text Source'}
              </button>
            </div>
          </form>
        )}

        {/* Source cards list */}
        {sources.length > 0 && (
          <div className="space-y-2 pt-2">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Ingested Sources ({sources.length})
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {sources.map((s) => (
                <div
                  key={s.id}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-semibold text-slate-800 line-clamp-1 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-teal-600 flex-shrink-0" />
                      <span>{s.title}</span>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-medium capitalize flex-shrink-0">
                      {s.type}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500">
                    <span className="inline-flex items-center gap-1">
                      {s.authority === 'primary_official' ? (
                        <ShieldCheck className="w-3 h-3 text-teal-600" />
                      ) : (
                        <AlertCircle className="w-3 h-3 text-slate-400" />
                      )}
                      {s.authority.replace('_', ' ')}
                    </span>
                    {s.publication_date && <span>• Date: {s.publication_date}</span>}
                    {s.content_hash && (
                      <span>• Hash: <code className="font-mono">{s.content_hash.substring(0, 8)}</code></span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Action CTA */}
      <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <CheckCircle className={`w-4 h-4 ${canAnalyze ? 'text-teal-600' : 'text-slate-300'}`} />
          <span>
            {canAnalyze
              ? 'Ready to run analysis across loaded sources and categories.'
              : 'Add an objective, enable categories, and load sources to run.'}
          </span>
        </div>

        <button
          type="button"
          onClick={onRunAnalysis}
          disabled={!canAnalyze || isAnalyzing}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-teal-600 text-white hover:bg-teal-700 font-semibold text-sm shadow-sm hover:shadow transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Play className="w-4 h-4 fill-white" />
          {isAnalyzing ? 'Analyzing Sources...' : 'Execute Analysis'}
        </button>
      </div>
    </div>
  );
};
