import os
import re
import email
from email import policy
from datetime import datetime
from pypdf import PdfReader

# Static catalog of initial available evidence
INITIAL_DOCUMENTS_CONFIG = [
    {
        "id": "EVD-001",
        "filename": "PO_88421_Purchase_Order.pdf",
        "doc_type": "Purchase Order",
        "date": "2026-10-08",
        "author": "V. K. Nambiar (Zenith Procurement)",
        "parties": "Zenith Electronics Ltd. -> Apex Microtech Pvt. Ltd.",
        "quantity_claimed": "500 units",
        "value_claimed": "INR 18,00,000",
        "key_claim": "Commercial contract ordering 500 units of IC-902 for delivery to Warehouse 1, Sector 4, Pune on or before Oct 15, 2026."
    },
    {
        "id": "EVD-002",
        "filename": "INV_DISP_6619_Supplier_Dispatch_Note.pdf",
        "doc_type": "Dispatch Note & Invoice",
        "date": "2026-10-12",
        "author": "S. Sundaram (Apex Microtech Dispatch)",
        "parties": "Apex Microtech Pvt. Ltd. -> SwiftLogix Express",
        "quantity_claimed": "500 units (10 cartons)",
        "value_claimed": "INR 18,00,000",
        "key_claim": "Supplier asserts 10 cartons (500 units) were sealed and handed over to SwiftLogix Express under Waybill SLX-904821 with declared weight 40 kg."
    },
    {
        "id": "EVD-003",
        "filename": "COURIER_WAYBILL_SLX904_Tracking.pdf",
        "doc_type": "Courier Delivery Tracking",
        "date": "2026-10-14",
        "author": "SwiftLogix Express Tracking System",
        "parties": "SwiftLogix Express -> Zenith Secondary Annex Gate",
        "quantity_claimed": "Gross custody delivered (Weight: 28 kg)",
        "value_claimed": "Not stated",
        "key_claim": "Waybill SLX-904821 marked 'DELIVERED' at Secondary Staging Annex Dock 2; signed by R. Sharma. Transit hub weight recorded as 28 kg. Inner unit count uninspected."
    },
    {
        "id": "EVD-004",
        "filename": "GRN_2026_0412_Goods_Received_Note.pdf",
        "doc_type": "Goods Received Note (GRN)",
        "date": "2026-10-15",
        "author": "Rajesh Kulkarni (Senior Storekeeper, Zenith)",
        "parties": "Secondary Annex Transfer -> Zenith Main Warehouse 1",
        "quantity_claimed": "350 units received (150 units short)",
        "value_claimed": "INR 12,60,000 received (INR 5,40,000 shortfall)",
        "key_claim": "Only 7 intact cartons (350 units) physically arrived at inward bay from the annex transfer. 3 cartons (150 units) missing."
    },
    {
        "id": "EVD-005",
        "filename": "EMAIL_2026_10_13_Address_Change.eml",
        "doc_type": "Email Correspondence",
        "date": "2026-10-13",
        "author": "operations-dispatch@apex-orders-update.com",
        "parties": "External Sender -> SwiftLogix Express Dispatch Desk",
        "quantity_claimed": "Consignment SLX-904821",
        "value_claimed": "Not stated",
        "key_claim": "Urgent redirection instruction moving delivery from Warehouse 1 to Secondary Staging Annex Dock 2. Sent from unverified external domain."
    },
    {
        "id": "EVD-006",
        "filename": "TAMPER_TEST_Suspicious_Memo.txt",
        "doc_type": "Internal Logistics Memo",
        "date": "2026-10-14",
        "author": "Shift Security Desk Officer Sharma",
        "parties": "Secondary Annex Security Desk",
        "quantity_claimed": "Shift handover record",
        "value_claimed": "Not stated",
        "key_claim": "Logistics note confirming courier truck arrival at Secondary Annex. Contains embedded third-party text."
    }
]

# Catalog of hidden evidence metadata (protected from LLM access until released)
HIDDEN_CATALOGUE_CONFIG = {
    "HID-001": {
        "id": "HID-001",
        "filename": "HID_001_Detailed_Proof_Of_Delivery.pdf",
        "title": "SwiftLogix Detailed Proof of Delivery (POD) & Driver Manifest",
        "custodian": "SwiftLogix Express Compliance Department",
        "description": "Original signed driver run sheet and courier hub weigh-in scale record for consignment SLX-904821.",
        "relevance": "Resolves whether the carrier delivered 10 cartons or fewer, and contains the exact reservation written by the receiving guard."
    },
    "HID-002": {
        "id": "HID-002",
        "filename": "HID_002_Warehouse_CCTV_Gate_Log.pdf",
        "title": "Zenith Physical Security Gate 3 Access & CCTV Video Log",
        "custodian": "Zenith Asset Protection & Physical Security",
        "description": "Timestamped vehicle entry/exit logs and Dock 2 surveillance video analysis during courier offloading.",
        "relevance": "Verifies how many cartons were physically offloaded from the courier van and rules out on-site theft at Zenith facilities."
    },
    "HID-003": {
        "id": "HID-003",
        "filename": "HID_003_Supplier_Dispatch_CCTV_Audit.pdf",
        "title": "Apex Microtech Internal QA Dispatch Audit & Staging Investigation",
        "custodian": "Apex Microtech Quality Assurance Committee (Bangalore)",
        "description": "Internal inquiry examining packing benches, dispatch CCTV footage, and physical warehouse inventory reconciliation at the supplier plant.",
        "relevance": "Investigates whether all 10 cartons ever left the Bangalore supplier facility and reconciles the missing 150 units."
    }
}

def read_pdf(file_or_path):
    """
    Extracts selectable text from a PDF file using pypdf.
    Follows Day 2 read_pdf() pattern with graceful error handling.
    """
    try:
        reader = PdfReader(file_or_path)
        extracted = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted.append(f"--- Page {index} ---\n{page_text.strip()}")
        
        full_text = "\n\n".join(extracted)
        if not full_text.strip():
            return "[Empty or Scanned PDF: No extractable text found in document]"
        return full_text
    except Exception as exc:
        return f"[PDF Extraction Error: {str(exc)}]"

def read_email(file_or_path):
    """
    Extracts headers and body content from an .eml email file.
    """
    try:
        if hasattr(file_or_path, "read"):
            content = file_or_path.read()
            if isinstance(content, bytes):
                msg = email.message_from_bytes(content, policy=policy.default)
            else:
                msg = email.message_from_string(content, policy=policy.default)
        else:
            with open(file_or_path, "rb") as f:
                msg = email.message_from_binary_file(f, policy=policy.default)
                
        headers = [
            f"From: {msg.get('From', 'Unknown')}",
            f"To: {msg.get('To', 'Unknown')}",
            f"Cc: {msg.get('Cc', 'None')}",
            f"Subject: {msg.get('Subject', 'No Subject')}",
            f"Date: {msg.get('Date', 'Unknown Date')}"
        ]
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_content()
        else:
            body = msg.get_content()
            
        return "HEADERS:\n" + "\n".join(headers) + "\n\nBODY:\n" + body.strip()
    except Exception as exc:
        return f"[Email Extraction Error: {str(exc)}]"

def read_text(file_or_path):
    """
    Reads a standard text document.
    """
    try:
        if hasattr(file_or_path, "read"):
            content = file_or_path.read()
            return content.decode("utf-8") if isinstance(content, bytes) else str(content)
        with open(file_or_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as exc:
        return f"[Text Extraction Error: {str(exc)}]"

def extract_document_text(filepath):
    """
    Dispatches file reading based on extension.
    """
    if not os.path.exists(filepath):
        return f"[File Not Found: {filepath}]"
    
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return read_pdf(filepath)
    elif ext in [".eml", ".msg"]:
        return read_email(filepath)
    elif ext in [".txt", ".log", ".csv"]:
        return read_text(filepath)
    else:
        return f"[Unsupported Format: {ext}]"

def load_initial_evidence_register(base_dir="data/available_evidence"):
    """
    Loads and indexes all initial business records into a structured evidence dictionary.
    Assigns stable evidence IDs and preserves extraction metadata.
    """
    register = {}
    for item in INITIAL_DOCUMENTS_CONFIG:
        path = os.path.join(base_dir, item["filename"])
        raw_text = extract_document_text(path)
        
        register[item["id"]] = {
            "id": item["id"],
            "filename": item["filename"],
            "doc_type": item["doc_type"],
            "date": item["date"],
            "author": item["author"],
            "parties": item["parties"],
            "quantity_claimed": item["quantity_claimed"],
            "value_claimed": item["value_claimed"],
            "key_claim": item["key_claim"],
            "raw_text": raw_text,
            "is_hidden": False,
            "status": "Accessible"
        }
    return register

def get_hidden_catalogue():
    """
    Returns public metadata of hidden records without disclosing protected contents.
    """
    return {
        hid: {
            "id": info["id"],
            "title": info["title"],
            "custodian": info["custodian"],
            "description": info["description"],
            "relevance": info["relevance"],
            "status": "Hidden / Requires Justification"
        }
        for hid, info in HIDDEN_CATALOGUE_CONFIG.items()
    }

def request_hidden_evidence(hidden_id, reason, question, accessible_register, release_history, base_dir="data/hidden_evidence"):
    """
    Strict Python-based access control for releasing hidden evidence.
    Validates existence, reason quality, and updates accessible evidence register.
    Never exposes unreleased records.
    """
    hidden_id = (hidden_id or "").strip().upper()
    reason = (reason or "").strip()
    question = (question or "").strip()
    
    # 1. Validate that the record exists
    if hidden_id not in HIDDEN_CATALOGUE_CONFIG:
        return False, f"Rejection: Record ID '{hidden_id}' does not exist in the confidential evidence registry."
    
    # 2. Check if already released
    if hidden_id in accessible_register:
        return False, f"Notice: Evidence record '{hidden_id}' is already released and accessible in your workspace."
        
    # 3. Validate request fields
    if len(reason) < 15 or len(reason.split()) < 3 or len(re.findall(r"[a-zA-Z]", reason)) < 10:
        return False, "Rejection: Access justification is insufficient. Provide a substantive investigative reason (at least 3 words and 15 characters)."
        
    if len(question) < 10 or len(question.split()) < 2 or len(re.findall(r"[a-zA-Z]", question)) < 6:
        return False, "Rejection: Specific investigative question is required (at least 2 words and 10 characters)."
        
    config = HIDDEN_CATALOGUE_CONFIG[hidden_id]
    filepath = os.path.join(base_dir, config["filename"])
    
    if not os.path.exists(filepath):
        return False, f"System Error: Physical file for '{hidden_id}' could not be located in secure storage."
        
    raw_text = extract_document_text(filepath)
    
    # Release record into accessible register
    accessible_register[hidden_id] = {
        "id": hidden_id,
        "filename": config["filename"],
        "doc_type": config["title"],
        "date": "2026-10-14" if "001" in hidden_id or "002" in hidden_id else "2026-10-18",
        "author": config["custodian"],
        "parties": "Confidential Investigation Record",
        "quantity_claimed": "Audited Record",
        "value_claimed": "Audited Record",
        "key_claim": config["description"],
        "raw_text": raw_text,
        "is_hidden": True,
        "status": "Released upon Request"
    }
    
    # Record release in history
    release_event = {
        "evidence_id": hidden_id,
        "title": config["title"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reason": reason,
        "question": question,
        "status": "Approved and Released"
    }
    release_history.append(release_event)
    
    return True, f"Success: Evidence '{hidden_id}' ({config['title']}) has been authorized and released into your evidence register."

def validate_evidence_ids(evidence_ids, accessible_register):
    """
    Validates a list of evidence IDs against currently accessible records.
    Returns a tuple of (valid_ids, invalid_ids).
    """
    if not evidence_ids:
        return [], []
    valid = []
    invalid = []
    for eid in evidence_ids:
        cleaned = eid.strip().upper()
        if cleaned in accessible_register:
            valid.append(cleaned)
        else:
            invalid.append(cleaned)
    return valid, invalid
