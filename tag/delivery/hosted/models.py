from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EnrollmentSession:
    account_id: str
    mode: str
    machine_label: str
    bootstrap_token: str
