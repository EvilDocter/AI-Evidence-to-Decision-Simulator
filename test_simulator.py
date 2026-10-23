import os
import pytest
from evidence import (
    load_initial_evidence_register,
    get_hidden_catalogue,
    request_hidden_evidence,
    validate_evidence_ids,
    read_pdf,
    read_email,
    read_text,
    INITIAL_DOCUMENTS_CONFIG
)
from investigator import (
    build_timeline,
    detect_conflicts,
    validate_citations_in_text,
    ask_investigation_assistant,
    build_evidence_context_prompt
)
from evaluator import (
    validate_submission_inputs,
    evaluate_decision_deterministic,
    evaluate_decision_with_llm,
    record_submission_attempt
)
from report import generate_investigation_report
from llm import ask_ai_json, clean_json_text

@pytest.fixture
def fresh_evidence_register():
    return load_initial_evidence_register()

# 1. Conflicting quantities or dates across two documents produce a conflict referencing both sources
def test_conflicting_quantities_produce_conflict_referencing_both(fresh_evidence_register):
    conflicts = detect_conflicts(fresh_evidence_register)
    qty_conflicts = [c for c in conflicts if "EVD-002" in c["evidence_ids"] and "EVD-004" in c["evidence_ids"]]
    assert len(qty_conflicts) > 0
    c = qty_conflicts[0]
    assert "EVD-002" in c["evidence_ids"]
    assert "EVD-004" in c["evidence_ids"]
    assert "500" in c["claim_a"]
    assert "350" in c["claim_b"]

# 2. A delivery record confirming delivery status is not incorrectly treated as proof that all 500 units arrived
def test_delivery_status_not_treated_as_quantity_proof(fresh_evidence_register):
    conflicts = detect_conflicts(fresh_evidence_register)
    delivery_conflicts = [c for c in conflicts if "EVD-003" in c["evidence_ids"] and "EVD-004" in c["evidence_ids"]]
    assert len(delivery_conflicts) > 0
    c = delivery_conflicts[0]
    assert "EVD-003" in c["evidence_ids"]
    assert "does not prove all 500 units were present" in c["why_conflicts"]

# 3. A nonexistent evidence ID is rejected safely
def test_nonexistent_evidence_id_rejected_safely(fresh_evidence_register):
    release_history = []
    success, msg = request_hidden_evidence(
        "HID-999",
        "Investigating missing cartons at dock",
        "Where are the missing boxes?",
        fresh_evidence_register,
        release_history
    )
    assert success is False
    assert "does not exist" in msg
    assert "HID-999" not in fresh_evidence_register

# 4. An instruction embedded inside a document is treated as untrusted content, not executed
def test_embedded_instruction_treated_as_untrusted(fresh_evidence_register):
    assert "EVD-006" in fresh_evidence_register
    doc = fresh_evidence_register["EVD-006"]
    assert "SYSTEM OVERRIDE" in doc["raw_text"]
    
    # Check that context prompt encapsulates it in <untrusted_document_content>
    prompt_context = build_evidence_context_prompt(fresh_evidence_register)
    assert "<untrusted_document_content>" in prompt_context
    
    # Verify that system state was NOT overridden by memo's prompt injection
    # Initial register should still have 6 items, HID-001 should NOT be released
    assert len(fresh_evidence_register) == 6
    assert "HID-001" not in fresh_evidence_register

# 5. Malformed JSON or an LLM API failure recovers gracefully
def test_malformed_json_or_api_failure_recovery():
    # clean_json_text handles markdown fences
    fenced_json = "```json\n{\"test\": 123}\n```"
    assert clean_json_text(fenced_json) == '{"test": 123}'
    
    # ask_ai_json with no client returns structured fallback without raising exception
    result = ask_ai_json("dummy prompt", api_key="INVALID_KEY", fallback={"status": "fallback_ok"})
    assert "error" in result or result.get("status") == "fallback_ok"

# 6. Insufficient evidence leads to an appropriately cautious conclusion
def test_insufficient_evidence_cautious_conclusion(fresh_evidence_register):
    # Initial register has only EVD-001 through EVD-006 (no HID-003)
    response = ask_investigation_assistant(
        "Who stole the missing 150 units?",
        fresh_evidence_register
    )
    resp_lower = response.lower()
    # Verify cautious conclusion when evidence is incomplete
    is_cautious = any(phrase in resp_lower for phrase in [
        "cannot be", "unproven", "insufficient", "not definitively", "not proven", "uncertain"
    ])
    assert is_cautious, f"Expected cautious language in response, got: {response[:300]}"

# 7. Hidden evidence cannot be accessed before release
def test_hidden_evidence_inaccessible_before_release(fresh_evidence_register):
    assert "HID-001" not in fresh_evidence_register
    assert "HID-002" not in fresh_evidence_register
    assert "HID-003" not in fresh_evidence_register
    
    catalogue = get_hidden_catalogue()
    assert "HID-001" in catalogue
    # Catalogue only displays metadata, does not contain raw_text
    assert "raw_text" not in catalogue["HID-001"]

# 8. A request with a valid ID but missing or trivial justification is rejected
def test_request_missing_justification_rejected(fresh_evidence_register):
    release_history = []
    # Reason < 15 characters
    success, msg = request_hidden_evidence(
        "HID-001",
        "Short reason",
        "What happened?",
        fresh_evidence_register,
        release_history
    )
    assert success is False
    assert "justification is insufficient" in msg
    assert "HID-001" not in fresh_evidence_register

# 9. Released evidence becomes available to subsequent permitted analyses
def test_released_evidence_becomes_available(fresh_evidence_register):
    release_history = []
    success, msg = request_hidden_evidence(
        "HID-001",
        "Need carrier signed proof of delivery to confirm piece count at dock",
        "Did driver deliver 7 or 10 cartons?",
        fresh_evidence_register,
        release_history
    )
    assert success is True
    assert "HID-001" in fresh_evidence_register
    assert fresh_evidence_register["HID-001"]["status"] == "Released upon Request"
    
    # Timeline updates to include HID-001
    timeline = build_timeline(fresh_evidence_register)
    timeline_ids = [item["id"] for item in timeline]
    assert "HID-001" in timeline_ids

# 10. Decision submissions reject invalid evidence references
def test_decision_submission_rejects_invalid_evidence(fresh_evidence_register):
    submission = {
        "conclusion": "The shipment had missing items due to transit discrepancies.",
        "supporting_evidence_ids": ["EVD-001", "EVD-999"],
        "counterevidence_ids": ["EVD-002", "FAKE-001"],
        "confidence_level": "Medium",
        "unresolved_uncertainties": "Carrier driver statements pending.",
        "recommended_action": "Request detailed driver run sheet."
    }
    is_valid, errors, validated_data = validate_submission_inputs(submission, fresh_evidence_register)
    assert is_valid is True
    assert "EVD-001" in validated_data["valid_supporting_ids"]
    assert "EVD-999" in validated_data["invalid_supporting_ids"]
    assert "FAKE-001" in validated_data["invalid_counter_ids"]

# 11. Resubmissions preserve previous attempts
def test_resubmission_preserves_previous_attempts(fresh_evidence_register):
    attempt_history = []
    
    sub1 = {
        "conclusion": "Initial guess that courier lost the 150 units in transit.",
        "valid_supporting_ids": ["EVD-001"],
        "invalid_supporting_ids": [],
        "valid_counter_ids": [],
        "invalid_counter_ids": [],
        "confidence_level": "High",
        "unresolved_uncertainties": "None",
        "recommended_action": "File claim against courier."
    }
    eval1 = evaluate_decision_deterministic(sub1, fresh_evidence_register)
    record_submission_attempt(attempt_history, sub1, eval1, fresh_evidence_register)
    
    assert len(attempt_history) == 1
    assert attempt_history[0]["attempt_number"] == 1
    
    # Second revised attempt
    sub2 = {
        "conclusion": "Revised assessment: 150 units were not received as per GRN-2026-0412 and transit hub weight was 28kg.",
        "valid_supporting_ids": ["EVD-001", "EVD-003", "EVD-004"],
        "invalid_supporting_ids": [],
        "valid_counter_ids": ["EVD-002"],
        "invalid_counter_ids": [],
        "confidence_level": "Medium",
        "unresolved_uncertainties": "Whether supplier failed to load or carrier lost them.",
        "recommended_action": "Request detailed POD and supplier staging audit."
    }
    eval2 = evaluate_decision_deterministic(sub2, fresh_evidence_register)
    record_submission_attempt(attempt_history, sub2, eval2, fresh_evidence_register)
    
    assert len(attempt_history) == 2
    assert attempt_history[0]["attempt_number"] == 1
    assert attempt_history[1]["attempt_number"] == 2
    # Ensure attempt 1 data was NOT overwritten
    assert attempt_history[0]["submission"]["conclusion"] == sub1["conclusion"]
    assert attempt_history[1]["submission"]["conclusion"] == sub2["conclusion"]
    # Attempt 2 should score higher because it cited more valid evidence and calibrated confidence
    assert attempt_history[1]["total_score"] >= attempt_history[0]["total_score"]

# 12. Final report includes source references and unresolved questions
def test_final_report_includes_sources_and_questions(fresh_evidence_register):
    timeline = build_timeline(fresh_evidence_register)
    conflicts = detect_conflicts(fresh_evidence_register)
    report = generate_investigation_report(
        "PO-88421",
        fresh_evidence_register,
        timeline,
        conflicts,
        [],
        []
    )
    assert "EVD-001" in report
    assert "EVD-004" in report
    assert "Evidentiary Contradictions & Material Conflicts" in report
    assert "Residual Uncertainty" in report

# 13. Starting a new case or resetting does not accidentally reuse stale evidence or scores
def test_reset_workflow_isolates_state():
    reg1 = load_initial_evidence_register()
    release_hist1 = []
    # Release HID-001 in session 1
    request_hidden_evidence(
        "HID-001",
        "Investigating carrier handover piece count discrepancy",
        "What piece count was signed for?",
        reg1,
        release_hist1
    )
    assert "HID-001" in reg1
    assert len(release_hist1) == 1
    
    # Simulate Resetting Case
    fresh_reg = load_initial_evidence_register()
    fresh_release_hist = []
    fresh_attempt_hist = []
    
    assert "HID-001" not in fresh_reg
    assert len(fresh_release_hist) == 0
    assert len(fresh_attempt_hist) == 0
    assert len(fresh_reg) == 6

# 14. Citation validator detects invalid citations in assistant text
def test_citation_validator(fresh_evidence_register):
    sample_text = "According to EVD-001 and EVD-004, 350 units arrived. However, EVD-999 and HID-888 say otherwise."
    valid, invalid = validate_citations_in_text(sample_text, fresh_evidence_register)
    assert "EVD-001" in valid
    assert "EVD-004" in valid
    assert "EVD-999" in invalid
    assert "HID-888" in invalid

# 15. Missing evidence files handled gracefully without crashing
def test_missing_evidence_files_handled_gracefully(fresh_evidence_register):
    from evidence import extract_document_text
    missing_res = extract_document_text("data/available_evidence/non_existent_file.pdf")
    assert "[File Not Found:" in missing_res
    
    release_hist = []
    success, msg = request_hidden_evidence(
        "HID-001",
        "Investigating carrier handover piece count discrepancy",
        "What piece count was signed for?",
        fresh_evidence_register,
        release_hist,
        base_dir="data/non_existent_directory"
    )
    assert success is False
    assert "System Error: Physical file" in msg

# 16. Unauthorized confidential record access blocked (duplicate requests, trivial reasons)
def test_unauthorized_confidential_record_access_blocked(fresh_evidence_register):
    release_hist = []
    
    # Empty justification
    s1, m1 = request_hidden_evidence("HID-001", "   ", "Valid question?", fresh_evidence_register, release_hist)
    assert s1 is False
    assert "insufficient" in m1
    
    # Gibberish without sufficient alphabetics
    s2, m2 = request_hidden_evidence("HID-001", "123456789012345", "Valid question?", fresh_evidence_register, release_hist)
    assert s2 is False
    
    # Valid release first
    s3, m3 = request_hidden_evidence(
        "HID-001",
        "Investigating carrier handover piece count discrepancy",
        "What piece count was signed for?",
        fresh_evidence_register,
        release_hist
    )
    assert s3 is True
    assert "HID-001" in fresh_evidence_register
    
    # Duplicate release attempt must be rejected
    s4, m4 = request_hidden_evidence(
        "HID-001",
        "Second request for same document to verify access rules",
        "What was signed for?",
        fresh_evidence_register,
        release_hist
    )
    assert s4 is False
    assert "already released" in m4

# 17. Decision submission with zero valid citations is rejected
def test_submission_with_only_invalid_citations_rejected(fresh_evidence_register):
    sub = {
        "conclusion": "The shipment was stolen in transit based on fake documents.",
        "supporting_evidence_ids": ["EVD-999", "FAKE-DOC-01"],
        "counterevidence_ids": [],
        "confidence_level": "High",
        "unresolved_uncertainties": "None",
        "recommended_action": "File claim against courier."
    }
    is_valid, errors, validated_data = validate_submission_inputs(sub, fresh_evidence_register)
    assert is_valid is False
    assert any("valid, accessible" in err for err in errors)

# 18. Malformed LLM response structures and out-of-bound scores handled safely
def test_malformed_llm_json_structures_fallback_cleanly(fresh_evidence_register):
    from evaluator import evaluate_decision_deterministic
    from llm import clean_json_text
    
    # Test cleaning markdown fences
    raw_markdown = "```json\n{\"scores\": {\"factual_accuracy\": 25}}\n```"
    cleaned = clean_json_text(raw_markdown)
    assert "```" not in cleaned
    
    # Test score bounding: evaluate_decision_deterministic enforces max score limits
    sub = {
        "conclusion": "Analysis of PO-88421 and GRN-2026-0412 confirms 150 units were not inwarded.",
        "confidence_level": "Medium",
        "recommended_action": "Audit carrier proof of delivery and supplier dispatch.",
        "unresolved_uncertainties": "Location of missing units remains unproven.",
        "valid_supporting_ids": ["EVD-001", "EVD-004"],
        "invalid_supporting_ids": ["EVD-999"],
        "valid_counter_ids": ["EVD-002"],
        "invalid_counter_ids": []
    }
    eval_res = evaluate_decision_deterministic(sub, fresh_evidence_register)
    scores = eval_res["criterion_scores"]
    assert 0 <= scores["factual_accuracy"] <= 20
    assert 0 <= scores["supporting_evidence"] <= 20
    assert 0 <= scores["counterevidence_analysis"] <= 15
    assert 0 <= scores["recognition_of_uncertainty"] <= 15
    assert 0 <= scores["reasoning_coherence"] <= 15
    assert 0 <= scores["actionable_next_steps"] <= 15
    assert eval_res["total_score"] == sum(scores.values())

# 19. Clean PDF text extraction without encoding artifacts
def test_clean_pdf_text_extraction_without_encoding_artifacts():
    from evidence import extract_document_text, INITIAL_DOCUMENTS_CONFIG, HIDDEN_CATALOGUE_CONFIG
    import os
    
    for item in INITIAL_DOCUMENTS_CONFIG:
        path = os.path.join("data/available_evidence", item["filename"])
        text = extract_document_text(path)
        assert "■" not in text, f"Found black square placeholder in {item['filename']}"
        assert "\ufffd" not in text, f"Found unicode replacement char in {item['filename']}"
        assert len(text.strip()) > 50
        
    for hid, item in HIDDEN_CATALOGUE_CONFIG.items():
        path = os.path.join("data/hidden_evidence", item["filename"])
        text = extract_document_text(path)
        assert "■" not in text, f"Found black square placeholder in {item['filename']}"
        assert "\ufffd" not in text, f"Found unicode replacement char in {item['filename']}"
        assert len(text.strip()) > 50

# 20. Confidential records are not leaked in unauthorized report
def test_confidential_records_not_leaked_in_unauthorized_report(fresh_evidence_register):
    # Only EVD-001 to EVD-006 are accessible
    timeline = build_timeline(fresh_evidence_register)
    conflicts = detect_conflicts(fresh_evidence_register)
    report = generate_investigation_report(
        "PO-88421",
        fresh_evidence_register,
        timeline,
        conflicts,
        [],
        []
    )
    # The final findings section must NOT cite HID-001, HID-002, or HID-003 before they are released
    findings_section = report.split("## 7. Final Grounded Findings & Limitations")[-1]
    assert "HID-001" not in findings_section
    assert "HID-002" not in findings_section
    assert "HID-003" not in findings_section

# 21. Copilot system context contains complete case facts and platform architecture
def test_copilot_system_context_generation(fresh_evidence_register):
    from copilot import build_copilot_system_context
    ctx = build_copilot_system_context(fresh_evidence_register, [], [], None)
    assert "PO-88421" in ctx
    assert "500 units" in ctx
    assert "350 units" in ctx
    assert "150 units" in ctx
    assert "INR 5,40,000" in ctx
    assert "28.0 kg" in ctx
    assert "EVD-001" in ctx
    assert "HID-001" in ctx
    assert "01 • Case Problem & Executive Analysis" in ctx
    assert "08 • Final Report (.txt)" in ctx


