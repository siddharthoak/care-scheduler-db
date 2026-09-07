from datetime import datetime

import pytest

from models import Appointment, Provider
from repository import AppointmentRepository, ProviderRepository, DoubleBookingError


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
    repo.cancel("a1")
    repo.create(_appointment(appointment_id="a2", patient_id="p2"))
    assert repo.get("a2").status == "scheduled"


def test_list_for_patient():
    repo = AppointmentRepository()
    repo.create(_appointment())
    repo.create(_appointment(appointment_id="a2", provider_id="prov2"))
    assert len(repo.list_for_patient("p1")) == 2


def test_provider_repository_create_and_get():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Smith", specialties=["cardiology", "pediatrics"])
    repo.create(p1)
    retrieved = repo.get("prov1")
    assert retrieved is not None
    assert retrieved.name == "Dr. Smith"
    assert retrieved.specialties == ["cardiology", "pediatrics"]


def test_provider_repository_list_no_filter():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Smith", specialties=["cardiology"])
    p2 = Provider(provider_id="prov2", name="Dr. Jones", specialties=[])
    repo.create(p1)
    repo.create(p2)
    
    # Unfiltered list should return all providers, including the one with no specialties
    all_providers = repo.list()
    assert len(all_providers) == 2
    assert {p.provider_id for p in all_providers} == {"prov1", "prov2"}


def test_provider_repository_list_with_specialty_filter():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Smith", specialties=["cardiology", "pediatrics"])
    p2 = Provider(provider_id="prov2", name="Dr. Jones", specialties=["pediatrics", "dermatology"])
    p3 = Provider(provider_id="prov3", name="Dr. Taylor", specialties=[])
    repo.create(p1)
    repo.create(p2)
    repo.create(p3)
    
    # Filter by pediatrics
    pediatricians = repo.list(specialty="pediatrics")
    assert len(pediatricians) == 2
    assert {p.provider_id for p in pediatricians} == {"prov1", "prov2"}
    
    # Filter by cardiology
    cardiologists = repo.list(specialty="cardiology")
    assert len(cardiologists) == 1
    assert cardiologists[0].provider_id == "prov1"


def test_provider_repository_list_empty_state_not_error():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Smith", specialties=["cardiology"])
    repo.create(p1)
    
    # Filtering by an unused specialty must return an empty list, not an error
    results = repo.list(specialty="neurology")
    assert results == []

