"""In-memory repository for appointments -- the data-access layer the rest
of the platform builds on. No real database: this is a demo project for
exercising a multi-repo AI pipeline (Driftbridge), not a production service.
"""

from __future__ import annotations

from models import Appointment


class DoubleBookingError(Exception):
    pass


class AppointmentRepository:
    def __init__(self) -> None:
        self._appointments: dict[str, Appointment] = {}

    def create(self, appointment: Appointment) -> Appointment:
        for existing in self._appointments.values():
            if (
                existing.provider_id == appointment.provider_id
                and existing.start_time == appointment.start_time
                and existing.status == "scheduled"
            ):
                raise DoubleBookingError(
                    f"Provider {appointment.provider_id} already has an active "
                    f"appointment at {appointment.start_time}"
                )
        self._appointments[appointment.appointment_id] = appointment
        return appointment

    def cancel(self, appointment_id: str) -> Appointment:
        appointment = self._appointments[appointment_id]
        appointment.status = "cancelled"
        return appointment

    def get(self, appointment_id: str) -> Appointment | None:
        return self._appointments.get(appointment_id)

    def list_for_patient(self, patient_id: str) -> list[Appointment]:
        return [a for a in self._appointments.values() if a.patient_id == patient_id]
