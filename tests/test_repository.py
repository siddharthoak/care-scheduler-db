from datetime import datetime

import pytest

from models import Appointment
from repository import AppointmentRepository, DoubleBookingError


def _appointment(**overrides):
    defaults = dict(
        appointment_id="a1",
        patient_id="p1",
        provider_id="prov1",
        start_time=datetime(2026, 9, 1, 10, 0),
    )
    defaults.update(overrides)
    return Appointment(**defaults)


def test_create_and_get():
    repo = AppointmentRepository()
    repo.create(_appointment())
    assert repo.get("a1").status == "scheduled"


def test_double_booking_is_rejected():
    repo = AppointmentRepository()
    repo.create(_appointment())
    with pytest.raises(DoubleBookingError):
        repo.create(_appointment(appointment_id="a2", patient_id="p2"))


def test_cancelled_slot_can_be_rebooked():
    repo = AppointmentRepository()
    repo.create(_appointment())
    repo.cancel("a1", "change of plans")
    repo.create(_appointment(appointment_id="a2", patient_id="p2"))
    assert repo.get("a2").status == "scheduled"


def test_cancellation_reason_is_stored():
    repo = AppointmentRepository()
    repo.create(_appointment())
    repo.cancel("a1", "health improvement")
    appointment = repo.get("a1")
    assert appointment.status == "cancelled"
    assert appointment.cancellation_reason == "health improvement"


def test_cancel_requires_non_empty_reason():
    repo = AppointmentRepository()
    repo.create(_appointment())
    with pytest.raises(ValueError) as excinfo:
        repo.cancel("a1", "")
    assert "cannot be empty" in str(excinfo.value)

    with pytest.raises(ValueError):
        repo.cancel("a1", "   ")


def test_cancel_requires_non_placeholder_reason():
    repo = AppointmentRepository()
    repo.create(_appointment())
    placeholders = ["placeholder", "none", "n/a", "na", "no reason", "blank", "test", "tbd", "temp", "null", "undefined"]
    for placeholder in placeholders:
        with pytest.raises(ValueError) as excinfo:
            repo.cancel("a1", placeholder)
        assert "cannot be a placeholder" in str(excinfo.value)

        # check case-insensitive placeholder
        with pytest.raises(ValueError):
            repo.cancel("a1", placeholder.upper())


def test_cancel_requires_non_punctuation_reason():
    repo = AppointmentRepository()
    repo.create(_appointment())
    punctuations = ["-", "...", "???", "!!!", " - - "]
    for punc in punctuations:
        with pytest.raises(ValueError) as excinfo:
            repo.cancel("a1", punc)
        assert "cannot be a placeholder" in str(excinfo.value)


def test_list_for_patient():
    repo = AppointmentRepository()
    repo.create(_appointment())
    repo.create(_appointment(appointment_id="a2", provider_id="prov2"))
    assert len(repo.list_for_patient("p1")) == 2


def test_cancel_requires_non_placeholder_reason_variations():
    repo = AppointmentRepository()
    repo.create(_appointment())
    # Test variation of placeholders with extra spaces and mixed casing
    with pytest.raises(ValueError):
        repo.cancel("a1", "  NONE  ")
    with pytest.raises(ValueError):
        repo.cancel("a1", "tbd")
    with pytest.raises(ValueError):
        repo.cancel("a1", "  - -  ")


def test_cancel_accepts_emojis_and_special_characters():
    repo = AppointmentRepository()
    repo.create(_appointment())
    valid_reasons = [
        "Patient had a family emergency 🎂",
        "Doctor recommended rescheduling!",
        "Felt much better today :)",
        "予約キャンセルのため",
    ]
    for reason in valid_reasons:
        repo.cancel("a1", reason)
        appointment = repo.get("a1")
        assert appointment.cancellation_reason == reason


