import React from "react"
import { Badge } from "@/components/ui/badge"
import { 
  CheckCircle2, 
  AlertTriangle, 
  AlertCircle, 
  Sparkles, 
  Clock, 
  HelpCircle,
  FileCheck
} from "lucide-react"

export type StatusVariant = 
  | "supported"
  | "partially-covered"
  | "potential-conflict"
  | "gap"
  | "requires-verification"
  | "ai-suggestion"
  | "undated"
  | "pre-ingested"
  | "fetched"
  | "precomputed"

interface StatusBadgeProps {
  status: StatusVariant
  label?: string
  className?: string
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, className = "" }) => {
  switch (status) {
    case "supported":
      return (
        <Badge 
          variant="outline" 
          className={`bg-[#166534]/10 text-[#166534] border-[#166534]/30 font-medium inline-flex items-center gap-1.5 ${className}`}
          data-testid="status-supported"
        >
          <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{label || "Supported"}</span>
        </Badge>
      )
    case "potential-conflict":
      return (
        <Badge 
          variant="outline" 
          className={`bg-[#B45309]/10 text-[#B45309] border-[#B45309]/30 font-medium inline-flex items-center gap-1.5 ${className}`}
          data-testid="status-conflict"
        >
          <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{label || "Potential Conflict"}</span>
        </Badge>
      )
    case "gap":
    case "requires-verification":
      return (
        <Badge 
          variant="outline" 
          className={`bg-[#B91C1C]/10 text-[#B91C1C] border-[#B91C1C]/30 font-medium inline-flex items-center gap-1.5 ${className}`}
          data-testid="status-gap"
        >
          <AlertCircle className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{label || (status === "gap" ? "Information Gap" : "Requires Verification")}</span>
        </Badge>
      )
    case "ai-suggestion":
      return (
        <Badge 
          variant="outline" 
          className={`bg-[#4F46E5]/10 text-[#4F46E5] border-[#4F46E5]/30 font-medium inline-flex items-center gap-1.5 ${className}`}
          data-testid="status-ai"
        >
          <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{label || "AI Suggestion"}</span>
        </Badge>
      )
    case "precomputed":
      return (
        <Badge 
          variant="outline" 
          className={`bg-[#475569]/10 text-[#475569] border-[#CBD5E1] font-medium inline-flex items-center gap-1.5 ${className}`}
          data-testid="status-precomputed"
        >
          <Clock className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{label || "Precomputed analysis"}</span>
        </Badge>
      )
    case "pre-ingested":
      return (
        <Badge 
          variant="outline" 
          className={`bg-slate-100 text-[#475569] border-[#CBD5E1] font-medium inline-flex items-center gap-1.5 ${className}`}
          data-testid="status-pre-ingested"
        >
          <FileCheck className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{label || "Pre-ingested"}</span>
        </Badge>
      )
    default:
      return (
        <Badge 
          variant="outline" 
          className={`bg-slate-100 text-[#475569] border-[#CBD5E1] font-medium inline-flex items-center gap-1.5 ${className}`}
        >
          <HelpCircle className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{label || status}</span>
        </Badge>
      )
  }
}
