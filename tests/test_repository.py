from datetime import datetime

import pytest

from models import Appointment, Provider
from repository import AppointmentRepository, DoubleBookingError, ProviderRepository


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
    provider = Provider(provider_id="prov1", name="Dr. Smith", specialties=["Cardiology"])
    repo.create(provider)
    assert repo.get("prov1") == provider


def test_provider_repository_list_no_filter():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Smith", specialties=["Cardiology"])
    p2 = Provider(provider_id="prov2", name="Dr. Jones", specialties=[])
    repo.create(p1)
    repo.create(p2)
    
    # Leaving the filter unset (None, empty, or whitespace) should return all providers
    assert len(repo.list()) == 2
    assert len(repo.list("")) == 2
    assert len(repo.list("  ")) == 2


def test_provider_repository_list_by_specialty():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Smith", specialties=["Cardiology"])
    p2 = Provider(provider_id="prov2", name="Dr. Jones", specialties=["Dermatology", "Cardiology"])
    p3 = Provider(provider_id="prov3", name="Dr. NoSpecialty")
    repo.create(p1)
    repo.create(p2)
    repo.create(p3)

    # Filter with cardiology, case-insensitive and stripped whitespace
    results = repo.list(" CARDIOLOGY  ")
    assert len(results) == 2
    assert p1 in results
    assert p2 in results
    assert p3 not in results

    # Filter by dermatology
    results_derm = repo.list("dermatology")
    assert len(results_derm) == 1
    assert p2 in results_derm


def test_provider_repository_empty_state_for_no_match():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Smith", specialties=["Cardiology"])
    repo.create(p1)

    # Filtering by a non-existent specialty should return empty list (no error)
    results = repo.list("Neurology")
    assert results == []


def test_provider_legacy_specialty_compatibility():
    repo = ProviderRepository()
    # A provider created with legacy 'specialty' field
    p = Provider(provider_id="prov1", name="Dr. Smith", specialty="Cardiology")
    repo.create(p)

    assert p.specialties == ["Cardiology"]
    results = repo.list("Cardiology")
    assert len(results) == 1
    assert results[0] == p
