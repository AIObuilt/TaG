from __future__ import annotations

import secrets


def create_enrollment_session(*, account_id: str, mode: str, billing_active: bool, machine_label: str) -> dict:
    if mode == "managed" and not billing_active:
        raise ValueError("billing required before managed bootstrap")
    return {
        "account_id": account_id,
        "mode": mode,
        "machine_label": machine_label,
        "bootstrap_token": secrets.token_urlsafe(24),
    }
