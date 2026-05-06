---
source_file: US-Health-Insurer-PA-API-X12-278-Landscape.md
ingested: 2026-05-06
sha256: be6e3280b4cd15a761569a5b9056294ba1be320373c36b98705c445ffb88aaa3
---
---
title: US Health Insurer Prior Authorization API and X12 278 Landscape
url: discord-conversation://nemt-market-research/1501666938097504326
date: 2026-05-06
source: Discord / Sze's OpenClaw #nemt-market-research
tags: [prior-authorization, health-insurance, FHIR, X12-278, CMS-0057-F, payer-API, NEMT, interoperability, HIPAA, EDI, clearinghouse]
domain: work-knowledge
---

# US Health Insurer Prior Authorization API and X12 278 Landscape

Research conducted to identify which US health insurers expose prior authorization API endpoints, and critically, which ones allow actual PA submission (not just read/query) via API vs. EDI.

## Key Finding: Most Payer APIs Are Read-Only

Most payer developer portals expose **read-only** FHIR APIs for:
- Patient/member data access
- Claims history lookup
- Coverage discovery (what services require PA)
- Payer-to-payer data transfer

**Very few allow actual submission of a PA request via a direct API call.**

## Regulatory Context: CMS-0057-F Final Rule

The CMS Interoperability and Prior Authorization Final Rule (CMS-0057-F) mandates FHIR-based APIs for prior authorization. Deadlines staggered (most by Jan 1, 2027). Relevant spec: **Da Vinci Prior Auth Support (PAS) Implementation Guide** — specifically `CoverageRequirementsDiscovery ($crd)`, `DocumentationTemplates ($dtr)`, and `PriorAuthorizationSupport ($pas)` operations.

The three required FHIR API types:
1. **Provider Directory API** — look up payer PA requirements
2. **Prior Authorization API (PARS)** — CRD, DTR, PAS operations
3. **Payer-to-Payer API** — transfer PA history when switching insurers

## Payers with Direct API Submission Capability

### 1. Optum / UnitedHealthcare (via Optum API)
- Portal: `developer.optum.com/eligibilityandclaims`
- Prior Authorization API V1 — full lifecycle:
  - **Determination** — check if service requires PA
  - **Inquiry** — check status of existing PA
  - **Submission** — submit new PA request (JSON → EDI 278 translation)
  - **Authorization (Orchestration)** — combines determination + submission
- Payer coverage: 100+ payers via `customerconnect.optum.com/payerlist` with "Authorization Verification Inquiry Connection" values
- Sandbox available for testing
- **Most actionable API for NEMT use cases**
- Payers reachable: UnitedHealthcare, Golden Rule, Oxford Health Plans, UMR, others in Optum clearinghouse network

### 2. Payers That Only Expose Read-Only APIs (No Public Submission)

| Payer | Portal | Status |
|---|---|---|
| Aetna/CVS Health | developerportal.aetna.com/fhirapis | Read-only only |
| Cigna/Evernorth | developer.cigna.com | Read-only only |
| Humana | developers.humana.com/apis | Read-only only |
| Elevance/Anthem | anthem.com/developers | Read-only only |
| BCBS (all plans) | Various developer portals | Read-only only |
| Centene | various | Read-only only |
| Molina | various | Read-only only |
| Kaiser Permanente | various | Read-only only |

### 3. Middleware Platforms (Enable Multi-Payer PA Submission)
- **Redox Engine**: `docs.redoxengine.com/fhir-api-actions/financial/submit-prior-authorization/` — `POST /fhir/R4/.../Coverage/$submit`
- **Cohere Health**: `coherehealth.com/utilization-management/api-based` — Cohere Connect™
- These are clearinghouses, not payers, but route submissions to downstream payers

## X12 278 — The Mature EDI Alternative

The **X12 278** (Health Care Services Review — Request for Review and Response) is the **HIPAA-mandated standard** for electronic prior authorization. Unlike REST/FHIR APIs, 278 supports actual submission and is broadly supported.

### Confirmed Payers with 278 Companion Guides (formal EDI support)

| Payer | Companion Guide Location | Version |
|---|---|---|
| UnitedHealthcare | uhcprovider.com/.../EDI-278-Companion-Guide-005010X217.pdf | 005010X217 |
| Cigna Healthcare | cigna.com/static/.../5010-278N-companion-guide.pdf | 5010 278N |
| CMS / Medicare (all MACs) | cms.gov/files/.../esmd-x12n-278-companion-guide.pdf | varies |
| TMHP (Texas Medicaid) | tmhp.com/.../278_COMPANION_GUIDE.pdf | 5010 |
| CareCentrix | Available | 5010 |
| Mass General Brigham Health Plan | Available | 5010 |
| Nebraska DHHS Medicaid | Available | 5010 |
| Nevada Medicaid | medicaid.nv.gov/.../companionguide278.pdf | 5010 |
| Wisconsin DHS | Available | 5010 |

### Clearinghouses for 278 (Route to ~600+ payers in single integration)

| Clearinghouse | Payer Reach | Notes |
|---|---|---|
| Availity | ~600+ payers | Largest healthcare clearinghouse |
| Change Healthcare (Optum) | ~70,000+ connections* | *includes dental, not just PA |
| Waystar | ~300+ payers | Payer ID: login.zirmed.com/ui/Payers |
| ZirMed | ~150+ payers | Mid-size |
| Office Ally | Budget option | Smaller coverage, low cost |

### 278 Coverage Summary

- ✅ All Medicare Administrative Contractors (MACs) — Noridian, CGS, NGS, Palmetto
- ✅ All State Medicaid programs (50 states)
- ✅ Medicaid MCOs — Centene, Molina, UHC Community Plan
- ✅ Medicare Advantage — UHC, Humana, Aetna, Cigna, Elevance, BCBS, Kaiser
- ✅ Major Commercial — UHC, Aetna, Cigna, Humana, Elevance, BCBS (30+ plans)
- ✅ Regional/Small Plans — Blue Shield CA, Premera, Horizon BCBSNJ, Highmark, etc.
- ✅ Dental/Vision Plans — Delta Dental, VSP (separate 278 transaction sets)

### CMS Enforcement Discretion on 278 vs FHIR

From CMS.gov: X12 278 is still a HIPAA requirement, but CMS granted enforcement discretion — payers with a full FHIR Prior Authorization API are exempt from enforcement action for not using 278. However, **X12 278 alone cannot satisfy the CMS-0057-F rule** — the FHIR API has additional requirements (discovery, DTR, etc.) that 278 cannot meet.

## Practical Recommendation for NEMT

1. **Optum API** for UHC-network PA submissions (largest single network, direct API)
2. **X12 278 via clearinghouse** (Availity, Waystar, or Change Healthcare) for ~95%+ US payer coverage
3. **Payer web portals** for manual submission where no API/EDI exists
4. **Middleware** (Redox, Cohere Health) for abstraction layer across payers
5. Monitor FHIR PA API maturity — by 2027 most payers will have submission-capable FHIR APIs
