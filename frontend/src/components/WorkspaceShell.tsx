import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StatusBadge } from "./StatusBadge"
import { 
  Compass, 
  FileSearch, 
  Layers, 
  ListChecks, 
  AlertCircle,
  ShieldCheck
} from "lucide-react"

export const WorkspaceShell: React.FC = () => {
  const [objective, setObjective] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [projectCreated, setProjectCreated] = useState(false)
  const [showErrorDemo, setShowErrorDemo] = useState(false)

  const handleCreateProject = () => {
    if (!objective.trim()) return
    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      setProjectCreated(true)
    }, 400)
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-[#CBD5E1] px-6 py-4 flex items-center justify-between sticky top-0 z-10">
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
          <StatusBadge status="precomputed" label="Curated baseline mode" />
          <div className="flex items-center gap-1.5 text-[14px] text-[#475569] bg-slate-100 px-3 py-1.5 rounded-md border border-[#CBD5E1]">
            <ShieldCheck className="w-4 h-4 text-[#0F766E]" aria-hidden="true" />
            <span>Provenance Safe</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Canvas */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        {!projectCreated ? (
          <div className="space-y-6">
            {/* Empty State / Research Objective Setup */}
            <Card className="bg-white border border-[#CBD5E1] rounded-[12px] shadow-none">
              <CardHeader className="p-6 pb-4">
                <CardTitle className="text-[28px] font-semibold leading-[1.2] text-[#0F172A]">
                  Start with a research objective
                </CardTitle>
                <CardDescription className="text-[16px] text-[#475569] leading-[1.5] mt-2">
                  Describe what you need to verify, then QuestionTrail will propose an editable assessment framework.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6 pt-0 space-y-4">
                <div className="space-y-2">
                  <label 
                    htmlFor="research-objective" 
                    className="block text-[14px] font-semibold text-[#0F172A] leading-[1.4]"
                  >
                    Research Objective
                  </label>
                  <Textarea
                    id="research-objective"
                    placeholder="e.g. Assess whether the available sources provide consistent and sufficiently current information about the Reliance Foundation Undergraduate Scholarship 2026–27..."
                    value={objective}
                    onChange={(e) => setObjective(e.target.value)}
                    rows={4}
                    className="w-full text-[16px] leading-[1.5] border-[#CBD5E1] rounded-[8px] focus-visible:ring-2 focus-visible:ring-[#0F766E] focus-visible:outline-none"
                  />
                </div>

                <div className="flex items-center justify-between pt-2">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      type="button"
                      size="sm"
                      onClick={() => setObjective("Assess whether the available sources provide consistent and sufficiently current information about the Reliance Foundation Undergraduate Scholarship 2026–27. Identify outdated information, conflicting claims, unanswered questions and what should be verified using official sources.")}
                      className="text-[14px] text-[#0F766E] hover:text-[#0F766E] hover:bg-[#0F766E]/10"
                    >
                      Load demo objective
                    </Button>
                  </div>

                  <Button
                    onClick={handleCreateProject}
                    disabled={!objective.trim() || isLoading}
                    className="min-h-[44px] px-6 text-[14px] font-semibold bg-[#0F766E] hover:bg-[#0F766E]/90 text-white rounded-[8px] transition-opacity focus-visible:ring-2 focus-visible:ring-[#0F766E]"
                  >
                    {isLoading ? "Proposing framework..." : "Create Research Project"}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Error State Preview Toggle */}
            <div className="pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowErrorDemo(!showErrorDemo)}
                className="text-[14px] text-[#475569] border-[#CBD5E1]"
              >
                {showErrorDemo ? "Hide error sample" : "Preview actionable error contract"}
              </Button>

              {showErrorDemo && (
                <div className="mt-4">
                  <Alert variant="destructive" className="bg-[#B91C1C]/5 border-[#B91C1C] text-[#B91C1C] rounded-[8px]">
                    <AlertCircle className="w-5 h-5 text-[#B91C1C]" />
                    <AlertTitle className="text-[14px] font-semibold">Source Ingestion Error</AlertTitle>
                    <AlertDescription className="text-[16px] leading-[1.5] mt-1 text-[#0F172A]">
                      We couldn’t process this source. Check that the URL/PDF is accessible, then try again or keep it out of this analysis.
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Active Project Header */}
            <Card className="bg-white border border-[#CBD5E1] rounded-[12px] p-6 shadow-none">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#CBD5E1]">
                <div>
                  <span className="text-[14px] font-semibold text-[#0F766E] uppercase tracking-wider">
                    Active Project
                  </span>
                  <h2 className="text-[20px] font-semibold leading-[1.2] text-[#0F172A] mt-1">
                    {objective}
                  </h2>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setProjectCreated(false)}
                  className="self-start md:self-auto text-[14px] text-[#475569] border-[#CBD5E1]"
                >
                  Reset Objective
                </Button>
              </div>

              {/* Workspace Navigation Tabs */}
              <Tabs defaultValue="framework" className="mt-6">
                <TabsList className="bg-[#F8FAFC] border border-[#CBD5E1] p-1 rounded-[8px]">
                  <TabsTrigger 
                    value="framework" 
                    className="min-h-[38px] text-[14px] font-medium data-[state=active]:bg-white data-[state=active]:text-[#0F766E] data-[state=active]:shadow-none"
                  >
                    <Layers className="w-4 h-4 mr-2" />
                    Assessment Framework
                  </TabsTrigger>
                  <TabsTrigger 
                    value="sources" 
                    className="min-h-[38px] text-[14px] font-medium data-[state=active]:bg-white data-[state=active]:text-[#0F766E] data-[state=active]:shadow-none"
                  >
                    <FileSearch className="w-4 h-4 mr-2" />
                    Sources & Provenance
                  </TabsTrigger>
                  <TabsTrigger 
                    value="checklist" 
                    className="min-h-[38px] text-[14px] font-medium data-[state=active]:bg-white data-[state=active]:text-[#0F766E] data-[state=active]:shadow-none"
                  >
                    <ListChecks className="w-4 h-4 mr-2" />
                    Verification Checklist
                  </TabsTrigger>
                </TabsList>

                {/* Framework Tab Content */}
                <TabsContent value="framework" className="mt-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-[20px] font-semibold leading-[1.2] text-[#0F172A]">
                        Assessment Categories
                      </h3>
                      <p className="text-[14px] text-[#475569] leading-[1.4] mt-1">
                        Review AI-suggested categories before analyzing sources.
                      </p>
                    </div>
                    <Button 
                      className="min-h-[44px] px-6 text-[14px] font-semibold bg-[#0F766E] hover:bg-[#0F766E]/90 text-white rounded-[8px]"
                    >
                      Approve Assessment Framework
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <Card className="border border-[#CBD5E1] rounded-[8px] p-4 bg-white">
                      <div className="flex items-center justify-between pb-2">
                        <span className="text-[16px] font-semibold text-[#0F172A]">Eligibility Criteria</span>
                        <StatusBadge status="ai-suggestion" />
                      </div>
                      <p className="text-[14px] text-[#475569] leading-[1.4]">
                        Evaluates required qualifications, household income thresholds, and academic standings.
                      </p>
                    </Card>

                    <Card className="border border-[#CBD5E1] rounded-[8px] p-4 bg-white">
                      <div className="flex items-center justify-between pb-2">
                        <span className="text-[16px] font-semibold text-[#0F172A]">Key Deadlines & Cycles</span>
                        <StatusBadge status="ai-suggestion" />
                      </div>
                      <p className="text-[14px] text-[#475569] leading-[1.4]">
                        Evaluates application deadlines, registration cutoffs, and relevant academic cycles.
                      </p>
                    </Card>
                  </div>
                </TabsContent>

                {/* Sources Tab Content */}
                <TabsContent value="sources" className="mt-6">
                  <div className="border border-dashed border-[#CBD5E1] rounded-[8px] p-8 text-center bg-white">
                    <h3 className="text-[20px] font-semibold text-[#0F172A] leading-[1.2]">
                      Add a source to begin evidence review
                    </h3>
                    <p className="text-[16px] text-[#475569] leading-[1.5] mt-2">
                      Use the curated demo sources or add a public URL/PDF.
                    </p>
                  </div>
                </TabsContent>

                {/* Checklist Tab Content */}
                <TabsContent value="checklist" className="mt-6">
                  <div className="space-y-3">
                    <h3 className="text-[20px] font-semibold text-[#0F172A]">
                      Verification Checklist
                    </h3>
                    <p className="text-[14px] text-[#475569]">
                      Prioritized verification actions derived deterministically from evidence status.
                    </p>
                    <div className="space-y-2 pt-2">
                      <Skeleton className="h-12 w-full bg-slate-200" />
                      <Skeleton className="h-12 w-full bg-slate-200" />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}
