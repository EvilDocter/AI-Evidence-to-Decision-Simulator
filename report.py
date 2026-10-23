from datetime import datetime

def generate_investigation_report(case_summary, accessible_register, timeline, conflicts, release_history, attempt_history):
    """
    Assembles a comprehensive, auditable forensic investigation report.
    Returns markdown-formatted string with source citations throughout.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    
    # 1. Header & Case Summary
    lines.append("# FORENSIC CASE REPORT: MISSING SHIPMENT INVESTIGATION")
    lines.append(f"**Case Reference:** CASE-2026-SHP-884 | **Report Generated:** {now_str}")
    lines.append("**Investigating Organization:** Enterprise Forensic & Commercial Compliance Unit\n")
    lines.append("---")
    
    lines.append("## 1. Executive Summary & Case Scope")
    lines.append(f"- **Contracted Goods:** 500 units of High-Precision Microcontroller IC-902")
    lines.append(f"- **Contract Value:** INR 18,00,000 (18 Lakh) under Purchase Order PO-88421")
    lines.append(f"- **Involved Parties:**")
    lines.append("  - **Buyer:** Zenith Electronics Ltd. (Warehouse 1, Sector 4, Pune)")
    lines.append("  - **Supplier:** Apex Microtech Pvt. Ltd. (Bangalore)")
    lines.append("  - **Logistics Carrier:** SwiftLogix Express Pvt. Ltd. (Air-Surface Logistics)")
    lines.append(f"- **Dispute Nature:** Supplier invoiced full 500 units; carrier tracking indicated delivered status at an unverified secondary annex; warehouse verified receipt of only 350 units (7 cartons), resulting in an unresolved shortage of 150 units (INR 5,40,000 shortfall).")
    lines.append("")
    
    # 2. Evidence Register
    lines.append("## 2. Accessible Evidence Register & Document Provenance")
    lines.append("| Evidence ID | Document Type | Date | Author / Entity | Declared Qty / Weight | Status |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for eid, doc in accessible_register.items():
        doc_type = doc.get("doc_type", "Document")
        date = doc.get("date", "N/A")
        author = doc.get("author", "N/A")
        qty = doc.get("quantity_claimed", "N/A")
        status = doc.get("status", "Active")
        lines.append(f"| `{eid}` | {doc_type} | {date} | {author} | {qty} | {status} |")
    lines.append("")

    # 3. Chronological Timeline
    lines.append("## 3. Chronological Event Reconstruction")
    if timeline:
        for idx, event in enumerate(timeline, start=1):
            lines.append(f"**{idx}. [{event['date']} {event['time']}] - `{event['id']}` ({event['type']})**")
            lines.append(f"   *Party:* {event['party']}")
            lines.append(f"   *Event:* {event['event']}")
    else:
        lines.append("No timeline events reconstructed.")
    lines.append("")

    # 4. Conflicting Claims & Contradictions
    lines.append("## 4. Evidentiary Contradictions & Material Conflicts")
    if conflicts:
        for idx, c in enumerate(conflicts, start=1):
            eids = ", ".join(f"`{e}`" for e in c["evidence_ids"])
            lines.append(f"### Conflict {idx}: {c['title']} ({eids})")
            lines.append(f"- **Sources in Dispute:** {c['sources']}")
            lines.append(f"- **Claim A:** {c['claim_a']}")
            lines.append(f"- **Claim B:** {c['claim_b']}")
            lines.append(f"- **Analytical Conflict:** {c['why_conflicts']}")
            lines.append(f"- **Residual Uncertainty:** {c['uncertainty']}")
            lines.append(f"- **Targeted Resolution:** {c['resolution_path']}\n")
    else:
        lines.append("No unresolved material conflicts logged.")
    lines.append("")

    # 5. Hidden Evidence Requests & Access Log
    lines.append("## 5. Controlled Evidence Requests & Release Log")
    if release_history:
        lines.append("| Released ID | Document Title | Release Timestamp | Investigator Justification |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for rel in release_history:
            lines.append(f"| `{rel['evidence_id']}` | {rel['title']} | {rel['timestamp']} | {rel['reason']} |")
    else:
        lines.append("No confidential records were requested or released during this investigation.")
    lines.append("")

    # 6. Decision History & Rubric Evaluations
    lines.append("## 6. Investigator Submissions & Revision History")
    if attempt_history:
        for attempt in attempt_history:
            sub = attempt["submission"]
            fb = attempt["evaluation_feedback"]
            crit = attempt["criterion_scores"]
            lines.append(f"### Attempt {attempt['attempt_number']} (Logged: {attempt['timestamp']})")
            lines.append(f"- **Overall Score:** **{attempt['total_score']} / 100**")
            lines.append(f"- **Stated Confidence:** {sub.get('confidence_level')}")
            lines.append(f"- **Supported Evidence IDs:** {', '.join(f'`{e}`' for e in sub.get('valid_supporting_ids', []))}")
            if sub.get("invalid_supporting_ids"):
                lines.append(f"- [FLAGGED] Invalid/Unreleased IDs Cited: {', '.join(sub['invalid_supporting_ids'])}")
            lines.append(f"- **Counterevidence IDs:** {', '.join(f'`{e}`' for e in sub.get('valid_counter_ids', []))}")
            lines.append(f"- **Investigator Conclusion:**\n  > {sub.get('conclusion')}")
            lines.append(f"- **Identified Uncertainties:**\n  > {sub.get('unresolved_uncertainties', 'None noted')}")
            lines.append(f"- **Recommended Action:**\n  > {sub.get('recommended_action')}")
            lines.append("\n**Rubric Breakdown:**")
            for k, val in crit.items():
                lines.append(f"  - *{k.replace('_', ' ').title()}:* {val} pts")
            lines.append(f"- **Key Evaluator Strengths:** {'; '.join(fb.get('strengths', []))}")
            lines.append(f"- **Areas for Improvement:** {'; '.join(fb.get('improvements', []))}")
            lines.append(f"- **Improvement Tip:** {fb.get('investigator_tip', '')}\n")
    else:
        lines.append("No formal decision has been submitted yet.")
    lines.append("")

    # 7. Final Grounded Conclusion & Limitations
    lines.append("## 7. Final Grounded Findings & Limitations")
    if "HID-003" in accessible_register:
        lines.append("- **Conclusive Root Cause:** Apex Microtech internal audit (HID-003) conclusively establishes that 150 units (Cartons #8, #9, #10) were withheld at the Bangalore plant for QA inspection and never loaded onto the courier vehicle.")
        lines.append("- **Financial Impact:** Zenith Electronics was billed INR 18,00,000 for 500 units but received only 350 units. Zenith is contractually owed an immediate credit note of INR 5,40,000.")
        
        delivery_notes = ["The unauthorized redirection email (EVD-005) originated from an external spoofed domain, creating confusion."]
        if "HID-001" in accessible_register and "HID-002" in accessible_register:
            delivery_notes.append("CCTV records (HID-002) and POD receipts (HID-001) verify that carrier delivered only 7 cartons.")
        elif "HID-001" in accessible_register:
            delivery_notes.append("POD receipts (HID-001) verify that carrier delivered only 7 cartons.")
        elif "HID-002" in accessible_register:
            delivery_notes.append("CCTV records (HID-002) verify that carrier offloaded only 7 cartons at the annex dock.")
        lines.append(f"- **Security & Delivery Finding:** {' '.join(delivery_notes)}")
    else:
        lines.append("- **Interim Finding:** Records substantiate that Zenith received only 350 units (EVD-004) and carrier transit scale recorded 28 kg (EVD-003).")
        lines.append("- **Investigative Limitation:** Without origin supplier staging audit records, it cannot be conclusively established whether 150 units were diverted during carrier transit or withheld prior to dispatch.")
        lines.append("- **Cautionary Note:** 'DELIVERED' status on carrier tracking (EVD-003) does NOT verify internal piece counts.")

    lines.append("\n**Report Authentication:** Compiled via Forensic Decision Workspace.")
    return "\n".join(lines)


def generate_investigation_report_txt(case_summary, accessible_register, timeline, conflicts, release_history, attempt_history):
    """
    Assembles a comprehensive, auditable forensic investigation report formatted as clean plain text (.txt).
    Formatted with structured ASCII headers, clear tabular layouts, and source citations throughout.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sep_heavy = "=" * 80
    sep_light = "-" * 80
    
    t = []
    t.append(sep_heavy)
    t.append("              ENTERPRISE COMMERCIAL FORENSIC INVESTIGATION REPORT")
    t.append("                         CHAIN OF CUSTODY DISPUTE AUDIT")
    t.append(sep_heavy)
    t.append(f"Case Reference     : CASE-2026-SHP-884")
    t.append(f"Contract Order Ref : PO-88421 (Purchase Order)")
    t.append(f"Report Generated   : {now_str}")
    t.append(f"Auditing Authority : Commercial Compliance & Forensic Review Unit")
    t.append(f"Classification     : FORMAL WORK PRODUCT / COMMERCIAL LITIGATION GRADE")
    t.append(sep_heavy)
    t.append("")
    
    # 1. Executive Summary
    t.append("1. EXECUTIVE DISPUTE DEFINITION & CONTRACTUAL SCOPE")
    t.append(sep_light)
    t.append("  * Contracted Goods    : 500 units High-Precision Microcontroller IC-902")
    t.append("  * Contract Value      : INR 18,00,000 (18.0 Lakhs) under PO-88421")
    t.append("  * Disputed Quantity   : 150 units short (3 full cartons @ 50 pcs)")
    t.append("  * Disputed Value      : INR 5,40,000 unverified commercial billing")
    t.append("  * Contracted Terms    : DDP Warehouse 1, Sector 4, MIDC Bhosari, Pune")
    t.append("")
    t.append("  PARTIES INVOLVED:")
    t.append("    [Buyer]    Zenith Electronics Ltd. (Pune, Maharashtra)")
    t.append("    [Supplier] Apex Microtech Pvt. Ltd. (Bangalore, Karnataka)")
    t.append("    [Carrier]  SwiftLogix Express Pvt. Ltd. (Air-Surface Logistics)")
    t.append("")
    t.append("  CORE DISPUTE STATEMENT:")
    t.append("    Supplier Apex invoiced Zenith for 500 units (DISP-6619) claiming complete")
    t.append("    handover to carrier SwiftLogix under Waybill SLX-904821. Carrier tracking")
    t.append("    portal marked status 'DELIVERED' at an unverified secondary annex gate signed")
    t.append("    by a security guard. Zenith Warehouse 1 storekeepers inward-verified only")
    t.append("    350 units (7 cartons), revealing a deficit of 150 units (INR 5,40,000).")
    t.append("    A rerouting directive from a spoofed domain diverted the consignment.")
    t.append("")
    
    # 2. Evidence Register
    t.append("2. REGISTERED BUSINESS EVIDENCE & DOCUMENT PROVENANCE")
    t.append(sep_light)
    t.append(f"{'EVID ID':<10} {'DOCUMENT TYPE':<26} {'DATE':<12} {'ORIGINATOR':<20} {'CLAIMED QTY':<12}")
    t.append(sep_light)
    for eid, doc in accessible_register.items():
        doc_type = doc.get("doc_type", "Document")[:24]
        date = doc.get("date", "N/A")[:10]
        author = doc.get("author", "N/A")[:18]
        qty = doc.get("quantity_claimed", "N/A")[:10]
        t.append(f"{eid:<10} {doc_type:<26} {date:<12} {author:<20} {qty:<12}")
    t.append(sep_light)
    t.append("")
    
    # 3. Chronological Sequence
    t.append("3. RECONSTRUCTED CHRONOLOGICAL SEQUENCE & CUSTODY TRACKING")
    t.append(sep_light)
    if timeline:
        for idx, event in enumerate(timeline, start=1):
            t.append(f"[{idx:02d}] {event['date']} {event['time']} IST | Ref: {event['id']} ({event.get('type', 'Event')})")
            t.append(f"     Title      : {event.get('step_title', event.get('type', 'Milestone'))}")
            t.append(f"     Custodian  : {event.get('party', 'N/A')}")
            t.append(f"     Location   : {event.get('location', 'N/A')}")
            t.append(f"     Signatory  : {event.get('signatory', 'N/A')}")
            t.append(f"     Reconciled : Declared: {event.get('declared_qty', 'N/A')} | Verified: {event.get('verified_qty', 'N/A')}")
            t.append(f"     Narrative  : {event.get('event')}")
            if event.get("discrepancy") and event.get("discrepancy") != "None":
                t.append(f"     ANOMALY    : {event.get('discrepancy')}")
            t.append("")
    else:
        t.append("  No timeline events reconstructed.")
        t.append("")
        
    # 4. Conflicts
    t.append("4. MATERIAL EVIDENTIARY CONTRADICTIONS & UNRESOLVED DISCREPANCIES")
    t.append(sep_light)
    if conflicts:
        for idx, c in enumerate(conflicts, start=1):
            eids = ", ".join(c["evidence_ids"])
            t.append(f"Conflict #{idx}: {c['title']} [{eids}]")
            t.append(f"  Sources in Dispute : {c['sources']}")
            t.append(f"  Assertion A        : {c['claim_a']}")
            t.append(f"  Assertion B        : {c['claim_b']}")
            t.append(f"  Forensic Conflict  : {c['why_conflicts']}")
            t.append(f"  Residual Anomaly   : {c['uncertainty']}")
            t.append(f"  Resolution Path    : {c['resolution_path']}")
            t.append("")
    else:
        t.append("  No unresolved material conflicts logged.")
        t.append("")
        
    # 5. Vault Access Log
    t.append("5. CONTROLLED CONFIDENTIAL VAULT ACCESS AUDIT LOG")
    t.append(sep_light)
    if release_history:
        for rel in release_history:
            t.append(f"  * Released ID    : {rel['evidence_id']} - {rel['title']}")
            t.append(f"    Timestamp      : {rel['timestamp']}")
            t.append(f"    Justification  : {rel['reason']}")
            t.append("")
    else:
        t.append("  No confidential vault records were unlocked during this session.")
        t.append("")
        
    # 6. Evaluation Submissions
    t.append("6. INVESTIGATIVE DETERMINATIONS & RUBRIC EVALUATION PROGRESSION")
    t.append(sep_light)
    if attempt_history:
        for attempt in attempt_history:
            sub = attempt["submission"]
            crit = attempt["criterion_scores"]
            fb = attempt["evaluation_feedback"]
            t.append(f"Attempt #{attempt['attempt_number']} (Timestamp: {attempt['timestamp']})")
            t.append(f"  Overall Score   : {attempt['total_score']} / 100")
            t.append(f"  Confidence      : {sub.get('confidence_level')}")
            t.append(f"  Citations Valid : {', '.join(sub.get('valid_supporting_ids', []))}")
            t.append(f"  Conclusion      : {sub.get('conclusion')}")
            t.append(f"  Action Proposed : {sub.get('recommended_action')}")
            t.append("  Criterion Scores:")
            for k, val in crit.items():
                t.append(f"    - {k.replace('_', ' ').title():<32} : {val} pts")
            t.append(f"  Key Strengths   : {'; '.join(fb.get('strengths', []))}")
            t.append(f"  Revision Notes  : {'; '.join(fb.get('improvements', []))}")
            t.append("")
    else:
        t.append("  No formal determination attempts scored yet.")
        t.append("")
        
    # 7. Final Findings
    t.append("7. FINAL GROUNDED FINDINGS, LIABILITY ALLOCATION & LIMITATIONS")
    t.append(sep_light)
    if "HID-003" in accessible_register:
        t.append("  [DEFINITIVE ROOT CAUSE IDENTIFIED]")
        t.append("  * Apex Microtech Internal QA Memo (HID-003) conclusively establishes that")
        t.append("    Cartons #8, #9, and #10 (150 units of IC-902) were withheld on Staging Pallet B-4")
        t.append("    at the Bangalore factory for batch re-testing and were NEVER loaded onto the")
        t.append("    courier vehicle. Invoice DISP-6619 was printed prematurely by dispatch.")
        t.append("")
        t.append("  * Carrier SwiftLogix received only 7 cartons (28.0 kg) at Bangalore origin, as")
        t.append("    corroborated by the Pune transit weighbridge scale log (EVD-003).")
        t.append("")
        t.append("  * Secondary Annex Security signed courier POD run sheet (HID-001) with explicit")
        t.append("    written reservation: 'Received 7 cartons only. 3 cartons short.'")
        t.append("")
        t.append("  * High-definition CCTV audit (HID-002) confirms driver offloaded exactly 7 cartons.")
        t.append("")
        t.append("  [LIABILITY DETERMINATION]")
        t.append("  * 100% Supplier Liability: Apex Microtech is solely responsible for the shortage.")
        t.append("  * Financial Settlement : Zenith Electronics is entitled to an immediate credit note")
        t.append("    of INR 5,40,000 plus reimbursement of excess freight and statutory interest.")
    else:
        t.append("  [INTERIM FINDINGS PENDING FINAL VAULT DISCLOSURE]")
        t.append("  * Records establish that Zenith physically received only 350 units (EVD-004).")
        t.append("  * Carrier inward transit hub scale recorded 28.0 kg (EVD-003), proving that the")
        t.append("    deficit of 12.0 kg existed before arrival at the Pune regional sort facility.")
        t.append("  * Tracking status 'DELIVERED' (EVD-003) is generic and does NOT prove piece count.")
        t.append("  * Requesting supplier internal QA audit records (HID-003) is required to establish")
        t.append("    conclusive supplier root cause.")
    t.append("")
    t.append(sep_heavy)
    t.append("END OF FORMAL REPORT -- AUTHENTICATED AUDIT DOSSIER Ref: CASE-2026-SHP-884")
    t.append(sep_heavy)
    return "\n".join(t)

