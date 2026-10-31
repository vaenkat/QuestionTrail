# Curated Demo Dataset: Reliance Foundation Undergraduate Scholarship 2026–27

## Research objective

“Assess whether the available sources provide consistent and sufficiently current information about the Reliance Foundation Undergraduate Scholarship 2026–27. Identify outdated information, conflicting claims, unanswered questions and what should be verified using official sources.”

## Candidate source register

These are candidate references only. No source has yet been downloaded, parsed by the application, assigned a final source ID, or included in a runtime manifest.

| Candidate | URL | Authority/type | Known date/cycle | Validation status | Planned use / limitation |
|---|---|---|---|---|---|
| Official scholarship page | https://scholarships.reliancefoundation.org/UG_Scholarship.aspx | Official program page | 2026–27 page context to verify | URL reachable; crawler text was not useful | Primary official source; validate rendered/linked content via app pipeline. |
| Official announcement | https://www.reliancefoundation.org/media/media-release/Reliance_Foundation_Scholarships_2026-27 | Official media release | 14 Aug 2026; 2026–27 | Content confirmed | Strong current-cycle reference; contains high-level program details. |
| Official older FAQ | https://www.scholarships.reliancefoundation.org/assets/pdf/UGFAQ2425Final.pdf | Official PDF FAQ | 2024–25 | URL candidate; extraction still required | Intentional stale-source test; never present as current guidance. |
| Buddy4Study page | https://www.buddy4study.com/article/reliance-foundation-ug-scholarships | Third-party information page | 16 Sep 2026; 2026–27 | Content confirmed | Lists 5 Oct 2026 application deadline; lower authority than official material. |
| Unstop listing | https://unstop.com/scholarships/reliance-foundation-scholarships-2026-27-reliance-industries-limited-1750177/amp | Third-party listing | 2026–27 | Content confirmed | Lists 30 Sep 2026 registration deadline; determine whether this is a platform cutoff before calling it a conflict. |

## Provenance rules for ingest

For every finalized source store: stable source ID; original URL; title; source type/authority; publication date and application cycle/version where available; retrieval timestamp; extraction status; raw/extracted content hash; evidence chunks with exact snippets and URL/section/page locations.

## Known limitations and validation tasks

1. Fetch and archive original source content using the future source pipeline; do not rely solely on web-search extraction.
2. Confirm dates/cycles and extract PDF pages before creating the curated manifest.
3. Resolve whether each differing date is a deadline for the same action before classifying a potential contradiction.
4. Record uncertainty when renewal conditions are absent; lack of a statement is not a negative claim.
5. Generate the precomputed snapshot from the finalized corpus, then verify its hash/version guard.

## Expected demonstration signals—not pre-decided results

The dataset should make it possible to show dated-source warnings and a candidate deadline conflict. The analysis must calculate its actual claims, coverage, gaps, and checklist from the finalized content; do not hardcode expected findings.
