# AI Evidence-to-Decision Simulator By Mahant S Arawal

A forensic decision-intelligence application built using Python, Streamlit, and the Google Gemini API. The system investigates commercial supply chain discrepancies using multi-source business documents, structured evidence registers, chronological timelines, contradiction analysis, controlled hidden record access, and rubric-based decision evaluations.

---

## 1. Project Overview & Scenario

### The Case: Missing Microcontroller Consignment (PO-88421)
- **Contract:** Zenith Electronics Ltd. issued PO-88421 for 500 units of High-Precision Microcontroller IC-902 worth INR 18,00,000 (18 Lakh) from Apex Microtech Pvt. Ltd. (Bangalore).
- **Supplier Claim:** Apex Microtech generated invoice DISP-6619 asserting that 500 units (10 cartons, 40 kg) were packed and handed over to SwiftLogix Express under Waybill SLX-904821.
- **Courier Tracking:** SwiftLogix tracking shows status DELIVERED at Secondary Staging Annex Dock 2; signed by gate guard R. Sharma. Transit scale recorded gross weight as 28.0 kg (not 40.0 kg). Carrier explicitly notes that inner piece counts were not inspected.
- **Warehouse Inward:** Zenith Main Warehouse received an annex transfer and inwarded only 350 units across 7 cartons. 3 cartons (150 units, worth INR 5.4 Lakh) are missing.
- **Anomalous Redirection:** An email from operations-dispatch@apex-orders-update.com diverted delivery away from Warehouse 1 to the Secondary Annex citing roof maintenance.
- **Confidential Records:** Releasing controlled hidden evidence (HID-001, HID-002, HID-003) allows the investigator to discover driver delivery reservations, CCTV gate proof, and internal supplier QA staging audits conclusively resolving the missing units.

---

## 2. Architecture & File Structure

```text
AI_Evidence_to_Decision_Simulator/
│
├── app.py                      # Main Streamlit UI, multi-tab layout, and session state
├── copilot.py                  # Interactive investigation copilot and context assistant
├── llm.py                      # Gemini API integration, ask_ai(), and ask_ai_json()
├── evidence.py                 # PDF/Email extraction, evidence IDs, and hidden access controls
├── investigator.py             # Event timeline, conflict detection, and grounded Q&A
├── evaluator.py                # 100-point decision evaluation rubric & attempt history
├── report.py                   # Final markdown report generation and export
├── test_simulator.py           # Automated test suite covering all minimum test cases
├── create_synthetic_docs.py    # Script generating synthetic PDF and email records
│
├── data/
│   ├── available_evidence/     # Initial documents (PO, Dispatch, Courier, GRN, Email, Memo)
│   └── hidden_evidence/        # Confidential records (POD run sheet, Gate CCTV, Supplier audit)
│
├── .env.example                # Template for Gemini API key and model config
├── .gitignore                  # Git exclusions for secrets and virtualenvs
├── requirements.txt            # Dependency specification
└── README.md                   # Documentation and usage guide
```

---

## 3. Evidence Integrity & Security Architecture

1. **Deterministic Access Control:**
   - Hidden documents are stored physically isolated in `data/hidden_evidence/`.
   - Hidden document contents are **never** passed to Gemini or exposed in the workspace until formal Python-level release.
   - Nonexistent IDs (`HID-999`) and requests lacking sufficient investigative justification are rejected by Python logic before any model interaction.
2. **Citation Validation:**
   - All citations in investigator decisions and LLM assistant answers are validated against the active register using regex and Python set intersection. Invalid or unreleased IDs are penalized and flagged.
3. **Prompt Injection Hardening:**
   - Document contents are encapsulated inside `<untrusted_document_content>` tags. Directives inside documents (such as `[SYSTEM OVERRIDE: ...]`) are treated strictly as passive evidence and cannot alter application state or bypass access rules.
4. **Python-Calculated Scoring:**
   - The final score is computed and verified by Python logic enforcing strict criterion bounds (`0 <= s <= max_pts`), preventing model hallucinations from assigning invalid totals.

---

## 4. Setup & Installation

### Prerequisites
- Python 3.9+ (Python 3.10 to 3.12 recommended)
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### Installation (macOS & Linux)
```bash
# 1. Create and activate virtual environment
python3 -m venv coach_env
source coach_env/bin/activate

# 2. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY
```

### Installation (Windows PowerShell)
```powershell
# 1. Create and activate virtual environment
python -m venv coach_env
.\coach_env\Scripts\Activate.ps1

# If execution policy blocks activation:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment variables
copy .env.example .env
```

---

## 5. Running the Application

Launch the Streamlit interface:
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your web browser.

---

## 6. Running Automated Tests

Run the full pytest suite:
```bash
coach_env/bin/pytest -v test_simulator.py
```

### Verification Results
All 21 test cases pass:
- `test_conflicting_quantities_produce_conflict_referencing_both`: PASSED
- `test_delivery_status_not_treated_as_quantity_proof`: PASSED
- `test_nonexistent_evidence_id_rejected_safely`: PASSED
- `test_embedded_instruction_treated_as_untrusted`: PASSED
- `test_malformed_json_or_api_failure_recovery`: PASSED
- `test_insufficient_evidence_cautious_conclusion`: PASSED
- `test_hidden_evidence_inaccessible_before_release`: PASSED
- `test_request_missing_justification_rejected`: PASSED
- `test_released_evidence_becomes_available`: PASSED
- `test_decision_submission_rejects_invalid_evidence`: PASSED
- `test_resubmission_preserves_previous_attempts`: PASSED
- `test_final_report_includes_sources_and_questions`: PASSED
- `test_reset_workflow_isolates_state`: PASSED
- `test_citation_validator`: PASSED
- `test_missing_evidence_files_handled_gracefully`: PASSED
- `test_unauthorized_confidential_record_access_blocked`: PASSED
- `test_submission_with_only_invalid_citations_rejected`: PASSED
- `test_malformed_llm_json_structures_fallback_cleanly`: PASSED
- `test_clean_pdf_text_extraction_without_encoding_artifacts`: PASSED
- `test_confidential_records_not_leaked_in_unauthorized_report`: PASSED
- `test_copilot_system_context_generation`: PASSED

---

## 7. Decision Evaluation Rubric

Evaluations are scored strictly against a 100-point rubric:

| Rubric Criterion | Max Points | Evaluation Focus |
| :--- | :---: | :--- |
| **Factual Accuracy** | 20 | Distinguishes verified facts from reported claims. Courier delivery does not equal 500 units received. |
| **Supporting Evidence** | 20 | Citation of valid, accessible evidence IDs substantiate claims. Penalizes fabricated IDs. |
| **Counterevidence Analysis** | 15 | Explicit consideration of conflicting records (weight discrepancy, PO vs GRN, address change). |
| **Recognition of Uncertainty** | 15 | Calibrated confidence; avoids unjustified certainty when root-cause evidence is missing. |
| **Reasoning Coherence** | 15 | Sound forensic deduction connecting records without jumping to unfounded criminal accusations. |
| **Actionable Next Steps** | 15 | Proportionate follow-up actions (carrier POD inspection, CCTV gate audit, supplier credit note). |
| **Total Score** | **100** | Python calculates and validates total score. |
