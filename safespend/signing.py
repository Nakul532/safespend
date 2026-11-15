"""HMAC signing for settlement permits and approvals."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

from .models import canonical_json


class Signer:
    def __init__(self, key: bytes | None = None) -> None:
        self._key = key if key is not None else secrets.token_bytes(32)

    def sign(self, fields: dict[str, Any]) -> str:
        return hmac.new(self._key, canonical_json(fields).encode("utf-8"), hashlib.sha256).hexdigest()

    def verify(self, fields: dict[str, Any], signature: str) -> bool:
        return hmac.compare_digest(self.sign(fields), signature)
