"""Curated demo dataset: Reliance Foundation Undergraduate Scholarship 2026–27.

Provides:
- 5 reviewed sources with verified exact text snippets, dates, and authority
- Standard assessment categories for scholarship evaluation
- Baseline AnalysisResult with strict referential integrity
- Precomputed AnalysisSnapshot matching exact dataset hash and schema version

DESIGN RULE:
- Scholarship is a demonstration dataset and test fixture only.
- Domain models and analysis logic remain strictly domain-agnostic.
"""

from datetime import datetime, timezone
from questiontrail.domain.models import (
    Source,
    SourceAuthority,
    SourceType,
    AssessmentCategory,
    AssessmentStatus,
    EvidenceRef,
    LocationType,
    Claim,
    CategoryAssessment,
    Finding,
    FindingType,
    FindingLabel,
    FindingSeverity,
    VerificationAction,
    AnalysisResult,
    AnalysisSnapshot,
    ANALYSIS_SCHEMA_VERSION,
)
from questiontrail.services.canonical import (
    compute_content_hash,
    compute_dataset_hash,
)

DEMO_OBJECTIVE = (
    "Assess whether the available sources provide consistent and sufficiently current "
    "information about the Reliance Foundation Undergraduate Scholarship 2026–27. "
    "Identify outdated information, conflicting claims, unanswered questions and what "
    "should be verified using official sources."
)

SOURCE_TEXTS = {
    "src-rf-media-2627": (
        "Reliance Foundation Undergraduate Scholarships 2026-27.\n"
        "Date of Release: August 14, 2026. Mumbai, India.\n"
        "Reliance Foundation announces the opening of applications for its prestigious "
        "Undergraduate Scholarships for the academic year 2026-27. Up to 5,000 meritorious "
        "undergraduate students from across India will be awarded scholarships. "
        "The scholarship offers a grant of up to Rs 2 Lakhs over the duration of the degree programme. "
        "Students must be enrolled in the first year of a full-time regular undergraduate degree in any stream. "
        "Eligibility: Applicant must have passed Class 12 with a minimum of 60% aggregate marks. "
        "Household annual income must be less than Rs 15 Lakhs, with priority given to applicants "
        "with household income below Rs 2.5 Lakhs. "
        "Selection involves an online mandatory aptitude test covering verbal ability, analytical thinking, "
        "and numerical ability. Applications must be submitted through the official portal."
    ),
    "src-rf-portal-2627": (
        "Official Application Portal: Reliance Foundation Undergraduate Scholarships 2026-27.\n"
        "Last Updated: August 14, 2026.\n"
        "Applications are invited from first-year undergraduate students for the 2026-27 cohort.\n"
        "Important Dates: Application Portal opens on August 14, 2026. "
        "Application Deadline: All online applications must be completed and submitted by "
        "October 6, 2026 at 11:59 PM IST. Late submissions will not be entertained.\n"
        "Award Value: Up to INR 2,00,000 for the duration of the degree.\n"
        "Selection Criteria: Performance in Class 12 examination, household income verification, "
        "and score in the mandatory online aptitude test."
    ),
    "src-rf-faq-2425": (
        "Reliance Foundation Undergraduate Scholarships - Frequently Asked Questions (2024-25 Archive).\n"
        "Document Date: August 1, 2024.\n"
        "Notice: This FAQ applies to the 2024-25 application cycle.\n"
        "Application Deadline: September 15, 2024.\n"
        "Renewal Policy: Scholarship disbursement for subsequent years is contingent upon the scholar "
        "maintaining at least 60% aggregate marks or equivalent CGPA in each academic semester, along with "
        "satisfactory conduct certified by the institution. Scholars failing to meet the minimum marks "
        "threshold will face review or suspension of funding."
    ),
    "src-b4s-listing-2627": (
        "Buddy4Study: Reliance Foundation Undergraduate Scholarships 2026-27.\n"
        "Article Published: September 16, 2026.\n"
        "Reliance Foundation invites applications for 5,000 undergraduate scholarships.\n"
        "Key Details: Maximum scholarship amount: INR 2,00,000.\n"
        "Application Deadline: 5 October 2026. Applicants are advised to apply early.\n"
        "Eligibility: First year students with minimum 60% marks in 12th board exams."
    ),
    "src-unstop-listing-2627": (
        "Unstop Opportunity Listing: Reliance Foundation Scholarships 2026-27.\n"
        "Listed: September 20, 2026.\n"
        "Reliance Foundation Undergraduate Scheme 2026-27.\n"
        "Platform Registration Deadline: 30 September 2026. "
        "Note: Unstop registration portal closes earlier than the national application deadline.\n"
        "Eligible Courses: All undergraduate degrees (B.Tech, B.Sc, B.Com, B.A., etc.)."
    ),
}


def get_curated_sources() -> list[Source]:
    """Return the 5 curated sources with computed content hashes."""
    retrieval_dt = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    return [
        Source(
            id="src-rf-media-2627",
            title="Reliance Foundation Undergraduate Scholarships 2026-27 Media Release",
            url="https://www.reliancefoundation.org/media/media-release/Reliance_Foundation_Scholarships_2026-27",
            type=SourceType.webpage,
            authority=SourceAuthority.primary_official,
            publication_date="2026-08-14",
            cycle_or_version="2026-27",
            retrieved_at=retrieval_dt,
            extraction_status="success",
            content_hash=compute_content_hash(SOURCE_TEXTS["src-rf-media-2627"]),
            metadata={"publisher": "Reliance Foundation", "format": "press_release"},
        ),
        Source(
            id="src-rf-portal-2627",
            title="Reliance Foundation Undergraduate Scholarship 2026-27 Application Portal",
            url="https://scholarships.reliancefoundation.org/UG_Scholarship.aspx",
            type=SourceType.webpage,
            authority=SourceAuthority.primary_official,
            publication_date="2026-08-14",
            cycle_or_version="2026-27",
            retrieved_at=retrieval_dt,
            extraction_status="success",
            content_hash=compute_content_hash(SOURCE_TEXTS["src-rf-portal-2627"]),
            metadata={"publisher": "Reliance Foundation", "format": "portal_page"},
        ),
        Source(
            id="src-rf-faq-2425",
            title="Reliance Foundation Undergraduate Scholarships FAQ (Archive 2024-25)",
            url="https://www.scholarships.reliancefoundation.org/assets/pdf/UGFAQ2425Final.pdf",
            type=SourceType.pdf,
            authority=SourceAuthority.primary_official,
            publication_date="2024-08-01",
            cycle_or_version="2024-25",
            retrieved_at=retrieval_dt,
            extraction_status="success",
            content_hash=compute_content_hash(SOURCE_TEXTS["src-rf-faq-2425"]),
            metadata={"archive_notice": "Historical reference only", "format": "pdf_faq"},
        ),
        Source(
            id="src-b4s-listing-2627",
            title="Buddy4Study: Reliance Foundation Undergraduate Scholarships 2026-27",
            url="https://www.buddy4study.com/article/reliance-foundation-ug-scholarships",
            type=SourceType.webpage,
            authority=SourceAuthority.third_party,
            publication_date="2026-09-16",
            cycle_or_version="2026-27",
            retrieved_at=retrieval_dt,
            extraction_status="success",
            content_hash=compute_content_hash(SOURCE_TEXTS["src-b4s-listing-2627"]),
            metadata={"aggregator": "Buddy4Study"},
        ),
        Source(
            id="src-unstop-listing-2627",
            title="Unstop: Reliance Foundation Scholarships 2026-27 Listing",
            url="https://unstop.com/scholarships/reliance-foundation-scholarships-2026-27-reliance-industries-limited-1750177",
            type=SourceType.webpage,
            authority=SourceAuthority.third_party,
            publication_date="2026-09-20",
            cycle_or_version="2026-27",
            retrieved_at=retrieval_dt,
            extraction_status="success",
            content_hash=compute_content_hash(SOURCE_TEXTS["src-unstop-listing-2627"]),
            metadata={"aggregator": "Unstop"},
        ),
    ]


def get_curated_categories() -> list[AssessmentCategory]:
    """Standard evaluation categories for the scholarship research objective."""
    return [
        AssessmentCategory(
            id="cat-eligibility",
            name="Eligibility & Income Criteria",
            description="Requirements regarding enrollment, academic marks, and family income thresholds.",
            evaluation_question="What are the specific academic, enrollment, and household income eligibility requirements for 2026-27?",
            enabled=True,
        ),
        AssessmentCategory(
            id="cat-financial-benefits",
            name="Grant Amount & Number of Awards",
            description="The monetary value of the scholarship and the total number of students supported.",
            evaluation_question="How much financial support is offered and how many scholarships will be awarded?",
            enabled=True,
        ),
        AssessmentCategory(
            id="cat-deadlines",
            name="Application Deadlines & Key Dates",
            description="Dates for application submission, portal closing, and testing.",
            evaluation_question="What is the official final deadline to apply for the 2026-27 scholarship?",
            enabled=True,
        ),
        AssessmentCategory(
            id="cat-renewal-policy",
            name="Renewal & Maintenance Conditions",
            description="Requirements for maintaining the scholarship across multi-year degree programs.",
            evaluation_question="What academic performance criteria must scholars maintain to renew the grant in subsequent years for the 2026-27 cohort?",
            enabled=True,
        ),
    ]


def get_curated_analysis_result() -> AnalysisResult:
    """Precomputed, verified AnalysisResult derived directly from the curated sources."""
    sources = get_curated_sources()
    categories = get_curated_categories()
    dataset_hash = compute_dataset_hash(
        sources=sources,
        objective=DEMO_OBJECTIVE,
        categories=categories,
    )

    claims = [
        Claim(
            id="clm-grant-amount",
            normalized_statement="The scholarship provides a grant of up to Rs 2 Lakhs over the duration of the degree programme.",
            entities=["Reliance Foundation", "Undergraduate Scholarship"],
            dates=[],
            is_verified=True,
            extraction_status="success",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-rf-media-2627",
                    exact_snippet="The scholarship offers a grant of up to Rs 2 Lakhs over the duration of the degree programme.",
                    location_type=LocationType.section,
                    location_value="Media Release Body",
                ),
                EvidenceRef(
                    source_id="src-rf-portal-2627",
                    exact_snippet="Up to INR 2,00,000 for the duration of the degree.",
                    location_type=LocationType.section,
                    location_value="Award Value",
                ),
            ],
        ),
        Claim(
            id="clm-scholarship-count",
            normalized_statement="Up to 5,000 meritorious undergraduate students from across India will be awarded scholarships for 2026-27.",
            entities=["Reliance Foundation", "5,000 students"],
            dates=["2026-27"],
            is_verified=True,
            extraction_status="success",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-rf-media-2627",
                    exact_snippet="Up to 5,000 meritorious undergraduate students from across India will be awarded scholarships.",
                    location_type=LocationType.section,
                    location_value="Media Release Body",
                )
            ],
        ),
        Claim(
            id="clm-income-criteria",
            normalized_statement="Household annual income must be under Rs 15 Lakhs, with priority for applicants below Rs 2.5 Lakhs.",
            entities=["Eligibility", "Income Threshold"],
            dates=[],
            is_verified=True,
            extraction_status="success",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-rf-media-2627",
                    exact_snippet="Household annual income must be less than Rs 15 Lakhs, with priority given to applicants with household income below Rs 2.5 Lakhs.",
                    location_type=LocationType.section,
                    location_value="Eligibility Section",
                )
            ],
        ),
        Claim(
            id="clm-academic-criteria",
            normalized_statement="Applicants must have passed Class 12 with a minimum of 60% aggregate marks and be enrolled in the first year of a full-time regular undergraduate degree.",
            entities=["Class 12", "Undergraduate Enrollment"],
            dates=[],
            is_verified=True,
            extraction_status="success",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-rf-media-2627",
                    exact_snippet="Applicant must have passed Class 12 with a minimum of 60% aggregate marks.",
                    location_type=LocationType.section,
                    location_value="Eligibility Section",
                ),
                EvidenceRef(
                    source_id="src-rf-portal-2627",
                    exact_snippet="Applications are invited from first-year undergraduate students for the 2026-27 cohort.",
                    location_type=LocationType.section,
                    location_value="Portal Header",
                ),
            ],
        ),
        Claim(
            id="clm-official-deadline",
            normalized_statement="The official online application deadline is October 6, 2026 at 11:59 PM IST.",
            entities=["Application Deadline", "Reliance Foundation Portal"],
            dates=["2026-10-06"],
            is_verified=True,
            extraction_status="success",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-rf-portal-2627",
                    exact_snippet="All online applications must be completed and submitted by October 6, 2026 at 11:59 PM IST.",
                    location_type=LocationType.section,
                    location_value="Important Dates",
                )
            ],
        ),
        Claim(
            id="clm-b4s-deadline",
            normalized_statement="Buddy4Study states the application deadline is 5 October 2026.",
            entities=["Buddy4Study", "Application Deadline"],
            dates=["2026-10-05"],
            is_verified=False,
            extraction_status="success",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-b4s-listing-2627",
                    exact_snippet="Application Deadline: 5 October 2026. Applicants are advised to apply early.",
                    location_type=LocationType.section,
                    location_value="Key Details",
                )
            ],
        ),
        Claim(
            id="clm-unstop-deadline",
            normalized_statement="Unstop lists a platform registration deadline of 30 September 2026.",
            entities=["Unstop", "Platform Registration"],
            dates=["2026-09-30"],
            is_verified=False,
            extraction_status="success",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-unstop-listing-2627",
                    exact_snippet="Platform Registration Deadline: 30 September 2026. Note: Unstop registration portal closes earlier than the national application deadline.",
                    location_type=LocationType.section,
                    location_value="Opportunity Overview",
                )
            ],
        ),
        Claim(
            id="clm-renewal-archive-2425",
            normalized_statement="Historical 2024-25 FAQ requires maintaining at least 60% aggregate marks in each academic semester for scholarship renewal.",
            entities=["Renewal Policy", "2024-25 Cycle"],
            dates=["2024-25"],
            is_verified=False,
            extraction_status="success",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-rf-faq-2425",
                    exact_snippet="Scholarship disbursement for subsequent years is contingent upon the scholar maintaining at least 60% aggregate marks or equivalent CGPA in each academic semester",
                    location_type=LocationType.section,
                    location_value="Renewal Policy",
                )
            ],
        ),
    ]

    assessments = [
        CategoryAssessment(
            category_id="cat-eligibility",
            status=AssessmentStatus.supported,
            supporting_claim_ids=["clm-income-criteria", "clm-academic-criteria"],
            contrary_claim_ids=[],
            unanswered_questions=[],
            rationale="Academic eligibility (Class 12 >=60%) and household income thresholds (<15L, priority <2.5L) are clearly documented across official sources.",
        ),
        CategoryAssessment(
            category_id="cat-financial-benefits",
            status=AssessmentStatus.supported,
            supporting_claim_ids=["clm-grant-amount", "clm-scholarship-count"],
            contrary_claim_ids=[],
            unanswered_questions=[],
            rationale="Grant of up to Rs 2 Lakhs over degree tenure for up to 5,000 scholars confirmed by both press release and application portal.",
        ),
        CategoryAssessment(
            category_id="cat-deadlines",
            status=AssessmentStatus.conflicting,
            supporting_claim_ids=["clm-official-deadline"],
            contrary_claim_ids=["clm-b4s-deadline", "clm-unstop-deadline"],
            unanswered_questions=["Why does Buddy4Study show 5 October while the official portal states 6 October 2026?"],
            rationale="Conflicting dates identified: official portal specifies October 6, 2026, while third-party sites report October 5 (Buddy4Study) and September 30 (Unstop platform cutoff).",
        ),
        CategoryAssessment(
            category_id="cat-renewal-policy",
            status=AssessmentStatus.requires_verification,
            supporting_claim_ids=[],
            contrary_claim_ids=[],
            unanswered_questions=[
                "Are the 2026-27 renewal requirements identical to the 2024-25 criteria (minimum 60% semester aggregate)?",
                "Has Reliance Foundation published an updated 2026-27 FAQ document?"
            ],
            rationale="Information gap: 2026-27 official materials do not detail renewal or maintenance conditions; only the archived 2024-25 FAQ mentions a 60% semester requirement.",
        ),
    ]

    findings = [
        Finding(
            id="fnd-deadline-discrepancy",
            type=FindingType.potential_conflict,
            label=FindingLabel.potential,
            severity=FindingSeverity.medium,
            rationale="Aggregators list different dates than the primary official portal. Unstop notes its date is a platform cutoff, but Buddy4Study does not qualify its 5 October date.",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-rf-portal-2627",
                    exact_snippet="All online applications must be completed and submitted by October 6, 2026 at 11:59 PM IST.",
                    location_type=LocationType.section,
                    location_value="Important Dates",
                ),
                EvidenceRef(
                    source_id="src-b4s-listing-2627",
                    exact_snippet="Application Deadline: 5 October 2026. Applicants are advised to apply early.",
                    location_type=LocationType.section,
                    location_value="Key Details",
                ),
            ],
            contrasting_claim_ids=["clm-official-deadline", "clm-b4s-deadline"],
        ),
        Finding(
            id="fnd-stale-source-warning",
            type=FindingType.dated_information,
            label=FindingLabel.confirmed,
            severity=FindingSeverity.high,
            rationale="Publication date is August 1, 2024, referencing the 2024-25 cycle. Deterministic date check flags it as stale relative to the 2026-27 cycle.",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-rf-faq-2425",
                    exact_snippet="Application Deadline: September 15, 2024.",
                    location_type=LocationType.section,
                    location_value="Archive FAQ",
                )
            ],
        ),
        Finding(
            id="fnd-renewal-policy-gap",
            type=FindingType.information_gap,
            label=FindingLabel.confirmed,
            severity=FindingSeverity.medium,
            rationale="Curated sources for the 2026-27 cycle omit renewal criteria, leaving multi-year disbursement rules unverified.",
            evidence_refs=[
                EvidenceRef(
                    source_id="src-rf-media-2627",
                    exact_snippet="The scholarship offers a grant of up to Rs 2 Lakhs over the duration of the degree programme.",
                    location_type=LocationType.section,
                    location_value="Media Release Body",
                )
            ],
            sources_examined=["src-rf-media-2627", "src-rf-portal-2627"],
            scope_examined="2026-27 official scholarship documentation",
        ),
    ]

    actions = [
        VerificationAction(
            id="act-verify-deadline-portal",
            action="Confirm final submission timestamp directly on the official Reliance Foundation portal.",
            rationale="Aggregator dates (5 Oct, 30 Sep) differ from the official deadline of October 6, 2026.",
            priority_score=0.95,
            recommended_source="https://scholarships.reliancefoundation.org/UG_Scholarship.aspx",
            linked_claim_ids=["clm-official-deadline", "clm-b4s-deadline"],
            linked_finding_ids=["fnd-deadline-discrepancy"],
        ),
        VerificationAction(
            id="act-verify-renewal-rules",
            action="Request or inspect official 2026-27 FAQ for multi-year renewal GPA / marks requirements.",
            rationale="2026-27 official documentation omits renewal criteria; only 2024-25 guidance (60% marks) exists.",
            priority_score=0.80,
            recommended_source="Reliance Foundation Scholarship Support Desk",
            linked_claim_ids=["clm-renewal-archive-2425"],
            linked_finding_ids=["fnd-renewal-policy-gap"],
        ),
        VerificationAction(
            id="act-exclude-stale-faq",
            action="Discard 2024-25 FAQ deadlines when planning 2026-27 application timelines.",
            rationale="The 2024-25 FAQ references September 15, 2024, which is outdated by two cycles.",
            priority_score=0.75,
            recommended_source="https://scholarships.reliancefoundation.org/UG_Scholarship.aspx",
            linked_claim_ids=[],
            linked_finding_ids=["fnd-stale-source-warning"],
        ),
    ]

    return AnalysisResult(
        project_id="proj-scholarship-curated",
        dataset_hash=dataset_hash,
        analysis_schema_version=ANALYSIS_SCHEMA_VERSION,
        sources=sources,
        claims=claims,
        assessments=assessments,
        findings=findings,
        actions=actions,
        summary=(
            "The available sources confirm key parameters of the Reliance Foundation Undergraduate "
            "Scholarship 2026–27: up to 5,000 awards of up to Rs 2 Lakhs for first-year undergraduates with "
            "household income under Rs 15 Lakhs and Class 12 marks of at least 60%. "
            "However, two key verification issues exist: (1) conflicting application deadlines across official "
            "and third-party sources (October 6 official vs October 5 Buddy4Study and September 30 Unstop cutoff), "
            "and (2) an absence of official 2026–27 renewal guidelines, which are only documented in an outdated "
            "2024–25 archive FAQ."
        ),
    )


def get_curated_snapshot() -> AnalysisSnapshot:
    """Return precomputed AnalysisSnapshot matching exact dataset hash and schema version."""
    result = get_curated_analysis_result()
    return AnalysisSnapshot(
        dataset_hash=result.dataset_hash,
        schema_version=ANALYSIS_SCHEMA_VERSION,
        provider="precomputed",
        model="curated-ground-truth-v1",
        payload=result,
        created_at=datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc),
    )
