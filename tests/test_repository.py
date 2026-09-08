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


def test_provider_creation_success():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Alice Smith", specialties=["Cardiology", "Internal Medicine"])
    repo.create(p1)
    
    saved = repo.get("prov1")
    assert saved is not None
    assert saved.name == "Dr. Alice Smith"
    assert "Cardiology" in saved.specialties
    assert "Internal Medicine" in saved.specialties


def test_provider_creation_validation():
    repo = ProviderRepository()
    # No specialty or specialties provided
    p1 = Provider(provider_id="prov1", name="Dr. Alice Smith")
    with pytest.raises(ValueError) as exc:
        repo.create(p1)
    assert "one or more specialties" in str(exc.value)


def test_provider_specialty_backwards_compatibility():
    # Instantiating with legacy single specialty:
    p1 = Provider(provider_id="prov1", name="Dr. Smith", specialty="Dermatology")
    assert p1.specialties == ["Dermatology"]
    assert p1.specialty == "Dermatology"

    # Instantiating with new specialties:
    p2 = Provider(provider_id="prov2", name="Dr. Jones", specialties=["Pediatrics", "Immunology"])
    assert p2.specialty == "Pediatrics"
    assert p2.specialties == ["Pediatrics", "Immunology"]


def test_provider_list_unfiltered_includes_existing():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Active", specialties=["Cardiology"])
    repo.create(p1)

    # Bypass validation to simulate an existing legacy provider record with no specialty
    p_legacy = Provider(provider_id="prov_legacy", name="Dr. Legacy")
    repo._providers[p_legacy.provider_id] = p_legacy

    providers = repo.list()
    assert len(providers) == 2
    assert any(p.provider_id == "prov1" for p in providers)
    assert any(p.provider_id == "prov_legacy" for p in providers)


def test_provider_list_filtered_case_insensitive_and_whitespace():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Cardio", specialties=["Cardiology"])
    p2 = Provider(provider_id="prov2", name="Dr. Ortho", specialties=["Orthopedics"])
    p3 = Provider(provider_id="prov3", name="Dr. Multi", specialties=["Cardiology", "Orthopedics"])
    repo.create(p1)
    repo.create(p2)
    repo.create(p3)

    # Filter with exact match
    cardio_exact = repo.list(specialty="Cardiology")
    assert len(cardio_exact) == 2
    assert any(p.provider_id == "prov1" for p in cardio_exact)
    assert any(p.provider_id == "prov3" for p in cardio_exact)

    # Filter with lowercase and spaces
    cardio_fuzzy = repo.list(specialty="  cardiology  ")
    assert len(cardio_fuzzy) == 2


def test_provider_list_empty_state_not_error():
    repo = ProviderRepository()
    p1 = Provider(provider_id="prov1", name="Dr. Cardio", specialties=["Cardiology"])
    repo.create(p1)

    # Filtering with a specialty that has no providers should return an empty list, not error
    results = repo.list(specialty="Dermatology")
    assert results == []

