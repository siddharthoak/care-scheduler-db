from datetime import datetime

import pytest

from models import Appointment
from repository import AppointmentRepository, DoubleBookingError, InvalidCancellationReasonError


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
    repo.cancel("a1", reason="Need to reschedule to next week")
    repo.create(_appointment(appointment_id="a2", patient_id="p2"))
    assert repo.get("a2").status == "scheduled"


def test_list_for_patient():
    repo = AppointmentRepository()
    repo.create(_appointment())
    repo.create(_appointment(appointment_id="a2", provider_id="prov2"))
    assert len(repo.list_for_patient("p1")) == 2


def test_cancel_with_valid_reason_retains_reason():
    repo = AppointmentRepository()
    repo.create(_appointment())
    
    appointment = repo.cancel("a1", reason="I have a scheduling conflict on that day.")
    
    assert appointment.status == "cancelled"
    assert appointment.cancellation_reason == "I have a scheduling conflict on that day."
    
    # Ensure it's persisted in the repository too
    fetched = repo.get("a1")
    assert fetched.status == "cancelled"
    assert fetched.cancellation_reason == "I have a scheduling conflict on that day."


def test_cancel_with_invalid_type_is_rejected():
    repo = AppointmentRepository()
    repo.create(_appointment())
    
    with pytest.raises(InvalidCancellationReasonError, match="Cancellation reason must be a string"):
        repo.cancel("a1", reason=None)
        
    with pytest.raises(InvalidCancellationReasonError, match="Cancellation reason must be a string"):
        repo.cancel("a1", reason=123)


def test_cancel_with_empty_or_whitespace_reason_is_rejected():
    repo = AppointmentRepository()
    repo.create(_appointment())
    
    with pytest.raises(InvalidCancellationReasonError, match="Cancellation reason must be a short, non-empty explanation"):
        repo.cancel("a1", reason="")
        
    with pytest.raises(InvalidCancellationReasonError, match="Cancellation reason must be a short, non-empty explanation"):
        repo.cancel("a1", reason="   ")


@pytest.mark.parametrize("placeholder", [
    "placeholder", "none", "n/a", "na", "no reason", "test", "null", "blank", "-", "."
])
def test_cancel_with_placeholder_reason_is_rejected(placeholder):
    repo = AppointmentRepository()
    repo.create(_appointment())
    
    with pytest.raises(InvalidCancellationReasonError, match="Cancellation reason cannot be a placeholder"):
        repo.cancel("a1", reason=placeholder)
        
    # Also verify case insensitivity and whitespace handling
    with pytest.raises(InvalidCancellationReasonError, match="Cancellation reason cannot be a placeholder"):
        repo.cancel("a1", reason=f"  {placeholder.upper()}  ")

