# OSFI B-13 — Reference File

Regulation reference for the BigID Compliance Report skill. Loaded in Step 4 when the
user selects **OSFI B-13**. Provides the regulatory facts, BigID category mapping,
controls-mapping skeleton, and report outline the PDF generator consumes.

OSFI Guideline **B-13 — Technology and Cyber Risk Management**, issued by the Office of
the Superintendent of Financial Institutions (Canada), **effective January 1, 2024**.
It applies to all federally regulated financial institutions (FRFIs) in Canada —
banks, insurers, trust and loan companies, and federally regulated pension plans.

This report is written from the perspective of the institution's Data Governance or
Compliance function — it should read like something a data governance officer sends to
a CISO or a board-level Risk Committee.

---

## Hardcoded regulatory facts

- **Instrument:** OSFI Guideline B-13, *Technology and Cyber Risk Management*.
- **Regulator:** Office of the Superintendent of Financial Institutions (OSFI), Canada.
- **Effective date:** January 1, 2024.
- **Applies to:** All federally regulated financial institutions (FRFIs).
- **Structure:** Three domains containing the guideline's principles.
  - **Domain 1 — Governance & Risk Management** (Principles 1–6): technology/cyber
    governance, risk management framework, data classification, ownership, lifecycle.
  - **Domain 2 — Technology Operations & Resilience** (Principles 7–11): asset
    management, technology operations, logging & monitoring, resilience, data protection.
  - **Domain 3 — Cybersecurity** (Principles 12–17): identity & access management,
    credential/secret management, encryption, secure configuration, defence & response.
- **Supervisory nature:** B-13 is a *principles-based* guideline. Non-compliance is not
  a fixed monetary penalty; OSFI exercises supervisory judgment and can escalate through
  its supervisory framework — increased monitoring, findings/recommendations, staging,
  and ultimately measures that affect the institution's standing. Frame regulatory risk
  in supervisory terms, not as a fine.
- **Related instruments to reference where relevant:** OSFI Technology & Cyber Security
  Incident Reporting (TCIR) advisory; Guideline B-10 (third-party risk).

> Verify current wording against the Step 2 web search. If the search surfaces an
> updated revision or supervisory expectation, reflect it in the Executive Summary and
> the References section. Primary sources:
> - https://www.osfi-bsif.gc.ca/en/risks/technology-cyber-risk-management
> - https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/technology-cyber-risk-management-self-assessment-tool

---

## Finding → B-13 domain/principle mapping

Use as the starting skeleton; adapt to what BigID actually returns. The left column is
the BigID finding/policy category (from cases-by-policy and data-categories pulls).

| BigID finding type | B-13 Domain | Key Principles | BigID evidence source |
|---|---|---|---|
| Tokens, keys, secrets in storage | Domain 3 — Cybersecurity | P12 (IAM), P13 (Credential Mgmt) | Security cases grouped by policy |
| Cleartext / explicit passwords | Domain 3 — Cybersecurity | P12, P13, P14 (Encryption) | Security cases grouped by policy |
| Personal Financial Info (PFI) / PCI exposed | Domain 3 — Cybersecurity | P11 (Data Protection), P14 | Cases + data categories |
| Open / public access to sensitive data | Domain 2 — Operations | P11 (Data Protection) | Cases by policy; catalog `open_access` |
| Access logging / monitoring disabled | Domain 2 — Operations | P8 (Logging & Monitoring), P10 | Cases by policy |
| No IT owners on data sources | Domain 1 — Governance | P2 (Risk Governance), P6 (Data Mgmt) | `post_ds_connections` → `owners_v2` |
| High % of objects carrying findings | Domain 1 — Governance | P6 (Data Classification & Lifecycle) | Coverage ratio (3g) |
| Unclassified / unscanned data at scale | Domain 1 — Governance | P6 | Coverage ratio; data categories |

Rate each domain as one of **Compliant / Partially compliant / Non-compliant**, mapped
to the report design-system colours: Compliant → green (`#1A7A2E`), Partially compliant
→ amber (`#E07B00`), Non-compliant → red (`#C0392B`).

---

## BigID data-category → B-13 data-type mapping

For the **Data Landscape** section. Map the categories returned by `get_data__categories`
to the B-13-relevant data types below; show counts where available.

| B-13 relevant data type | Typical BigID categories |
|---|---|
| Credentials & secrets | Tokens/Keys/Secrets, Passwords, API keys, AWS Access Key ID |
| Customer financial data | PFI, Payment Card / PCI, Account numbers, Banking data |
| Personal information | PII, Contact data, National ID / SIN, Email |
| Regulated/special data | Health (PHI), biometric, where present |
| Operational/system data | Logs, configuration, infrastructure metadata |

---

## Controls-compliance mapping skeleton

For the **Controls Compliance Mapping** section. One row per control area; fill
`Status` and `Evidence` from live data. Status values: Met / Partially met / Not met.

| B-13 control area | Principle(s) | BigID evidence to cite | Status |
|---|---|---|---|
| Privileged credential & secret management | P12, P13 | Count of open token/secret/password cases; affected objects | [derive] |
| Encryption & data protection at rest | P11, P14 | PFI/PCI exposure cases; cleartext findings | [derive] |
| Access control & least privilege | P11, P12 | Open/public-access cases; over-shared sensitive objects | [derive] |
| Logging, monitoring & detection | P8, P10 | Logging-disabled findings; monitoring-gap policies | [derive] |
| Data classification & lifecycle | P6 | Sensitive-data coverage %; unclassified volume | [derive] |
| Data ownership & risk governance | P2, P6 | Data sources missing `owners_v2`; unowned sensitive sources | [derive] |

---

## Report section outline (OSFI B-13)

Use the skill's **fixed nine canonical sections and headings** (Step 5 Repeatability
contract) — do not merge or renumber them. Below is the B-13-specific *content* for each;
the headings themselves stay verbatim.

1. **Cover page** — title shows "OSFI B-13 — Technology & Cyber Risk Management";
   subtitle "Data Governance & Security Posture Assessment"; org name if known; date;
   classification "Internal — Confidential"; data source "BigID MCP".
2. **Executive Summary** — overall posture, total open cases, highest-severity gaps, and
   the Compliant/Partially compliant/Non-compliant rollup across the three B-13 domains.
   Plain language for a Risk Committee. Fold in any Step 2 search update.
3. **Regulatory Overview** — what B-13 requires, the three-domain structure, effective
   date, FRFI applicability, and supervisory (not monetary) risk framing.
4. **Data Landscape** — BigID categories mapped to B-13 data types; include the
   sensitive-data coverage % from pull 3g.
5. **Compliance Frameworks Active** — frameworks, control counts, enabled status (3a).
6. **Policy & Security Posture** — policy pass/fail (3b), cases by severity (3c), top
   critical cases (3d).
7. **Controls Compliance Mapping** — the heart of the B-13 report. Group the controls
   skeleton rows by the three domains, but keep them within this single canonical
   section. For each control area: OSFI expectation → finding → gap analysis → status →
   B-13 principle reference. Use the §7 table columns from the contract.
8. **Open Items & Remediation Plan** — Immediate / Short-term / Medium-term buckets from
   open cases (3e) and ownership gaps (3g).
9. **Conclusion & Attestation** — the Domain/Area | Status | Key gap rollup, 1–2
   paragraphs on what non-compliance means in OSFI *supervisory* terms, then a numbered
   attestation list citing live data.

### Tone and voice

- Write as a compliance professional, not a technologist. Reader is the CISO or board
  Risk Committee.
- Be direct about non-compliance — no hedging.
- Connect technical findings to regulatory language explicitly (e.g., "exposed
  credentials in storage contravene B-13 Principle 13's expectation that privileged
  credentials be held in a secure vault").
- Use actual data source names and case counts from BigID — specificity makes the report
  credible and actionable.

---

## References (include in the report)

- OSFI — Technology and Cyber Risk Management:
  https://www.osfi-bsif.gc.ca/en/risks/technology-cyber-risk-management
- OSFI — B-13 Self-Assessment Tool:
  https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/technology-cyber-risk-management-self-assessment-tool
- Any additional current source surfaced during the Step 2 web search.
