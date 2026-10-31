import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import App from "./App"

describe("WorkspaceShell foundation", () => {
  it("renders workspace branding and initial empty state", () => {
    render(<App />)
    
    // Top header branding
    expect(screen.getByText("QuestionTrail")).toBeInTheDocument()
    expect(screen.getByText("Evidence-first research workspace")).toBeInTheDocument()
    
    // Exact copywriting contract checks from 01-UI-SPEC.md
    expect(screen.getByText("Start with a research objective")).toBeInTheDocument()
    expect(
      screen.getByText(
        "Describe what you need to verify, then QuestionTrail will propose an editable assessment framework."
      )
    ).toBeInTheDocument()
    
    // Primary CTA check
    const createBtn = screen.getByRole("button", { name: "Create Research Project" })
    expect(createBtn).toBeInTheDocument()
    expect(createBtn).toBeDisabled() // Disabled until input has text
  })

  it("renders precomputed analysis mode badge", () => {
    render(<App />)
    expect(screen.getByTestId("status-precomputed")).toBeInTheDocument()
    expect(screen.getByText("Curated baseline mode")).toBeInTheDocument()
  })
})
