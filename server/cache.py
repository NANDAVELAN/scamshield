"""Message hash-keyed verdict cache for fast demo replays and rate-limit hygiene."""
import hashlib
import json
import time
from typing import Dict, Any, Optional
from scamshield_agent.schemas import Verdict, TriageResult

class VerdictCache:
    def __init__(self, ttl_seconds: int = 86400):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def compute_hash(self, message: Dict[str, Any]) -> str:
        """Compute deterministic SHA256 digest of relevant message payload."""
        channel = str(message.get("channel", "")).strip().lower()
        sender = str(message.get("sender", "")).strip().lower()
        body = str(message.get("body", "")).strip()
        urls = sorted([str(u).strip().lower() for u in message.get("urls", [])])
        att_names = sorted([
            a.get("name", "") if isinstance(a, dict) else str(a)
            for a in message.get("attachments", [])
        ])

        payload = f"{channel}|{sender}|{body}|{','.join(urls)}|{','.join(att_names)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Look up verdict by message hash."""
        m_hash = self.compute_hash(message)
        entry = self._cache.get(m_hash)
        if not entry:
            self.misses += 1
            return None

        if time.time() - entry["timestamp"] > self.ttl:
            del self._cache[m_hash]
            self.misses += 1
            return None

        self.hits += 1
        return entry["data"]

    def set(self, message: Dict[str, Any], data: Dict[str, Any]):
        """Store verdict in cache."""
        m_hash = self.compute_hash(message)
        self._cache[m_hash] = {
            "timestamp": time.time(),
            "data": data
        }

    def clear(self):
        """Clear cache (used for live demos)."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

verdict_cache = VerdictCache()
