"""Data models for the care-scheduler platform's appointment domain.

Owned by this repo. care-scheduler-api keeps its own copy of this same
shape rather than importing this package directly -- these are separate
deployable repos, not packages published to a shared registry -- so a
schema change here is a coordinated change across repos, not an automatic
one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Provider:
    provider_id: str
    name: str
    specialties: list[str] = field(default_factory=list)


@dataclass
class Appointment:
    appointment_id: str
    patient_id: str
    provider_id: str
    start_time: datetime
    status: str = "scheduled"  # "scheduled" | "completed" | "cancelled"
    reason_for_visit: str = ""
