# Project Selection — Healthcare Application Context

## Selected Healthcare Application Context

### Name

**OpenMRS — Open Medical Record System**

### Public Repository

[https://github.com/openmrs/openmrs-core](https://github.com/openmrs/openmrs-core)

### Purpose

OpenMRS is an open-source electronic health record (EHR) platform developed and maintained by a global
community. It is used in healthcare facilities worldwide — primarily in low- and middle-income countries —
to store, manage, and retrieve patient medical records, appointment schedules, clinical observations,
and medication orders.

OpenMRS provides:
- Patient registration and demographic management
- Appointment scheduling workflows
- Clinical observation and form entry
- Medication prescription management
- Multi-user, multi-facility support
- RESTful API for integration with external systems

---

### Healthcare Workflow Relevance

This evaluation framework focuses on the **appointment scheduling and clinical navigation** workflows
that represent a common first point of contact between patients and healthcare providers.

These workflows — booking appointments, checking availability, cancelling, rescheduling, and
navigating clinical scope boundaries — are representative of the types of tasks an AI assistant would
perform as a front-end layer over a system like OpenMRS.

Key workflow categories from OpenMRS that inspire this project's scenario design:
- **Appointment scheduling module** — book, cancel, reschedule, check availability
- **Patient identity management** — DOB validation, MRN, phone number
- **Provider directory** — doctor name lookup, specialty, department
- **Clinical safety guardrails** — scope of practice, prescription, diagnosis boundaries

---

### How This Project Uses OpenMRS

This project does **not** integrate with, modify, or extend OpenMRS.

This project uses OpenMRS as a **reference architecture and workflow context** — the types of operations
an AI healthcare scheduling assistant would need to perform over a real EHR system like OpenMRS serve
as the foundation for the 21 evaluation scenarios.

Specifically:
- The 5 simulated healthcare tools (`check_availability`, `book_appointment`, `cancel_appointment`,
  `reschedule_appointment`, `get_appointment_info`) are modeled after operations that would be exposed
  by a real scheduling API such as the OpenMRS REST API.
- Synthetic patient data (names, DOBs, MRNs) follows the types of data fields found in OpenMRS patient records.
- Scenario categories (urgent symptoms, medication scope, PHI privacy, prompt injection) reflect
  realistic patient interactions with a healthcare scheduling AI agent.

---

### Explicit Clarification

> **This project does NOT rebuild, modify, extend, or integrate with OpenMRS or any other real healthcare application.**

The evaluation framework is entirely self-contained:
- All healthcare data is **synthetic** (fictional patient names, DOBs, appointment IDs).
- All tool implementations are **simulated** (no real EHR API calls are made).
- The `MockHealthcareAgent` and `DegradedHealthcareAgent` are **deterministic simulators**, not wrappers around OpenMRS.

No claim is made that this framework evaluates OpenMRS itself.
OpenMRS is cited as an **illustrative reference context** for the types of workflows and data structures
used in the evaluation scenarios.

---

### Why This Context Was Chosen

1. **Real-world relevance**: Appointment scheduling is one of the highest-volume patient interactions
   with healthcare AI systems.
2. **Safety boundary richness**: Scheduling AI agents operate at the intersection of clinical safety
   (emergency escalation), regulatory compliance (HIPAA), and operational correctness (tool argument precision).
3. **Open-source and transparent**: OpenMRS is a globally recognized, open-source EHR with public
   documentation, making it an appropriate non-commercial reference.
4. **Evaluable without real credentials**: The simulated tool layer reproduces the types of operations
   that would be performed without requiring access to any real healthcare system.
