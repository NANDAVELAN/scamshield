"""Attachment threat analysis tool for ScamShield."""
import os
from typing import Dict, Any, List

DANGEROUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".vbs", ".cmd", ".apk",
    ".ps1", ".jar", ".iso", ".wsf", ".msi", ".dll"
}

MACRO_EXTENSIONS = {".docm", ".xlsm", ".pptm", ".dotm"}

def analyze_attachment(filename: str, size_kb: float = 0.0) -> Dict[str, Any]:
    """Inspect attachment filename and extension for double extensions, executables, and malicious macros.

    Args:
        filename: Name of the attachment file.
        size_kb: File size in kilobytes.

    Returns:
        dict: Danger rating, suspicious indicators, and status.
    """
    if not filename:
        return {
            "status": "success",
            "filename": "",
            "is_suspicious": False,
            "reasons": []
        }

    lower_name = filename.lower().strip()
    reasons: List[str] = []
    is_suspicious = False

    # Check double extensions (e.g. invoice.pdf.exe)
    parts = lower_name.split(".")
    if len(parts) > 2:
        inner_ext = "." + parts[-2]
        outer_ext = "." + parts[-1]
        if inner_ext in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".jpg", ".png"}:
            if outer_ext in DANGEROUS_EXTENSIONS or outer_ext in MACRO_EXTENSIONS:
                is_suspicious = True
                reasons.append(f"Deceptive double extension hiding executable ({inner_ext}{outer_ext})")

    # Check executable extension
    _, ext = os.path.splitext(lower_name)
    if ext in DANGEROUS_EXTENSIONS:
        is_suspicious = True
        reasons.append(f"Direct executable file format ({ext})")

    # Check macro-enabled documents
    if ext in MACRO_EXTENSIONS:
        is_suspicious = True
        reasons.append(f"Macro-enabled office document format ({ext})")

    return {
        "status": "success",
        "filename": filename,
        "extension": ext,
        "size_kb": size_kb,
        "is_suspicious": is_suspicious,
        "reasons": reasons,
        "risk_weight": 0.85 if is_suspicious else 0.0
    }
