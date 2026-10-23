import json
from datetime import datetime
from llm import ask_ai_json

RUBRIC_CRITERIA = {
    "factual_accuracy": {
        "title": "Factual Accuracy",
        "max_points": 20,
        "description": "Conclusion adheres strictly to verified records; distinguishes claims from established facts; avoids unfounded speculation."
    },
    "supporting_evidence": {
        "title": "Supporting Evidence Utilization",
        "max_points": 20,
        "description": "Appropriate citation of valid, accessible evidence IDs directly substantiating the claims."
    },
    "counterevidence_analysis": {
        "title": "Counterevidence & Discrepancy Analysis",
        "max_points": 15,
        "description": "Explicit consideration of conflicting records (e.g. supplier dispatch vs warehouse GRN, transit scale weights)."
    },
    "recognition_of_uncertainty": {
        "title": "Recognition of Uncertainty & Restraint",
        "max_points": 15,
        "description": "Avoids unjustified certainty; acknowledges gaps in the record; states when evidence is insufficient."
    },
    "reasoning_coherence": {
        "title": "Quality of Reasoning & Coherence",
        "max_points": 15,
        "description": "Logical deduction from evidence to conclusion without logical fallacies or unsupported jumps."
    },
    "actionable_next_steps": {
        "title": "Actionability of Next Steps",
        "max_points": 15,
        "description": "Proportional, realistic forensic, commercial, or audit actions to resolve remaining questions."
    }
}

def validate_submission_inputs(submission, accessible_register):
    """
    Validates submission fields and checks evidence IDs against accessible register.
    Returns (is_valid, validation_errors, validated_data).
    """
    errors = []
    conclusion = (submission.get("conclusion") or "").strip()
    recommendation = (submission.get("recommended_action") or "").strip()
    confidence = submission.get("confidence_level", "Medium")
    uncertainties = (submission.get("unresolved_uncertainties") or "").strip()
    
    if len(conclusion) < 20:
        errors.append("Conclusion must be at least 20 characters explaining your assessment.")
        
    if len(recommendation) < 15:
        errors.append("Recommended next action must be at least 15 characters.")
        
    # Check supporting evidence IDs
    raw_support = submission.get("supporting_evidence_ids", [])
    valid_support = []
    invalid_support = []
    for eid in raw_support:
        cleaned = eid.strip().upper()
        if not cleaned:
            continue
        if cleaned in accessible_register:
            valid_support.append(cleaned)
        else:
            invalid_support.append(cleaned)
            
    # Check counterevidence IDs
    raw_counter = submission.get("counterevidence_ids", [])
    valid_counter = []
    invalid_counter = []
    for eid in raw_counter:
        cleaned = eid.strip().upper()
        if not cleaned:
            continue
        if cleaned in accessible_register:
            valid_counter.append(cleaned)
        else:
            invalid_counter.append(cleaned)
            
    if not valid_support:
        errors.append("At least one valid, accessible supporting evidence record must be cited.")
        
    is_valid = len(errors) == 0
    validated_data = {
        "conclusion": conclusion,
        "confidence_level": confidence,
        "recommended_action": recommendation,
        "unresolved_uncertainties": uncertainties,
        "valid_supporting_ids": valid_support,
        "invalid_supporting_ids": invalid_support,
        "valid_counter_ids": valid_counter,
        "invalid_counter_ids": invalid_counter
    }
    return is_valid, errors, validated_data

def evaluate_decision_deterministic(validated_data, accessible_register):
    """
    Deterministic rule-based evaluator providing exact, objective rubric scoring.
    Used for reliable evaluation and as a fallback if LLM is unavailable.
    """
    scores = {}
    strengths = []
    gaps = []
    tips = []
    
    conc = validated_data["conclusion"].lower()
    rec = validated_data["recommended_action"].lower()
    unc = validated_data["unresolved_uncertainties"].lower()
    valid_sup = validated_data["valid_supporting_ids"]
    invalid_sup = validated_data["invalid_supporting_ids"]
    valid_cnt = validated_data["valid_counter_ids"]
    invalid_cnt = validated_data["invalid_counter_ids"]
    confidence = validated_data["confidence_level"]
    
    has_hid1 = "HID-001" in accessible_register
    has_hid2 = "HID-002" in accessible_register
    has_hid3 = "HID-003" in accessible_register

    # 1. Factual Accuracy (Max 20)
    acc_score = 14
    if "delivered" in conc and "500" in conc and not ("short" in conc or "350" in conc or "missing" in conc):
        acc_score = 4
        gaps.append("Inaccurately treated courier delivery status as proof of 500 units delivered, ignoring GRN shortage.")
    elif "350" in conc or "150" in conc or "shortage" in conc or "missing" in conc:
        acc_score = 18
        strengths.append("Correctly recognized the 150-unit physical shortfall between supplier dispatch claim and warehouse inward.")
        
    if has_hid3 and ("qa" in conc or "withheld" in conc or "bangalore" in conc or "pallet" in conc):
        acc_score = 20
        strengths.append("Accurately identified root cause from supplier QA audit: units were withheld at Bangalore staging.")
    scores["factual_accuracy"] = acc_score

    # 2. Supporting Evidence Utilization (Max 20)
    sup_score = 10
    if len(valid_sup) >= 2:
        sup_score = 16
        strengths.append(f"Cited {len(valid_sup)} verified accessible evidence sources: {', '.join(valid_sup)}.")
    elif len(valid_sup) == 1:
        sup_score = 12
        
    if invalid_sup:
        sup_score = max(0, sup_score - (len(invalid_sup) * 5))
        gaps.append(f"Cited invalid or unreleased evidence IDs: {', '.join(invalid_sup)}.")
        tips.append("Only cite evidence records that have been formally released in your workspace register.")
    elif len(valid_sup) >= 3:
        sup_score = 20
    scores["supporting_evidence"] = min(20, max(0, sup_score))

    # 3. Counterevidence Analysis (Max 15)
    cnt_score = 8
    if valid_cnt:
        cnt_score = 13
        strengths.append(f"Actively examined counterevidence and discrepancies: {', '.join(valid_cnt)}.")
    if invalid_cnt:
        cnt_score = max(0, cnt_score - 4)
        gaps.append(f"Referenced invalid counterevidence IDs: {', '.join(invalid_cnt)}.")
    if ("weight" in conc or "28" in conc or "40" in conc or "email" in conc or "annex" in conc or "conflict" in conc):
        cnt_score = min(15, cnt_score + 2)
    scores["counterevidence_analysis"] = min(15, max(0, cnt_score))

    # 4. Recognition of Uncertainty (Max 15)
    unc_score = 9
    if not has_hid3 and confidence == "High" and ("stole" in conc or "theft" in conc):
        unc_score = 5
        gaps.append("Displayed unjustified high confidence and alleged theft without definitive supplier dispatch audit records.")
        tips.append("When core evidence remains unverified, maintain Medium or Low confidence and state the uncertainty.")
    elif not has_hid3 and (confidence in ["Low", "Medium"] or len(unc) > 15):
        unc_score = 14
        strengths.append("Appropriately acknowledged unresolved uncertainties regarding the location of missing cargo.")
    elif has_hid3:
        unc_score = 15
        strengths.append("Well-calibrated certainty supported by conclusive confidential audit evidence.")
    scores["recognition_of_uncertainty"] = min(15, max(0, unc_score))

    # 5. Quality of Reasoning & Coherence (Max 15)
    reas_score = 11
    if ("weight" in conc or "discrepancy" in conc or "disclaimer" in conc or "shortage" in conc):
        reas_score = 14
        strengths.append("Demonstrated coherent forensic reasoning linking document facts.")
    if len(gaps) > 2:
        reas_score = max(5, reas_score - 3)
    scores["reasoning_coherence"] = min(15, max(0, reas_score))

    # 6. Actionability of Next Steps (Max 15)
    act_score = 10
    if len(rec) >= 25:
        act_score = 13
        strengths.append("Proposed concrete, actionable investigative follow-ups.")
    if "credit" in rec or "audit" in rec or "pod" in rec or "cctv" in rec or "vendor" in rec:
        act_score = 15
    scores["actionable_next_steps"] = min(15, max(0, act_score))

    # Calculate total in Python
    total_score = sum(scores.values())
    
    return {
        "criterion_scores": scores,
        "total_score": round(total_score, 1),
        "strengths": strengths if strengths else ["Basic submission format completed."],
        "improvements": gaps if gaps else ["Consider requesting additional records to verify initial assumptions."],
        "investigator_tip": tips[0] if tips else "Always reconcile physical piece receipts with transit hub scale weights before concluding theft."
    }

def evaluate_decision_with_llm(submission_data, accessible_register, api_key=None):
    """
    Evaluates investigator decision using 100% live structured JSON from Gemini.
    Zero hardcoded keyword scores. Python validates bounds and applies citation penalties.
    """
    prompt = f"""
You are an institutional forensic assessment evaluator.
Evaluate the investigator's submitted findings against the 6 rubric criteria below.

RUBRIC CRITERIA:
1. factual_accuracy (0 to 20): Adherence to verified records vs claims. Courier delivery does NOT prove 500 units arrived.
2. supporting_evidence (0 to 20): Use of valid accessible evidence IDs: {list(accessible_register.keys())}.
3. counterevidence_analysis (0 to 15): Identification of contradictory data (weight, PO vs GRN, address change).
4. recognition_of_uncertainty (0 to 15): Modesty and acknowledgment of missing facts. Low/Medium confidence when evidence is incomplete.
5. reasoning_coherence (0 to 15): Sound logical deduction without unjustified accusations.
6. actionable_next_steps (0 to 15): Practical follow-up actions (audits, credit notes, manifests).

SUBMISSION:
Conclusion: {submission_data['conclusion']}
Confidence Level: {submission_data['confidence_level']}
Supporting Evidence IDs: {submission_data['valid_supporting_ids']} (Invalid submitted: {submission_data['invalid_supporting_ids']})
Counterevidence IDs: {submission_data['valid_counter_ids']} (Invalid submitted: {submission_data['invalid_counter_ids']})
Unresolved Uncertainties: {submission_data['unresolved_uncertainties']}
Recommended Action: {submission_data['recommended_action']}

ACCESSIBLE EVIDENCE IN CASE:
{list(accessible_register.keys())}

Return JSON with exactly these keys:
{{
  "scores": {{
    "factual_accuracy": <number 0-20>,
    "supporting_evidence": <number 0-20>,
    "counterevidence_analysis": <number 0-15>,
    "recognition_of_uncertainty": <number 0-15>,
    "reasoning_coherence": <number 0-15>,
    "actionable_next_steps": <number 0-15>
  }},
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "investigator_tip": "..."
}}
"""
    result = ask_ai_json(prompt, api_key=api_key, fallback=None)
    
    if not result or "error" in result or "scores" not in result or not isinstance(result.get("scores"), dict):
        err_msg = result.get("message") if isinstance(result, dict) else "Model output could not be parsed."
        raise RuntimeError(f"Live AI Evaluation Error: {err_msg}")
        
    raw_scores = result["scores"]
    validated_scores = {}
    
    # Enforce strict score bounds in Python
    for key, spec in RUBRIC_CRITERIA.items():
        max_p = spec["max_points"]
        val = raw_scores.get(key, 0.0)
        try:
            val = float(val)
            val = max(0.0, min(float(max_p), val))
        except (ValueError, TypeError):
            val = 0.0
        validated_scores[key] = round(val, 1)
        
    # Apply Python penalties if invalid citations exist
    if submission_data["invalid_supporting_ids"]:
        penalty = len(submission_data["invalid_supporting_ids"]) * 4.0
        validated_scores["supporting_evidence"] = max(0.0, validated_scores["supporting_evidence"] - penalty)
        
    total_score = round(sum(validated_scores.values()), 1)
    
    return {
        "criterion_scores": validated_scores,
        "total_score": total_score,
        "strengths": result.get("strengths", ["Live AI identified verified analysis adherence."]),
        "improvements": result.get("improvements", ["Expand cross-referencing with weighbridge telemetry."]),
        "investigator_tip": result.get("investigator_tip", "Always reconcile piece counts with verified transit scale tickets.")
    }

def record_submission_attempt(attempt_history, submission_data, evaluation_result, accessible_register):
    """
    Appends a complete submission record to attempt history for adaptive retry tracking.
    """
    attempt_num = len(attempt_history) + 1
    record = {
        "attempt_number": attempt_num,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "submission": submission_data,
        "criterion_scores": evaluation_result["criterion_scores"],
        "total_score": evaluation_result["total_score"],
        "evaluation_feedback": evaluation_result,
        "accessible_evidence_at_submission": list(accessible_register.keys())
    }
    attempt_history.append(record)
    return record
