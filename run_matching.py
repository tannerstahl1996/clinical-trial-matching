from collections import Counter
from patients import PATIENTS
from rules_engine import evaluate, TRIAL_CHECKERS, Verdict

# Lower number = shown first. FAIL is the most actionable finding,
# so it surfaces above data gaps and non-automatable clauses.
DISPLAY_PRIORITY = {
    Verdict.FAIL: 0,
    Verdict.NOT_AUTOMATABLE: 1,
    Verdict.INSUFFICIENT_DATA: 2,
    Verdict.PASS: 3,
}

def print_scorecard(nct_id: str):
    print(f"\n{'='*60}\n{nct_id}\n{'='*60}")
    for patient in PATIENTS:
        result = evaluate(patient, nct_id)
        counts = Counter(c.verdict.value for c in result.checks)
        summary = ", ".join(f"{v}={n}" for v, n in counts.items())
        print(f"\n  {patient.patient_id}: {result.overall}  ({summary})")

        sorted_checks = sorted(result.checks, key=lambda c: DISPLAY_PRIORITY[c.verdict])
        for check in sorted_checks:
            if check.verdict != Verdict.PASS:
                print(f"      [{check.verdict.value}] {check.description}")

if __name__ == "__main__":
    for nct_id in TRIAL_CHECKERS:
        print_scorecard(nct_id)
