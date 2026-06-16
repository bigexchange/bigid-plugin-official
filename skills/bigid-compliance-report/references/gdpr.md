# GDPR — Reference File

Regulation reference for the BigID Compliance Report skill. Loaded in Step 4 when the
user selects **GDPR**. Provides the regulatory facts, BigID category mapping,
controls-mapping skeleton, and report outline the PDF generator consumes.

EU **General Data Protection Regulation** — Regulation (EU) 2016/679 — entered into
force May 25, 2018. Applies to controllers and processors handling personal data of EU
residents, with extraterritorial reach under Article 3(2).

The report is written for a Data Protection Officer (DPO), CISO, or General Counsel.

---

## Hardcoded regulatory facts

- **Instrument:** Regulation (EU) 2016/679 (General Data Protection Regulation).
- **Regulator:** national Data Protection Authorities (DPAs); one-stop-shop lead
  authority for cross-border cases via the EDPB.
- **In force:** since May 25, 2018; cumulative fines through early 2026 have crossed
  €7 billion across more than 2,200 documented enforcement actions.
- **Applies to:** any controller or processor processing personal data of EU residents,
  regardless of where the organisation is based (Art. 3(2)). Joint controllers and
  processors are directly liable for their own statutory obligations.
- **Two-tier penalty structure (Article 83):**
  - **Tier 1 (Art. 83(4))** — administrative or procedural failures (records of
    processing, breach notification, DPIA failures, DPO appointment). Up to
    **€10 million or 2% of worldwide annual turnover**, whichever is higher.
  - **Tier 2 (Art. 83(5))** — substantive rights and principles violations (lawful
    basis, consent validity, data-subject rights, international transfers). Up to
    **€20 million or 4% of worldwide annual turnover**, whichever is higher.
- **Beyond fines:** reprimands; processing bans (temporary or permanent); mandated
  audits; remediation orders; suspension of data flows.
- **Key obligations operationalised in this report:** lawful basis & consent (Art. 6, 7),
  data-subject rights (Art. 12–22), security of processing (Art. 32), records of
  processing activities — RoPA (Art. 30), breach notification (Art. 33–34), DPIA
  (Art. 35), international transfers (Chapter V).
- **Special categories** (Art. 9): racial/ethnic origin, political opinions, religious
  or philosophical beliefs, trade-union membership, genetic data, biometric data for
  unique identification, health data, sex life, sexual orientation. Processing is
  generally prohibited absent an Art. 9(2) condition.

> Verify wording against the Step 2 web search. EDPB guidelines and binding decisions
> change material interpretation; the AI Act overlay (in force from August 2026 for
> high-risk systems) is also folding into GDPR enforcement of AI processing. Primary
> sources:
> - Regulation 2016/679 (EUR-Lex): https://eur-lex.europa.eu/eli/reg/2016/679/oj
> - EDPB: https://www.edpb.europa.eu/edpb_en

---

## Finding → GDPR mapping

| BigID finding type | GDPR area | Article | BigID evidence source |
|---|---|---|---|
| Personal data in unauthorised systems | Lawful processing | Art. 5, 6 | Catalog inventory; data categories |
| Special-category data without Art. 9 basis | Special categories | Art. 9 | Data categories; cases by policy |
| Open / public access to personal data | Security of processing | Art. 32 | Cases by policy; `open_access` |
| Tokens, keys, secrets in storage | Security of processing | Art. 32 | Security cases by policy |
| Cleartext passwords / weak encryption | Security of processing | Art. 32(1)(a) | Security cases by policy |
| No records of processing activities | Accountability | Art. 30 | Inventory completeness; data sources |
| Stale or untracked data subjects' data | Storage limitation | Art. 5(1)(e) | Catalog age / retention metadata |
| Cross-border transfers without safeguards | International transfers | Chapter V | Data-source location; transfer findings |
| Personal data without owner/controller | Accountability | Art. 24, 30 | Data sources missing `owners_v2` |
| Unclassified / unscanned personal data | Accountability | Art. 5(2) | Coverage ratio; data categories |

Status values: **Met / Partially met / Not met** at control level; **Compliant /
Partially compliant / Non-compliant** at section rollup. Map to the report design
colours (green / amber / red).

---

## BigID data-category → GDPR data-class mapping

For the **Data Landscape** section. Map the categories returned by `get_data__categories`
to the GDPR data classes below; show counts where available.

| GDPR data class | Typical BigID categories |
|---|---|
| Personal data (Art. 4(1)) | PII, contact, identifiers, online identifiers |
| Special-category data (Art. 9) | Health (PHI), biometric, genomic, religious, political |
| Criminal-offence data (Art. 10) | Criminal record, conviction data |
| Financial data | PFI, payment card / PCI, account data |
| Children's data | Identifiers tied to minors (age tag) |
| Pseudonymised data | Hashed identifiers, tokenised PII |
| Operational / system data | Logs, configuration (relevant only if it includes PII) |

---

## Controls-compliance mapping skeleton

| Control area | Requirement ref | BigID evidence to cite | Status |
|---|---|---|---|
| Records of processing activities (RoPA) | Art. 30 | RoPA app population; inventory completeness | [derive] |
| Lawful basis & consent governance | Art. 6, 7 | Personal data found in systems without recorded basis | [derive] |
| Special-category data controls | Art. 9 | Cases on health/biometric/genomic data; access exposure | [derive] |
| Data-subject rights operations | Art. 12–22 | DSAR/erasure findability; catalog search readiness | [derive] |
| Security of processing | Art. 32 | Token/secret cases; open-access cases; encryption gaps | [derive] |
| Breach detection & notification | Art. 33–34 | Logging/monitoring findings | [derive] |
| DPIA for high-risk processing | Art. 35 | PIA app coverage of high-risk apps | [derive] |
| International transfers | Chapter V | Data-source location; transfer-mechanism evidence | [derive] |
| Accountability — ownership & RoPA owners | Art. 24, 30 | Data sources missing `owners_v2` | [derive] |
| Data classification & lifecycle | Art. 5(1)(c)–(e) | Coverage ratio; retention metadata | [derive] |

Out-of-scope-for-BigID items (e.g., contractual SCC text, DPO appointment notice) keep
their row and are marked accordingly.

---

## Report section content (GDPR)

Use the skill's **fixed nine canonical sections and headings** (Step 5 Repeatability
Contract). Headings stay verbatim; content below is GDPR-specific.

1. **Cover page** — title "GDPR Compliance Report — Regulation (EU) 2016/679";
   subtitle "Data Protection & Accountability Assessment"; org name if known; date;
   classification "Internal — Confidential"; data source "BigID MCP".
2. **Executive Summary** — overall posture; volumes of personal data and special
   categories; whether RoPA is populated and current; Compliant / Partially compliant /
   Non-compliant rollup. Fold in any Step 2 search update — particularly recent EDPB
   guidance or material national enforcement actions.
3. **Regulatory Overview** — material scope (Art. 2) and territorial scope (Art. 3);
   the Article 83 two-tier penalty structure; the rights-based architecture (Art.
   12–22); accountability as a first-class duty (Art. 5(2), 24).
4. **Data Landscape** — BigID categories mapped to GDPR data classes; separate breakouts
   for personal data, special-category data (Art. 9), criminal-offence data (Art. 10),
   and children's data; cross-border distribution where data sources are tagged.
5. **Compliance Frameworks Active** — frameworks, control counts, enabled status (3a).
6. **Policy & Security Posture** — policy pass/fail (3b), cases by severity (3c), top
   critical cases (3d).
7. **Controls Compliance Mapping** — the heart of the report. Use the controls skeleton
   above. For each control area: GDPR article → finding → gap → status → reference. Use
   the §7 columns from the Repeatability Contract.
8. **Open Items & Remediation Plan** — Immediate / Short-term / Medium-term buckets.
   Prioritize: special-category exposure first; Article 32 security gaps with
   open-access second; accountability/RoPA gaps third.
9. **Conclusion & Attestation** — Domain/Area | Status | Key gap rollup; 1–2 paragraphs
   framing exposure under Art. 83 (which tier each material gap implicates and the
   maximum applicable penalty); numbered attestation list citing live data.

### Tone and voice

- Write as a DPO speaking to a board or supervisory authority.
- Be direct about which gaps fall under Tier 1 vs Tier 2 — the penalty ceiling differs
  materially.
- Connect technical findings to GDPR articles explicitly (e.g., "exposed credentials
  on systems processing personal data are an Article 32 security failure; the same
  files held special-category data, raising the Article 9 question of lawful condition").
- Distinguish controller and processor obligations where it matters; processors are
  directly liable for their own statutory duties.

---

## References (include in the report)

- Regulation (EU) 2016/679: https://eur-lex.europa.eu/eli/reg/2016/679/oj
- European Data Protection Board (EDPB): https://www.edpb.europa.eu/edpb_en
- Any additional current source surfaced during the Step 2 web search.
