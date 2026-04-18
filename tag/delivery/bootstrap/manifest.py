from __future__ import annotations


def build_bootstrap_manifest(
    *,
    bootstrap_token: str,
    enrollment_id: str,
    machine_label: str,
    hosted_base_url: str,
) -> dict:
    return {
        "bootstrap_token": bootstrap_token,
        "enrollment_id": enrollment_id,
        "machine_label": machine_label,
        "bootstrap_url": f"{hosted_base_url.rstrip('/')}/bootstrap/{bootstrap_token}",
    }
