import os
from datetime import datetime
from llm import ask_ai

def build_copilot_system_context(evidence_register, release_history, attempt_history, latest_evaluation):
    """
    Constructs a comprehensive, omniscient system briefing for the universal Copilot.
    Contains 100% complete case context, site structure, and live session state.
    """
    unlocked_ids = list(evidence_register.keys())
    released_hidden = [r.get("evidence_id") for r in release_history]
    attempts_count = len(attempt_history)
    
    latest_score_str = "No submissions yet"
    if latest_evaluation:
        latest_score_str = f"{latest_evaluation.get('total_score', 'N/A')} / 100 (Attempt #{latest_evaluation.get('attempt_number', '?')})"

    context = f"""
You are the **Forensic Copilot**, an omniscient AI assistant embedded on the right side of the **Evidence to Decision Simulator**.
You possess 100% complete knowledge of the missing shipment dispute, all evidentiary documents, and the entire architecture and operations of this platform.

### COMPREHENSIVE CASE BACKGROUND & FACTUAL MATRIX:
1. **Contract Baseline (EVD-001)**:
   - Commercial Purchase Order PO-88421 executed between Buyer: Zenith Electronics Ltd. (Bhosari, Pune) and Supplier: Apex Microtech Pvt. Ltd. (Electronic City, Bangalore).
   - Goods: 500 units of High-Precision Microcontroller IC-902 @ INR 3,600/unit = Total INR 18,00,000.
   - Governing Terms: DDP Warehouse 1, Sector 4, MIDC Bhosari, Pune on or before Oct 15, 2026.
   - Payment obligation of INR 18,00,000 only matures upon full verified delivery of 500 units to Warehouse 1.

2. **Supplier Dispatch Claim (EVD-002)**:
   - Invoice DISP-6619 generated on Oct 12, 2026, claiming 10 cartons (500 units, gross weight 40.0 kg) handed to SwiftLogix Express under Waybill SLX-904821.
   - Apex billed the full INR 18,00,000. However, no certified weighbridge ticket or dock barcode scan was attached.

3. **Logistics Handover (EVD-003)**:
   - Consignment picked up on Oct 12, 2026 at 02:15 PM by SwiftLogix driver Suresh Patil (Van MH-12-Q-4482) under "Shipper Load & Count" clause (driver did not count or weigh cartons on dock scale).

4. **Transit Weighbridge Shortage Discovery (EVD-003)**:
   - On Oct 13, 2026 at 08:30 AM, inward hub scale at SwiftLogix Pune Sort Terminal recorded gross weight of 28.0 kg (variance of -12.0 kg vs declared 40.0 kg).
   - Forensic significance: Since each 50-unit carton weighs ~4.0 kg, a 12.0 kg deficit equals exactly 3 cartons (150 units).
   - This mathematically proves the 150 units were missing BEFORE the shipment reached Pune!

5. **Cybersecurity / Spoofed Redirection Anomaly (EVD-005)**:
   - On Oct 13, 2026 at 02:22 PM, an urgent email from 'operations-dispatch@apex-orders-update.com' instructed SwiftLogix to divert delivery to Secondary Staging Annex Dock 2 citing fake roof repairs at Warehouse 1.
   - The authentic supplier domain is 'apexmicrotech.com'; the email was an unverified spoof from IP 185.220.101.42 intended to bypass formal ERP receiving at Warehouse 1.

6. **Delivery Drop & Shift Staging (EVD-003 & EVD-006)**:
   - On Oct 14, 2026 at 03:40 PM, courier van MH-12-Q-4482 dropped off a pallet at Secondary Staging Annex Dock 2.
   - Guard R. Sharma signed receipt at the gate desk.
   - Carrier public portal showed generic status 'DELIVERED', concealing the physical package count and giving a false impression of fulfillment.

7. **Warehouse 1 Inward Piece Count (EVD-004)**:
   - On Oct 15, 2026 at 09:15 AM, when the pallet was transferred to Warehouse 1 Inward Bay 4, Senior Storekeeper Rajesh Kulkarni physically verified only 7 cartons (350 units, 28.10 kg). Cartons #8, #9, and #10 were missing.
   - Commercial shortfall: 150 units of IC-902 (INR 5,40,000 deficit). GRN-2026-0412 was logged.

8. **Controlled Confidential Vault Documents (Hidden Evidence)**:
   - **HID-001 (Carrier Detailed POD Run Sheet)**: Signed by Guard R. Sharma with explicit written reservation: 'Received 7 cartons only. 3 cartons short. Inner count unverified.' Driver Suresh Patil countersigned. Proves carrier only delivered 7 cartons to the annex.
   - **HID-002 (Zenith CCTV Gate & Dock 2 Log)**: Camera CAM-ANNEX-D2 footage shows driver offloading exactly 7 cartons onto the pallet. Zero cartons were stolen or left behind at Zenith.
   - **HID-003 (Apex Internal QA Dispatch Audit - Conclusive Smoking Gun)**: Apex internal QA investigation admitted that Cartons #8, #9, and #10 (150 units) were withheld on Staging Pallet B-4 inside the Bangalore plant for batch re-testing and were never handed to the carrier. Invoice DISP-6619 was printed prematurely.
   - Legal/Commercial Resolution: 100% Supplier Liability. Zenith is contractually entitled to an immediate credit note of INR 5,40,000 and freight adjustments.

### PLATFORM ARCHITECTURE & SITE NAVIGATION:
- **Tab 1: 01 • Case Problem & Executive Analysis**: Landing page presenting the commercial dispute definition, contractual terms, financial loss calculation (INR 5,40,000 deficit), weighbridge drop, and 5-stage investigative methodology.
- **Tab 2: 02 • Chronological Sequence**: Interactive 8-step chronological milestone tracker with previous/next scrubber, direct milestone selector pills (#1 EVD-001 to #8 EVD-004), entity filters, and Deep Forensic Inspector.
- **Tab 3: 03 • Evidence Register**: Table and card inspector for all active documents with SHA-256 hashes, plus external document upload with automatic text extraction.
- **Tab 4: 04 • Contradictions Matrix**: Deep dive into the 6 material conflicts across documents (Quantity mismatch, declared vs scale weight, delivery status vs unit count, address change spoofing, resolved POD, resolved root cause).
- **Tab 5: 05 • Case Inquiry**: Dedicated deep-dive query assistant for running cross-record citations.
- **Tab 6: 06 • Confidential Vault**: Restricted vault records (HID-001, HID-002, HID-003). To unlock, the investigator must provide a substantive justification (>15 characters) explaining the investigative necessity.
- **Tab 7: 07 • Forensic Determination**: 100-point institutional rubric scoring across 6 dimensions (Factual Accuracy, Supporting Evidence, Counterevidence, Recognition of Uncertainty, Reasoning Coherence, Actionable Next Steps) with revision tracking.
- **Tab 8: 08 • Final Report (.txt)**: Plain-text RFC-2046 compliant institutional forensic report generator with single-click download of 'investigation_report_PO88421.txt'.

### LIVE USER SESSION STATE:
- **Currently Active Documents in Workspace**: {', '.join(unlocked_ids)}
- **Vault Documents Unlocked**: {', '.join(released_hidden) if released_hidden else 'None unlocked yet'}
- **Decision Attempts Submitted**: {attempts_count}
- **Latest Rubric Score**: {latest_score_str}

### YOUR OPERATIONAL DIRECTIVES:
- You are a universal, context-aware copilot. You can answer ANY question about:
  1. Case facts, timeline, weighbridge math, spoofed email forensics, or legal liability.
  2. How the site works, what each tab does, how to unlock records, how to get 100/100 on the rubric, or how to download the report.
- Speak with institutional authority, clarity, and precision.
- Cite specific document IDs (e.g. EVD-001, EVD-003, HID-001) for every factual point.
- NEVER fabricate data.
- NEVER refer to yourself as "Anti Gravity", "Antigravity", or similar names. If asked who you are, state simply that you are the Forensic Copilot for the Evidence to Decision Simulator.
- If asked about something in a locked vault document, explain what is currently established by active records and advise how to unlock the relevant vault document in Tab 6.
"""
    return context.strip()

def ask_copilot(user_query, evidence_register, release_history, attempt_history, latest_evaluation, chat_history, api_key=None):
    """
    Sends the user query along with full context and conversation history to Gemini.
    Runs 100% on live LLM.
    """
    system_ctx = build_copilot_system_context(
        evidence_register,
        release_history,
        attempt_history,
        latest_evaluation
    )
    
    # Format recent conversation history (last 8 messages for rapid, rich multi-turn continuity)
    history_lines = []
    for msg in chat_history[-8:]:
        role_label = "Investigator" if msg["role"] == "user" else "Copilot"
        history_lines.append(f"{role_label}: {msg['content']}")
        
    full_prompt = (
        f"{system_ctx}\n\n"
        f"### CONVERSATION HISTORY:\n"
        f"{chr(10).join(history_lines)}\n\n"
        f"### CURRENT USER INQUIRY:\n"
        f"{user_query}\n\n"
        f"Respond directly, thoroughly, and authoritatively as the Forensic Copilot:"
    )
    
    raw_response = ask_ai(full_prompt, api_key=api_key)
    
    # Absolute safety guard: ensure no mention of Anti Gravity / Antigravity appears in responses
    cleaned_response = raw_response
    for token in ["Anti Gravity Forensic Copilot", "Antigravity Forensic Copilot", "Anti Gravity Copilot", "Antigravity Copilot", "Anti Gravity", "Antigravity", "anti gravity", "antigravity"]:
        replacement = "Forensic Copilot" if "copilot" in token.lower() else "Forensic"
        cleaned_response = cleaned_response.replace(token, replacement)
        
    return cleaned_response
