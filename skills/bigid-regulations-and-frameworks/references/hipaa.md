# HIPAA — Reference File

Regulation/framework reference for the BigID Regulations & Frameworks skill. Loaded in Step 4 when the
user selects **HIPAA**. Provides the regulatory facts, BigID category mapping,
controls-mapping skeleton, and report outline the PDF generator consumes.

US **Health Insurance Portability and Accountability Act of 1996** — implementing
regulations at 45 C.F.R. Parts 160 and 164: the **Privacy Rule** (Subpart E), the
**Security Rule** (Subpart C), the **Breach Notification Rule** (Subpart D), and the
**HITECH Act** modifications. Enforced by the HHS Office for Civil Rights (OCR).

The report is written for a HIPAA Privacy Officer / Security Officer reporting to the
CISO, Compliance Committee, or Board.

---

## Hardcoded regulatory facts

- **Instrument:** HIPAA (1996); 45 C.F.R. Parts 160, 162, 164; HITECH Act (2009);
  HIPAA Omnibus Final Rule (2013).
- **Regulator:** HHS Office for Civil Rights (OCR); state attorneys general (HITECH
  expanded enforcement authority).
- **Applies to:** *Covered entities* (health plans, health care clearinghouses, health
  care providers who transmit electronic health information) and their *business
  associates* (and subcontractors), each directly liable.
- **Civil monetary penalty tiers** (inflation-adjusted by HHS effective Jan 28, 2026):
  - Tier 1 — *No knowledge*: ~$141 to $71,162 per violation
  - Tier 2 — *Reasonable cause*: ~$1,424 to $71,162 per violation
  - Tier 3 — *Willful neglect, corrected within 30 days*: ~$14,232 to $71,162 per
    violation
  - Tier 4 — *Willful neglect, not timely corrected*: ~$71,162 to $2,134,831 per
    violation
  - **Annual cap (per identical provision):** $2,190,294 (2026 adjustment)
  - Criminal penalties (DOJ): up to $250,000 and 10 years' imprisonment for
    knowing-and-malicious disclosure of PHI.
- **Status of the Security Rule NPRM:** OCR's Notice of Proposed Rulemaking published
  January 6, 2025 (90 FR 800) would make most "addressable" specifications mandatory
  and require documented annual risk analyses. **As of June 2026 the rule is still
  proposed** — not final. The current Security Rule remains in force; OCR continues to
  enforce it. If finalised as proposed, compliance is required 240 days after
  publication. Report against the current rule; flag the NPRM as anticipated tightening.
- **Key operational duties (current Security Rule):**
  - Administrative safeguards (§164.308): risk analysis, workforce training, access
    management, contingency planning.
  - Physical safeguards (§164.310): facility access, workstation controls.
  - Technical safeguards (§164.312): access control, audit controls, integrity,
    transmission security.
  - Organisational requirements (§164.314): BAAs, group health plan documents.
  - Documentation (§164.316): written policies, six-year retention.
- **Breach Notification Rule:** notify affected individuals "without unreasonable
  delay" and not later than 60 days; OCR notification for breaches ≥500 individuals
  within 60 days; smaller breaches reported annually.

> Verify wording against the optional Step 3h currency check, only if one was run
> for this report — particularly any final rule status change. Primary sources:
> - HHS OCR (HIPAA): https://www.hhs.gov/hipaa/index.html
> - 45 C.F.R. Parts 160 & 164
> - HIPAA Security Rule NPRM (90 FR 800, Jan 6 2025)

---

## Finding → HIPAA mapping

| BigID finding type | HIPAA area | Regulatory ref | BigID evidence source |
|---|---|---|---|
| PHI in unauthorised systems / shadow IT | Privacy Rule scope | §164.502 | Catalog inventory; data categories |
| Open / public access to PHI | Access control | §164.312(a) | Cases by policy; `open_access` |
| Tokens, keys, secrets near PHI | Technical safeguards | §164.312(a)–(d) | Security cases by policy |
| Cleartext / unencrypted ePHI | Transmission security | §164.312(e); §164.312(a)(2)(iv) | Security cases by policy |
| Access logging / monitoring disabled | Audit controls | §164.312(b) | Cases by policy |
| No risk analysis evidence | Administrative safeguards | §164.308(a)(1)(ii)(A) | Out of scope for BigID — note in §7 |
| PHI without owner/custodian | Administrative safeguards | §164.308(a)(2) | Data sources missing `owners_v2` |
| Unclassified / unscanned PHI | Administrative safeguards | §164.308(a)(1) | Coverage ratio; data categories |
| Sub-contractor / BA access exposure | Organisational requirements | §164.314(a) | Data-source ownership; external sharing |

Status values: **Met / Partially met / Not met** at control level; **Compliant /
Partially compliant / Non-compliant** at section rollup. Map to the report design
colours (green / amber / red).

---

## BigID data-category → HIPAA PHI mapping

For the **Data Landscape** section. PHI = "individually identifiable health
information" — any of the 18 HIPAA Safe Harbor identifiers in combination with health,
treatment, or payment information.

| HIPAA PHI element (Safe Harbor) | Typical BigID categories |
|---|---|
| Names, addresses (smaller than state), dates tied to person | PII, contact data, DOB |
| Phone, fax, email, IP, URL | Contact data, online identifiers |
| SSN, MRN, health plan member ID | National ID, Medical Record Number, member ID |
| Account / certificate / vehicle / device IDs | Account numbers, device identifiers |
| Biometric identifiers; full-face photos | Biometric, image with face |
| Genetic data | Genomic, sequence |
| Diagnosis / treatment / payment data | Health condition, diagnosis code, claims |
| Other unique identifying number/code | Any custom identifier flagged in catalog |

ePHI = PHI in electronic form, which is what the Security Rule actually governs. Flag
any catalog item that combines an identifier with a health/treatment/payment attribute.

---

## Controls-compliance mapping skeleton

| Control area | Requirement ref | BigID evidence to cite | Status |
|---|---|---|---|
| Risk analysis & management | §164.308(a)(1) | PHI inventory; unclassified PHI volume | [derive] |
| Workforce access management | §164.308(a)(3)–(4) | Open-access PHI cases; over-shared findings | [derive] |
| Information access management | §164.308(a)(4) | Permission audits on PHI sources | [derive] |
| Technical access control | §164.312(a) | IAM-gap cases; shared accounts | [derive] |
| Audit controls | §164.312(b) | Logging-disabled findings on PHI sources | [derive] |
| Integrity controls | §164.312(c) | Tamper / hash-failure findings (if collected) | [derive] |
| Transmission security & encryption | §164.312(e), §164.312(a)(2)(iv) | Cleartext / weak-encryption cases on ePHI | [derive] |
| Business associate agreements | §164.314(a), §164.504(e) | External-share findings on PHI; vendor data flow | [derive] |
| Breach detection & notification | §164.400–414 | Logging coverage; incident metadata | [derive] |
| Workforce training & sanctions | §164.308(a)(5) | Out of scope for BigID — note in §7 | [derive] |
| Documentation & retention | §164.316 | Out of scope for BigID — note in §7 | [derive] |

Out-of-scope-for-BigID rows are kept (not dropped) and labelled accordingly.

---

## Report section content (HIPAA)

Use the skill's **fixed nine canonical sections and headings** (Step 5 Repeatability
Contract). Headings stay verbatim; content below is HIPAA-specific.

1. **Cover page** — title "HIPAA Compliance Report — Privacy, Security & Breach
   Notification Rules"; subtitle "ePHI Data Protection Assessment"; org name if known;
   date; classification "Internal — Confidential"; data source "BigID MCP".
2. **Executive Summary** — overall posture; ePHI volume and scope; highest-severity
   gaps; Compliant / Partially compliant / Non-compliant rollup. Note that the report
   evaluates the **current** Security Rule (the 2025 NPRM is not final as of June 2026);
   identify any controls where the proposed rule would tighten current practice.
3. **Regulatory Overview** — Privacy / Security / Breach Notification Rule structure;
   covered entities and business associates; CMP tier structure and 2026 inflation
   adjustments; the NPRM status note.
4. **Data Landscape** — BigID categories mapped to the 18 Safe Harbor identifiers;
   ePHI volume; data-source breakdown (where catalog tagging supports it).
5. **Compliance Frameworks Active** — frameworks, control counts, enabled status (3a).
6. **Policy & Security Posture** — policy pass/fail (3b), cases by severity (3c), top
   critical cases (3d) — prioritise PHI-tagged sources.
7. **Controls Compliance Mapping** — the heart of the report. Use the controls
   skeleton above. For each safeguard: HIPAA cite → finding → gap → status →
   reference. Use the §7 columns from the Repeatability Contract.
8. **Open Items & Remediation Plan** — Immediate / Short-term / Medium-term buckets.
   Prioritise: ePHI exposure with open access first; technical safeguard gaps
   (encryption, audit logging) second; administrative gaps (risk analysis, BAA
   coverage) third.
9. **Conclusion & Attestation** — Domain/Area | Status | Key gap rollup; 1–2
   paragraphs framing exposure under OCR's tiered CMP structure (which tier each gap
   most plausibly implicates, including the willful-neglect ceilings); numbered
   attestation list citing live data.

### Tone and voice

- Write as a HIPAA Privacy/Security Officer who reads OCR resolution agreements.
- Be direct about willful-neglect indicators (e.g., known-but-uncorrected exposed
  ePHI) — these carry the highest tier penalties.
- Connect technical findings to HIPAA cites explicitly (e.g., "unencrypted ePHI on a
  source flagged for cleartext transmission contravenes the addressable encryption
  specification at §164.312(a)(2)(iv); under the current rule a documented decision
  is required, and the NPRM would make this mandatory").
- Flag any BA-shared data sources — vendor exposure is a frequent OCR enforcement
  pattern.

---

## References (include in the report)

- HHS OCR — HIPAA: https://www.hhs.gov/hipaa/index.html
- HIPAA Security Rule NPRM (90 FR 800, Jan 6, 2025): consult the Federal Register
- Any additional current source surfaced during the optional Step 3h currency check (if run).
