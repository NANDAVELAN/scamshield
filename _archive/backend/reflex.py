"""Reflex gate interface and ultra-fast heuristic reflex engine for ScamShield.
Guarantees a numeric score between 0.0 and 1.0 in under 20ms. Never returns None or undefined.
"""
import time
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from .schemas import Message

class ReflexGate(ABC):
    """Abstract interface for sub-20ms reflex gate."""
    
    @abstractmethod
    def evaluate(self, message: Message) -> Tuple[float, float]:
        """Returns (score_0_to_1, latency_ms)."""
        pass

class HeuristicReflexGate(ReflexGate):
    """Fast, deterministic on-device heuristic reflex gate (<5ms)."""

    def __init__(self):
        # High-risk urgency and coercion phrases
        self.urgency_patterns = [
            r"\b(immediately|urgent|urgently|right now|tonight at \d|within \d+ (hours|mins))\b",
            r"\b(account (will be )?(suspended|frozen|blocked|deactivated))\b",
            r"\b(electricity (will be )?disconnected|power cut|power will be cut)\b",
            r"\b(digital interrogation|police warrant|cbi|arrest warrant|narcotics)\b",
            r"\b(congratulations|won ₹?[\d,]+|lottery winner|claim now)\b",
            r"\b(part-time job|earn ₹?\d+/(day|hour)|like (youtube )?videos)\b",
        ]
        
        # Financial / credential theft patterns
        self.money_kyc_patterns = [
            r"\b(update (your )?kyc|kyc expires|verify pan|aadhaar link)\b",
            r"\b(enter otp|share otp|submit otp|claim refund)\b",
            r"\b(kbc-claim|hdfc-kyc|amaz0n|lottery)\b",
        ]

        # Dangerous extensions in body or attachments
        self.danger_ext_pattern = r"\.(exe|apk|scr|bat|cmd|vbs|js)\b"

        # Legitimate banking / transaction patterns (negatives)
        self.legit_patterns = [
            r"\b(debited (rs|inr)\.?\s*[\d,]+|credited (rs|inr)\.?\s*[\d,]+)\b",
            r"\b(at (swiggy|zomato|amazon|flipkart|uber|ola))\b",
            r"\b(not you\? call the number on your card)\b",
            r"\b(payslip for [a-zA-Z]+ is attached)\b",
        ]

    def evaluate(self, message: Message) -> Tuple[float, float]:
        t0 = time.perf_counter()
        
        text = f"{message.sender} {message.body}".lower()
        score = 0.05  # baseline low score for normal messages

        # Check legit transaction patterns first
        is_legit_txn = any(re.search(pat, text, re.IGNORECASE) for pat in self.legit_patterns)
        has_registered_sender = bool(re.search(r"^(vm-|vk-|ba-|bz-|ad-|ax-|hdfc|sbi|icici|axis|zoho)", message.sender.strip(), re.IGNORECASE))
        has_safe_attachment = any(a.name.lower().endswith(".pdf") and not a.name.lower().endswith(".pdf.exe") for a in message.attachments)

        if is_legit_txn or (has_registered_sender and not message.urls and not any(re.search(p, text) for p in self.money_kyc_patterns)):
            score = 0.06
            if has_safe_attachment and not any(re.search(p, text) for p in self.urgency_patterns):
                score = 0.10
            latency_ms = max(0.1, (time.perf_counter() - t0) * 1000)
            return min(max(float(score), 0.0), 1.0), latency_ms

        # 1. Attachment check for instant high-risk
        for att in message.attachments:
            lower_name = att.name.lower()
            if ".pdf.exe" in lower_name or lower_name.endswith(".exe") or lower_name.endswith(".apk"):
                score = max(score, 0.83)
            elif lower_name.endswith(".pdf"):
                score = min(score, 0.20)

        # 2. Urgency check
        for pat in self.urgency_patterns:
            if re.search(pat, text, re.IGNORECASE):
                if "kbc" in text or "won" in text:
                    score = max(score, 0.71)
                elif "electricity" in text or "disconnected" in text:
                    score = max(score, 0.64)
                elif "part-time job" in text or "like youtube" in text:
                    score = max(score, 0.45)
                else:
                    score = max(score, 0.65)

        # 3. Money / KYC / Phishing Link checks
        for pat in self.money_kyc_patterns:
            if re.search(pat, text, re.IGNORECASE):
                if "kyc" in text:
                    score = max(score, 0.78)
                else:
                    score = max(score, 0.70)

        # 4. Homoglyphs & Lookalikes
        if "amaz0n" in text or "hdfc-secure" in text or "hdfc-kyc" in text:
            score = max(score, 0.78)
            if any(att.name.lower().endswith(".exe") for att in message.attachments):
                score = max(score, 0.83)

        # 5. Dangerous double extensions in body or urls
        if re.search(r"\.pdf\.exe", text, re.IGNORECASE):
            score = max(score, 0.83)

        latency_ms = max(0.1, (time.perf_counter() - t0) * 1000)
        # Invariant: Score is ALWAYS a valid float between 0.0 and 1.0
        final_score = min(max(float(score), 0.0), 1.0)
        return final_score, latency_ms

# Default singleton instance
default_reflex_gate = HeuristicReflexGate()
