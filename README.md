# care-scheduler-db

Data layer for the care-scheduler platform's appointment domain: models
(`Appointment`, `Provider`) and an in-memory repository enforcing the
double-booking rule. One of four repos in a multi-repo Driftbridge demo:

- **care-scheduler-db** (this repo) -- data models + repository
- [care-scheduler-api](https://github.com/siddharthoak/care-scheduler-api) -- booking/cancellation API
- [care-scheduler-ui](https://github.com/siddharthoak/care-scheduler-ui) -- patient-facing forms
- [care-scheduler-notify](https://github.com/siddharthoak/care-scheduler-notify) -- appointment notifications

Run tests: `pytest`
