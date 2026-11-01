import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import App from "./App"
import { EvidenceDrawer } from "./components/EvidenceDrawer"
import type { EvidenceRef, Source } from "./types/api"

describe("WorkspaceShell foundation and Phase 2 workflow", () => {
  it("renders workspace branding and setup controls", () => {
    render(<App />)
    
    // Top header branding
    expect(screen.getByText("QuestionTrail")).toBeInTheDocument()
    expect(screen.getByText("Evidence-first research workspace")).toBeInTheDocument()
    expect(screen.getByText("Curated baseline mode")).toBeInTheDocument()
    expect(screen.getByText("Evidence Traceability Active")).toBeInTheDocument()
    
    // Objective input
    expect(screen.getByText("1. Research Objective")).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Enter a free-text research objective/i)).toBeInTheDocument()
    
    // Buttons
    expect(screen.getByRole("button", { name: /generate categories/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /load curated demo corpus/i })).toBeInTheDocument()
    
    // Analysis CTA is disabled until ready
    const analyzeBtn = screen.getByRole("button", { name: /execute analysis/i })
    expect(analyzeBtn).toBeInTheDocument()
    expect(analyzeBtn).toBeDisabled()
  })

  it("renders evidence drawer with exact quote and provenance metadata", () => {
    const mockEvidence: EvidenceRef = {
      source_id: "src-rf-portal-2627",
      exact_snippet: "All online applications must be completed and submitted by October 6, 2026 at 11:59 PM IST.",
      location_type: "section",
      location_value: "Important Dates",
    }
    const mockSource: Source = {
      id: "src-rf-portal-2627",
      title: "Reliance Foundation Undergraduate Scholarship Application Portal",
      url: "https://scholarships.reliancefoundation.org/UG_Scholarship.aspx",
      type: "webpage",
      authority: "primary_official",
      publication_date: "2026-08-14",
      cycle_or_version: "2026-27",
      retrieved_at: "2026-10-31T12:00:00Z",
      extraction_status: "success",
      content_hash: "abcd1234efgh5678",
    }

    render(
      <EvidenceDrawer
        evidence={mockEvidence}
        source={mockSource}
        onClose={() => {}}
      />
    )

    expect(screen.getByText("Source Evidence Provenance")).toBeInTheDocument()
    expect(screen.getByText(/"All online applications must be completed and submitted by October 6, 2026 at 11:59 PM IST."/i)).toBeInTheDocument()
    expect(screen.getByText("Reliance Foundation Undergraduate Scholarship Application Portal")).toBeInTheDocument()
    expect(screen.getByText("Official Primary")).toBeInTheDocument()
    expect(screen.getByText("Important Dates")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: /open original source document/i })).toHaveAttribute(
      "href",
      "https://scholarships.reliancefoundation.org/UG_Scholarship.aspx"
    )
  })

  it("distinguishes Live AI, Precomputed and Mock/Demo modes in StatusBadge", async () => {
    const { StatusBadge } = await import("./components/StatusBadge")

    const { unmount: u1 } = render(<StatusBadge status="precomputed" label="Curated baseline" />)
    expect(screen.getByText("Curated baseline")).toBeInTheDocument()
    u1()

    const { unmount: u2 } = render(<StatusBadge status="supported" label="Live AI Analyzed" />)
    expect(screen.getByText("Live AI Analyzed")).toBeInTheDocument()
    u2()

    const { unmount: u3 } = render(<StatusBadge status="mock-demo" label="Mock / Demo" />)
    expect(screen.getByText("Mock / Demo")).toBeInTheDocument()
    u3()
  })

  it("renders epistemic accuracy terminology and historical cycle notice", async () => {
    const { AnalysisDashboard } = await import("./components/AnalysisDashboard")
    const mockResult = {
      project_id: "proj-scholarship-curated",
      dataset_hash: "abcd1234efgh5678",
      analysis_schema_version: "1.0.0",
      created_at: new Date().toISOString(),
      sources: [
        {
          id: "src-rf-portal",
          title: "Portal",
          type: "webpage" as const,
          authority: "primary_official" as const,
          url: "https://example.com",
          retrieved_at: new Date().toISOString(),
          extraction_status: "success" as const,
        },
      ],
      claims: [
        {
          id: "clm-1",
          normalized_statement: "Statement",
          entities: [],
          dates: [],
          is_verified: true,
          extraction_status: "success" as const,
          evidence_refs: [],
        },
      ],
      assessments: [],
      findings: [
        {
          id: "fnd-1",
          type: "potential_conflict" as const,
          label: "potential" as const,
          severity: "medium" as const,
          rationale: "Discrepancy notice",
          evidence_refs: [],
        },
      ],
      actions: [],
      summary: "Curated summary text",
    }

    render(
      <AnalysisDashboard
        result={mockResult}
        mode="precomputed"
        categories={[]}
        onSelectEvidence={() => {}}
        onReset={() => {}}
      />
    )

    // Epistemic KPI labels
    expect(screen.getByText("Evidence-linked Claims")).toBeInTheDocument()
    expect(screen.getByText("Claims supported by traceable source excerpts.")).toBeInTheDocument()
    expect(screen.getByText(/1 potential date discrepancy/i)).toBeInTheDocument()

    // Historical cycle contextual notice
    expect(
      screen.getByText(/Historical application-cycle review — the listed 2026 application dates have passed as of November 1, 2026./i)
    ).toBeInTheDocument()
  })
})
