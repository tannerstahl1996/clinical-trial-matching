import json
from patients import PatientProfile
from rules_engine import Verdict, CriterionCheck, TrialEligibilityResult, in_range

with open("extracted_criteria.json") as f:
    EXTRACTED = json.load(f)

def _keyword_match(patient_meds: list, term: str) -> bool:
    term_lower = term.lower()
    return any(m.lower() in term_lower or term_lower in m.lower() for m in patient_meds)

def _check_required(patient: PatientProfile, required: list, req_type: str) -> Verdict:
    if req_type == "any_of":
        return Verdict.PASS if any(_keyword_match(patient.current_medications, t) for t in required) else Verdict.FAIL
    return Verdict.PASS if all(_keyword_match(patient.current_medications, t) for t in required) else Verdict.FAIL

def _check_excluded(patient: PatientProfile, excluded: list) -> Verdict:
    hit = any(_keyword_match(patient.recent_medications, t) for t in excluded)
    return Verdict.FAIL if hit else Verdict.PASS

def evaluate_llm(patient: PatientProfile, nct_id: str) -> TrialEligibilityResult:
    crit = EXTRACTED[nct_id]
    checks = []

    checks.append(CriterionCheck("Age range", in_range(patient.age, crit["min_age"] or 0, crit["max_age"] or 200)))

    if crit["min_bmi"] is not None or crit["max_bmi"] is not None:
        checks.append(CriterionCheck("BMI range", in_range(patient.bmi, crit["min_bmi"] or 0, crit["max_bmi"] or 999)))

    if crit["min_hba1c"] is not None or crit["max_hba1c"] is not None:
        checks.append(CriterionCheck("HbA1c range", in_range(patient.hba1c, crit["min_hba1c"] or 0, crit["max_hba1c"] or 99)))

    if crit["required_medications"]:
        checks.append(CriterionCheck(
            f"Required medications ({crit['medication_requirement_type']})",
            _check_required(patient, crit["required_medications"], crit["medication_requirement_type"])
        ))

    if crit["excluded_medications"]:
        checks.append(CriterionCheck("No excluded medications", _check_excluded(patient, crit["excluded_medications"])))

    if crit["excludes_type1_diabetes"]:
        checks.append(CriterionCheck("Not Type 1 diabetes", Verdict.FAIL if patient.diabetes_type == "Type 1" else Verdict.PASS))

    if crit["excludes_pregnancy"]:
        checks.append(CriterionCheck("Not pregnant/lactating", Verdict.FAIL if patient.pregnant_or_lactating else Verdict.PASS))

    return TrialEligibilityResult(nct_id=nct_id, patient_id=patient.patient_id, checks=checks)
