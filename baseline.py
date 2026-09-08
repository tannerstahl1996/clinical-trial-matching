import json
from patients import PatientProfile
from rules_engine import Verdict, CriterionCheck, TrialEligibilityResult, in_range
from trial_scope import KEPT_TRIAL_IDS

with open("trials.json") as f:
    all_trials = json.load(f)
TRIALS_BY_ID = {t["nct_id"]: t for t in all_trials if t["nct_id"] in KEPT_TRIAL_IDS}

def _parse_age(age_str):
    return int(age_str.split()[0]) if age_str else None

def evaluate_baseline(patient: PatientProfile, nct_id: str) -> TrialEligibilityResult:
    trial = TRIALS_BY_ID[nct_id]
    min_age = _parse_age(trial["minimum_age"]) or 0
    max_age = _parse_age(trial["maximum_age"]) or 200
    checks = [
        CriterionCheck("Age range (structured field)", in_range(patient.age, min_age, max_age)),
        CriterionCheck("Sex eligibility (structured field)",
            Verdict.PASS if trial["sex"] in ("ALL", patient.sex) else Verdict.FAIL),
    ]
    return TrialEligibilityResult(nct_id=nct_id, patient_id=patient.patient_id, checks=checks)
