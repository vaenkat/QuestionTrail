import React, { useState } from 'react';
import { Compass, ShieldCheck, AlertCircle } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { ProjectSetup } from './ProjectSetup';
import { AnalysisDashboard } from './AnalysisDashboard';
import { EvidenceDrawer } from './EvidenceDrawer';
import { api } from '../services/api';
import type {
  AssessmentCategory,
  Source,
  AnalysisResult,
  EvidenceRef,
} from '../types/api';

export const WorkspaceShell: React.FC = () => {
  const [objective, setObjective] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [categories, setCategories] = useState<AssessmentCategory[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analysisMode, setAnalysisMode] = useState<string>('precomputed');

  // Loading states
  const [isProposing, setIsProposing] = useState(false);
  const [isLoadingDemo, setIsLoadingDemo] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Evidence Drawer state
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceRef | null>(null);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);

  const handleOpenEvidence = (evidence: EvidenceRef, source: Source | null) => {
    setSelectedEvidence(evidence);
    setSelectedSource(source);
  };

  const handleCloseEvidence = () => {
    setSelectedEvidence(null);
    setSelectedSource(null);
  };

  // 1. Propose Categories from objective
  const handleProposeCategories = async () => {
    if (!objective.trim()) return;
    try {
      setIsProposing(true);
      setErrorMessage(null);
      const proposed = await api.proposeCategories(objective);
      setCategories(proposed);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setIsProposing(false);
    }
  };

  // 2. Load Curated Demo
  const handleLoadCuratedDemo = async () => {
    try {
      setIsLoadingDemo(true);
      setErrorMessage(null);

      // Create project if not exists
      let currentId = projectId;
      if (!currentId) {
        const created = await api.createProject(objective || 'Reliance Foundation Scholarship 2026-27', categories);
        currentId = created.id;
        setProjectId(currentId);
      }

      const res = await api.loadCuratedDemo(currentId);
      setObjective(res.project.objective);
      setCategories(res.project.categories);
      setSources(res.sources);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoadingDemo(false);
    }
  };

  // 3. Run Analysis
  const handleRunAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      setErrorMessage(null);

      let currentId = projectId;
      if (!currentId) {
        const created = await api.createProject(objective, categories);
        currentId = created.id;
        setProjectId(currentId);
      }

      const resp = await api.analyzeProject(currentId);
      setAnalysisResult(resp.result);
      setAnalysisMode(resp.mode);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Reset to create another run
  const handleReset = () => {
    setAnalysisResult(null);
    setProjectId(null);
    setSources([]);
    setSelectedEvidence(null);
    setSelectedSource(null);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-[#CBD5E1] px-6 py-4 flex items-center justify-between sticky top-0 z-30 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#0F766E] flex items-center justify-center text-white">
            <Compass className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-[20px] font-semibold leading-[1.2] text-[#0F172A] m-0">
              QuestionTrail
            </h1>
            <p className="text-[14px] text-[#475569] leading-[1.4] m-0">
              Evidence-first research workspace
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {analysisResult ? (
            <StatusBadge
              status={analysisMode === 'precomputed' ? 'precomputed' : 'supported'}
              label={analysisMode === 'precomputed' ? 'Curated baseline' : 'Analyzed'}
            />
          ) : (
            <StatusBadge status="precomputed" label="Curated baseline mode" />
          )}
          <div className="flex items-center gap-1.5 text-[14px] text-[#475569] bg-slate-100 px-3 py-1.5 rounded-md border border-[#CBD5E1]">
            <ShieldCheck className="w-4 h-4 text-[#0F766E]" aria-hidden="true" />
            <span>Provenance Safe</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        {/* Error Notification */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold">Action Failed:</span> {errorMessage}
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-xs font-semibold text-rose-700 hover:text-rose-900"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* View switching: Setup vs Active Analysis Dashboard */}
        {!analysisResult ? (
          <div className="space-y-6">
            <div className="space-y-1">
              <h2 className="text-2xl font-bold text-slate-900">
                Setup Research Investigation
              </h2>
              <p className="text-sm text-slate-500">
                Define your research objective, review evaluation categories, and load source evidence.
              </p>
            </div>

            <ProjectSetup
              objective={objective}
              setObjective={setObjective}
              categories={categories}
              setCategories={setCategories}
              sources={sources}
              onProposeCategories={handleProposeCategories}
              onLoadCuratedDemo={handleLoadCuratedDemo}
              onRunAnalysis={handleRunAnalysis}
              isProposing={isProposing}
              isLoadingDemo={isLoadingDemo}
              isAnalyzing={isAnalyzing}
            />
          </div>
        ) : (
          <AnalysisDashboard
            result={analysisResult}
            mode={analysisMode}
            categories={categories}
            onSelectEvidence={handleOpenEvidence}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Slide-out Evidence Drawer */}
      {selectedEvidence && (
        <EvidenceDrawer
          evidence={selectedEvidence}
          source={selectedSource}
          onClose={handleCloseEvidence}
        />
      )}
    </div>
  );
};
