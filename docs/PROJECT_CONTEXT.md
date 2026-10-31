# QuestionTrail: Product Context

## Problem

Online research often produces information that is incomplete, dated, inconsistent, or insufficiently evidenced. Users need more than a chatbot or summary: they need to see what sources establish, where they disagree, what remains unknown, and what should be verified before acting.

## Product vision

QuestionTrail is an AI-assisted, evidence-first research and information-intelligence workspace. A user enters a free-text research objective, reviews generic AI-proposed assessment categories, adds sources, and receives traceable summaries, potential conflict signals, gaps, uncertainty-aware answers, and a prioritized verification plan.

Its core is a reusable evidence model—sources, metadata, claims, entities/dates, evidence snippets, assessments, findings, unanswered questions, and verification actions. It is not scholarship-specific, a search engine, a recommendation engine, or a generic chatbot.

## Hackathon objective and success story

For the SHINCHAN ONLINE HACKATHON 2026, demonstrate: an Indian undergraduate assesses whether sources on the Reliance Foundation Undergraduate Scholarship 2026–27 are sufficiently current and consistent before applying. They create a project, approve suggested categories, inspect curated evidence, investigate potential conflicts and gaps, ask a grounded question about renewal conditions, and receive a verification checklist and report.

The deadline is **1 November 2026, 5:00 PM IST**. A polished, complete flow outranks feature breadth.

## Locked scope

- Curated, pre-reviewed real source corpus is the primary judge experience; its analysis must derive from actual extracted content.
- Public URL ingestion and PDF upload are secondary, basic runtime capabilities.
- Live LLM support is provider-independent: NVIDIA NIM primary, Gemini optional, mock adapter for tests.
- A bundled precomputed snapshot must keep the curated demo working without providers or internet. It must never serve mismatched sources.
- The default flow is objective → suggested categories → optional edit → add sources → analyze → evidence dashboard → Q&A/checklist/report.

## Explicit exclusions for v1

No authentication, collaboration, payments, scholarship discovery/recommendations, autonomous crawler, database, microservices, Kubernetes, or agent framework. Do not represent AI signals as confirmed facts without evidence.

## Product principles

1. Evidence before assertion.
2. Potential signals are visibly distinct from sourced facts and uncertainty.
3. Reproducible source sets and analyses beat opaque convenience.
4. The engine stays domain-neutral; templates may be added later.
