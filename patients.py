from dataclasses import dataclass
from typing import Optional

@dataclass
class PatientProfile:
    patient_id: str
    age: int
    sex: str
    condition: str
    diabetes_type: Optional[str]
    bmi: Optional[float]
    hba1c: Optional[float]
    egfr: Optional[float]
    current_medications: list
    recent_medications: list       # anything taken in the past ~3 months,
                                    # including drugs no longer active —
                                    # separate from current_medications
                                    # because a stopped drug can still
                                    # trigger a recency-based exclusion
    medication_stable_days: Optional[int]
    prior_therapy_failed: bool
    pregnant_or_lactating: bool
    days_since_substance_abuse: Optional[int]
    days_since_last_trial: int
    known_drug_allergies: list
    notes: str = ""

PATIENTS = [
    PatientProfile(
        patient_id="P001", age=45, sex="FEMALE", condition="Type 2 Diabetes",
        diabetes_type="Type 2", bmi=28.0, hba1c=8.0, egfr=75.0,
        current_medications=["metformin", "SGLT2i"], recent_medications=["metformin", "SGLT2i"],
        medication_stable_days=90,
        prior_therapy_failed=True, pregnant_or_lactating=False,
        days_since_substance_abuse=None, days_since_last_trial=400,
        known_drug_allergies=[],
        notes="Control case: designed to pass every checkable criterion."
    ),
    PatientProfile(
        patient_id="P002", age=16, sex="MALE", condition="Type 1 Diabetes",
        diabetes_type="Type 1", bmi=22.0, hba1c=9.0, egfr=110.0,
        current_medications=["insulin"], recent_medications=["insulin"],
        medication_stable_days=30,
        prior_therapy_failed=True, pregnant_or_lactating=False,
        days_since_substance_abuse=None, days_since_last_trial=400,
        known_drug_allergies=[],
        notes="Fails on age AND diabetes type across nearly every trial."
    ),
    PatientProfile(
        patient_id="P003", age=34, sex="FEMALE", condition="Type 2 Diabetes",
        diabetes_type="Type 2", bmi=27.0, hba1c=8.5, egfr=80.0,
        current_medications=["metformin"], recent_medications=["metformin"],
        medication_stable_days=90,
        prior_therapy_failed=True, pregnant_or_lactating=True,
        days_since_substance_abuse=None, days_since_last_trial=400,
        known_drug_allergies=[],
        notes="Pregnant. Tests whether each trial's exclusions even mention pregnancy."
    ),
    PatientProfile(
        patient_id="P004", age=60, sex="FEMALE", condition="Type 2 Diabetes",
        diabetes_type="Type 2", bmi=30.0, hba1c=8.5, egfr=70.0,
        current_medications=["metformin", "SGLT2i"], recent_medications=["metformin", "SGLT2i", "semaglutide"],
        medication_stable_days=90,
        prior_therapy_failed=True, pregnant_or_lactating=False,
        days_since_substance_abuse=None, days_since_last_trial=200,
        known_drug_allergies=[],
        notes="200 days since last trial: fails 365-day window, passes 30-day window. "
              "Also took semaglutide (a GLP-1) recently: tests trial 5's excluded-medication check."
    ),
    PatientProfile(
        patient_id="P005", age=29, sex="MALE", condition="Type 2 Diabetes",
        diabetes_type="Type 2", bmi=23.0, hba1c=6.0, egfr=95.0,
        current_medications=[], recent_medications=[],
        medication_stable_days=None,
        prior_therapy_failed=False, pregnant_or_lactating=False,
        days_since_substance_abuse=None, days_since_last_trial=99999,
        known_drug_allergies=[],
        notes="Newly diagnosed, untreated, HbA1c already near normal. Never eligible to begin with."
    ),
]
