# NIST-P Scoring Rubric

## Control-to-Risk-Case Mapping

Use this table to determine which open risk cases affect which NIST-P controls.
When a control has open cases mapped to it, its status drops from "In Place" to "Partial" or "Gap".

### IDENTIFY-P Controls

| Control | Name | Degrade to Partial if... | Degrade to Gap if... |
|---|---|---|---|
| ID.IM-P1 | Data Processing Inventory | Any data source lacks catalog coverage | Shadow IT cases open with no controls |
| ID.IM-P2 | Data Flow Mapping | Cross-border transfer cases open | Multiple cross-border cases with no mechanism documented |
| ID.IM-P3 | Third-Party Data Inventory | 1–3 vendor review cases open | 4+ vendor review cases open |
| ID.IM-P4 | Data Classification | Minor classification gaps | Sensitive data policy violations active |
| ID.RA-P1 | Privacy Risk Identification | Risk register exists but < 30 risks defined | No active risk assessment program |
| ID.RA-P2 | Privacy Risk Assessment | Some risks lack probability/impact scores | No scoring methodology applied |
| ID.RA-P3 | Risk to Individuals | Child data / harm cases open | Child data with no controls mapped |
| ID.RA-P4 | Emerging Risk Monitoring | AI risks tracked but some uncontrolled | AI risk cases with 0 controls, no DPIA |

### GOVERN-P Controls

| Control | Name | Degrade to Partial if... | Degrade to Gap if... |
|---|---|---|---|
| GV.PO-P1 | Privacy Policy Management | Some frameworks disabled | Missing RoPA cases open |
| GV.PO-P2 | Legal & Regulatory Compliance | Some jurisdictional gaps | Active unlawful processing cases |
| GV.PO-P3 | Assigned Privacy Roles | Accountability gaps evidenced by awareness cases | No DPO or privacy owner identifiable |
| GV.PO-P4 | Privacy Training | 1–2 awareness gap cases | 3+ awareness gap cases open |

### CONTROL-P Controls

| Control | Name | Degrade to Partial if... | Degrade to Gap if... |
|---|---|---|---|
| CT.DP-P1 | Data Minimization | 1–2 overcollection cases | 3+ overcollection cases, risk score ≥ 12 |
| CT.DP-P2 | Purpose Limitation | Legitimate interest cases pending balancing test | Processing without lawful basis cases open |
| CT.DP-P3 | Consent Management | 1 consent case open | Consent missing across multiple systems |
| CT.DP-P4 | Automated Decisions Gov. | AI decision cases open with controls | AI decision cases with no DPIAs |
| CT.DP-P5 | Privacy by Design/Default | Privacy by Design not consistently applied | No SDLC privacy gate, PbD cases unresolved |

### COMMUNICATE-P Controls

| Control | Name | Degrade to Partial if... | Degrade to Gap if... |
|---|---|---|---|
| CM.CO-P1 | Transparent Privacy Notices | Notice-related cases open | Consent/notice missing at data collection |
| CM.CO-P2 | Individual Rights Enablement | DSR capability exists but untested | Active cases flagging inability to fulfil DSRs |
| CM.CO-P3 | Breach Notification | Procedure defined but untested | Active uncontrolled deletion/breach risk |
| CM.CO-P4 | Privacy Inquiry Channels | Channel defined but not operationalized | No mechanism exists |

### PROTECT-P Controls

| Control | Name | Degrade to Partial if... | Degrade to Gap if... |
|---|---|---|---|
| PR.DS-P1 | Data Encryption | Unencrypted data policy active but findings exist | Multiple unencrypted data cases unresolved |
| PR.DS-P2 | Access Control | 1–2 unauthorized access cases | RBAC missing + multiple unauthorized access cases |
| PR.DS-P3 | Activity Logging | Logging defined but Shadow IT gaps | Shadow IT cases with no logging controls |
| PR.DS-P4 | Anonymization/Pseudonymization | Overcollection implies no de-identification | Sensitive data stored without anonymization |
| PR.DS-P5 | Retention & Disposal | 1–3 retention schedule missing cases | 4+ retention cases OR incomplete deletion uncontrolled |

---

## Scoring Formula

### Per-control score
- **In Place** = 1.0
- **Partial** = 0.5
- **Gap** = 0.0

### Per-function score
```
function_score = (sum of control scores / total controls in function) × 100
round to nearest integer
```

Example: PROTECT-P has 5 controls. If PR.DS-P1=In Place (1.0), PR.DS-P2=Gap (0.0), PR.DS-P3=Partial (0.5), PR.DS-P4=Partial (0.5), PR.DS-P5=Gap (0.0):
```
score = (1.0 + 0.0 + 0.5 + 0.5 + 0.0) / 5 × 100 = 40%
```

### Overall score
```
overall_score = average of all 5 function scores
round to nearest integer
```

### Maturity labels
- **Managed**: score ≥ 75%
- **Developing**: score 50–74%
- **Initial**: score < 50%

---

## Key Risk Categories → NIST-P Function

Use this mapping when analyzing risk cases not explicitly tagged to NIST-P:

| Risk Category (BigID) | Primary NIST-P Function | Primary Controls |
|---|---|---|
| Data Retention & Deletion | PROTECT-P | PR.DS-P5, CT.DP-P1 |
| Access & Security | PROTECT-P | PR.DS-P2, PR.DS-P3 |
| AI Governance | CONTROL-P | CT.DP-P4, ID.RA-P4 |
| Consent & individual rights management | CONTROL-P | CT.DP-P3, CM.CO-P2 |
| Data lifecycle management | CONTROL-P | CT.DP-P1, CT.DP-P2 |
| Privacy Program Education | GOVERN-P | GV.PO-P4, CT.DP-P5 |
| Third-Party Risk Management | IDENTIFY-P | ID.IM-P3, GV.PO-P2 |
| Third Party Vendor management | GOVERN-P | GV.PO-P2, ID.IM-P3 |
| Transfer / International Data Transfers | CONTROL-P | CT.DP-P2, GV.PO-P2 |
| Profiling / Tracking | CONTROL-P | CT.DP-P2, CT.DP-P3 |
| General Privacy Risk | GOVERN-P | GV.PO-P1, ID.IM-P2 |
| Payment Card Industry Standard | PROTECT-P | PR.DS-P1, PR.DS-P2 |

---

## Prioritization Logic for the Executive Summary (Top Open Risks)

Select top 8 risks from the open cases, ranked by:
1. Risk score (probability × impact) descending
2. Controls count ascending (0 controls = highest urgency)

For each selected risk, find its NIST-P mapping using the table above plus any explicit control mappings from the `controls[]` field on the risk case.

Use this ranked list to drive the "new-case callout" on the Executive Summary slide (see SKILL.md Step 4) and to prioritize which cases appear first in each control's findings table.

---

## Additional Catalog-Derived Risk Patterns

Always check for the following risk patterns in the live data. When present, make sure they surface on their mapped control's drilldown slide (SKILL.md Step 4, "one slide per control") and are called out in the Executive Summary's new-case callout if severity is Critical or High:

| Check | What to look for | NIST-P mapping |
|---|---|---|
| Child/minor data | Any risk named "Processing of child (minors) data" with mappedControls=0 | CT.DP-P3 / ID.RA-P3 |
| LLM token exposure | BigID policy "Public LLM Secrets and Tokens" active | PR.DS-P2 / GV.PO-P1 |
| AI datasets with sensitive data | Policies "AI Datasets with Restricted/Confidential Sensitive Data" active | CT.DP-P4 / PR.DS-P1 |
| Open-source AI | Risk case "Open-Source AI Component" with mappedControls=0 | CT.DP-P4 / GV.PO-P1 |
| Missing RoPAs | Risk "Missing records of processing activities" with mappedControls < 5 | GV.PO-P1 / ID.IM-P2 |
| Subprocessor gaps | Risk "Addition of subprocessors without necessary notifications" | GV.PO-P2 / CM.CO-P3 |
| Shadow IT | Risk "Shadow IT processing of personal data" | PR.DS-P2 / ID.IM-P1 |
| Sensitive data no DPIA | Risk "Processing of Sensitive Personal Data" with mappedControls=0 | CT.DP-P1 / PR.DS-P1 |
| Cross-border restricted | Risk involving Russia, Iran, North Korea, China, Venezuela, Cuba | CT.DP-P2 / GV.PO-P2 |

For each matched item, set severity: Critical (score ≥ 14, 0 controls), High (score ≥ 8), Medium (score ≥ 4), Low (otherwise).
