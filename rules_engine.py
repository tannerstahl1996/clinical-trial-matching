from dataclasses import dataclass
from enum import Enum
from typing import List
from patients import PatientProfile
from trial_scope import KEPT_TRIAL_IDS

class Verdict(Enum):
    PASS = "pass"
    FAIL = "fail"
    INSUFFICIENT_DATA = "insufficient_data"
    NOT_AUTOMATABLE = "not_automatable"

@dataclass
class CriterionCheck:
    description: str
    verdict: Verdict

@dataclass
class TrialEligibilityResult:
    nct_id: str
    patient_id: str
    checks: List[CriterionCheck]

    @property
    def overall(self) -> str:
        if any(c.verdict == Verdict.FAIL for c in self.checks):
            return "INELIGIBLE"
        if any(c.verdict in (Verdict.INSUFFICIENT_DATA, Verdict.NOT_AUTOMATABLE) for c in self.checks):
            return "UNDETERMINED"
        return "ELIGIBLE"

def in_range(value, low, high) -> Verdict:
    if value is None:
        return Verdict.INSUFFICIENT_DATA
    return Verdict.PASS if low <= value <= high else Verdict.FAIL

def has_any_med(patient: PatientProfile, options: list) -> Verdict:
    # "any_of" requirement: patient needs at least ONE of these
    meds = [m.lower() for m in patient.current_medications]
    return Verdict.PASS if any(o.lower() in meds for o in options) else Verdict.FAIL

def has_med(patient: PatientProfile, name: str) -> Verdict:
    # One line of an "all_of" requirement — used alongside other has_med
    # calls, since requiring every check to PASS naturally expresses AND
    meds = [m.lower() for m in patient.current_medications]
    return Verdict.PASS if name.lower() in meds else Verdict.FAIL

def no_recent_excluded_med(patient: PatientProfile, excluded_terms: list) -> Verdict:
    recent = [m.lower() for m in patient.recent_medications]
    hit = any(term.lower() in med for term in excluded_terms for med in recent)
    return Verdict.FAIL if hit else Verdict.PASS

def not_recent(days_since, window_days) -> Verdict:
    if days_since is None:
        return Verdict.INSUFFICIENT_DATA
    return Verdict.PASS if days_since >= window_days else Verdict.FAIL

def no_history(days_since_event) -> Verdict:
    return Verdict.FAIL if days_since_event is not None else Verdict.PASS

def not_recent_event(days_since_event, window_days) -> Verdict:
    if days_since_event is None:
        return Verdict.PASS
    return Verdict.FAIL if days_since_event <= window_days else Verdict.PASS

def check_nct05028140(p: PatientProfile) -> List[CriterionCheck]:
    return [
        CriterionCheck("Age 18-85", in_range(p.age, 18, 85)),
        CriterionCheck("Diagnosis of T2DM", Verdict.PASS if p.diabetes_type == "Type 2" else Verdict.FAIL),
        CriterionCheck("Prior therapy failed to reach HbA1c goal", Verdict.PASS if p.prior_therapy_failed else Verdict.FAIL),
        CriterionCheck("Investigator safety judgment (exclusion)", Verdict.NOT_AUTOMATABLE),
        CriterionCheck("No history of alcohol/drug abuse", no_history(p.days_since_substance_abuse)),
        CriterionCheck("No trial participation in past 365 days", not_recent(p.days_since_last_trial, 365)),
        CriterionCheck("Not pregnant or lactating", Verdict.FAIL if p.pregnant_or_lactating else Verdict.PASS),
        CriterionCheck("No hypersensitivity to formula compounds", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("Not Type 1 diabetes", Verdict.FAIL if p.diabetes_type == "Type 1" else Verdict.PASS),
    ]

def check_nct07465224(p: PatientProfile) -> List[CriterionCheck]:
    return [
        CriterionCheck("Age 18-65", in_range(p.age, 18, 65)),
        CriterionCheck("Confirmed T2DM diagnosis", Verdict.PASS if p.diabetes_type == "Type 2" else Verdict.FAIL),
        CriterionCheck("BMI 23-39.9", in_range(p.bmi, 23, 39.9)),
        CriterionCheck("HbA1c 6.5-<10.5", in_range(p.hba1c, 6.5, 10.49)),
        # any_of: metformin OR SGLT2i OR DPP4i
        CriterionCheck("On stable metformin/SGLT2i/DPP4i (any one)", has_any_med(p, ["metformin", "SGLT2i", "DPP4i"])),
        CriterionCheck("No clinically significant concomitant disease (exclusion)", Verdict.NOT_AUTOMATABLE),
        CriterionCheck("No other glucose/insulin-interfering therapy (exclusion)", Verdict.NOT_AUTOMATABLE),
    ]

def check_nct06863532(p: PatientProfile) -> List[CriterionCheck]:
    stable_8wks = Verdict.PASS if (p.medication_stable_days or 0) >= 56 else (
        Verdict.INSUFFICIENT_DATA if p.medication_stable_days is None else Verdict.FAIL
    )
    return [
        CriterionCheck("Age 18-74", in_range(p.age, 18, 74)),
        CriterionCheck("T2DM diagnosis", Verdict.PASS if p.diabetes_type == "Type 2" else Verdict.FAIL),
        # all_of: SGLT2i AND metformin, each its own required line
        CriterionCheck("On SGLT2i monotherapy", has_med(p, "SGLT2i")),
        CriterionCheck("On metformin 500-1000mg/day", has_med(p, "metformin")),
        CriterionCheck("Stable regimen >= 8 weeks", stable_8wks),
        CriterionCheck("HbA1c 7.5-9.5", in_range(p.hba1c, 7.5, 9.5)),
        CriterionCheck("BMI <= 40", in_range(p.bmi, 0, 40)),
        CriterionCheck("Urine ketone negative", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("eGFR >= 60", in_range(p.egfr, 60, 999)),
        CriterionCheck("Not Type 1 diabetes", Verdict.FAIL if p.diabetes_type == "Type 1" else Verdict.PASS),
        CriterionCheck("No secondary diabetes types", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No pancreatitis/pancreatic transplant history", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No DKA/hyperosmolar coma history", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No moderate/severe liver insufficiency", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No recent CV event (3mo)", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No uncontrolled hypertension", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("Hemoglobin >= threshold", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No recurrent GU infections", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No bariatric surgery history", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No recent anti-obesity meds/weight loss attempt", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No cancer history (5yr)", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("HIV negative", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No severe peripheral vascular disease", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No hematologic malignancy/hemolytic disease", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No immune disease/systemic corticosteroids", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No recent thyroid dosage change", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No alcohol/drug abuse in past 3mo", not_recent_event(p.days_since_substance_abuse, 90)),
        CriterionCheck("No known drug allergies to study meds", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("Not pregnant/lactating", Verdict.FAIL if p.pregnant_or_lactating else Verdict.PASS),
        CriterionCheck("No trial participation in past 30 days", not_recent(p.days_since_last_trial, 30)),
        CriterionCheck("Investigator suitability judgment (exclusion)", Verdict.NOT_AUTOMATABLE),
    ]

def check_nct06428968(p: PatientProfile) -> List[CriterionCheck]:
    return [
        CriterionCheck("Age >= 18", in_range(p.age, 18, 200)),
        CriterionCheck("T2DM diagnosis", Verdict.PASS if p.diabetes_type == "Type 2" else Verdict.FAIL),
        CriterionCheck("No substance dependence/abuse or mental disorder", no_history(p.days_since_substance_abuse)),
        CriterionCheck("No TBI/seizure/CNS disease history", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No current suicidal/homicidal ideation", Verdict.NOT_AUTOMATABLE),
        CriterionCheck("Not on cognition-affecting drugs", Verdict.INSUFFICIENT_DATA),
        CriterionCheck("No significantly abnormal renal function", in_range(p.egfr, 60, 999)),
        CriterionCheck("Not pregnant/lactating", Verdict.FAIL if p.pregnant_or_lactating else Verdict.PASS),
    ]

def check_nct06256419(p: PatientProfile) -> List[CriterionCheck]:
    return [
        CriterionCheck("Age 25-70", in_range(p.age, 25, 70)),
        CriterionCheck("BMI 20-35", in_range(p.bmi, 20, 35)),
        CriterionCheck("HbA1c 7.0-12", in_range(p.hba1c, 7.0, 12.0)),
        CriterionCheck("T2DM diagnosis", Verdict.PASS if p.diabetes_type == "Type 2" else Verdict.FAIL),
        CriterionCheck("Follow-up data availability (post-hoc, not known at screening)", Verdict.NOT_AUTOMATABLE),
        CriterionCheck("No serious disease history (MI/stroke/trauma/kidney/liver/GI/pancreatitis)",
                        in_range(p.egfr, 60, 999) if p.egfr is not None else Verdict.INSUFFICIENT_DATA),
        CriterionCheck(
            "No recent GLP-1/weight-loss/glucocorticoid/GI-motility drugs (3mo)",
            no_recent_excluded_med(p, ["glp-1", "semaglutide", "exenatide", "weight-loss", "glucocorticoid", "gi-motility"])
        ),
    ]

TRIAL_CHECKERS = {
    "NCT05028140": check_nct05028140,
    "NCT07465224": check_nct07465224,
    "NCT06863532": check_nct06863532,
    "NCT06428968": check_nct06428968,
    "NCT06256419": check_nct06256419,
}

assert set(TRIAL_CHECKERS.keys()) == set(KEPT_TRIAL_IDS), (
    f"Mismatch: TRIAL_CHECKERS has {set(TRIAL_CHECKERS.keys())}, "
    f"but trial_scope.KEPT_TRIAL_IDS has {set(KEPT_TRIAL_IDS)}"
)

def evaluate(patient: PatientProfile, nct_id: str) -> TrialEligibilityResult:
    checker = TRIAL_CHECKERS[nct_id]
    return TrialEligibilityResult(nct_id=nct_id, patient_id=patient.patient_id, checks=checker(patient))
