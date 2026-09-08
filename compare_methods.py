import json
from collections import Counter
from patients import PATIENTS
from rules_engine import evaluate as evaluate_ground_truth, TRIAL_CHECKERS
from llm_evaluator import evaluate_llm
from baseline import evaluate_baseline

def run_layered(patient, nct_id):
    baseline_result = evaluate_baseline(patient, nct_id)
    if baseline_result.overall == "INELIGIBLE":
        return baseline_result.overall, "baseline_only"
    llm_result = evaluate_llm(patient, nct_id)
    return llm_result.overall, "needed_extracted_criteria"

if __name__ == "__main__":
    rows = []
    stage_counts = Counter()

    for nct_id in TRIAL_CHECKERS:
        for patient in PATIENTS:
            gt = evaluate_ground_truth(patient, nct_id).overall
            baseline = evaluate_baseline(patient, nct_id).overall
            llm = evaluate_llm(patient, nct_id).overall
            layered, stage = run_layered(patient, nct_id)
            stage_counts[stage] += 1
            rows.append((nct_id, patient.patient_id, gt, baseline, llm, layered))

    print(f"{'Trial':<14}{'Pt':<5}{'GroundTruth':<14}{'Baseline':<12}{'LLM':<14}{'Layered'}")
    for r in rows:
        print(f"{r[0]:<14}{r[1]:<5}{r[2]:<14}{r[3]:<12}{r[4]:<14}{r[5]}")

    true_ineligible = [r for r in rows if r[2] == "INELIGIBLE"]
    n = len(true_ineligible)

    def recall(method_idx):
        caught = sum(1 for r in true_ineligible if r[method_idx] == "INELIGIBLE")
        return caught, caught / n if n else 0.0

    baseline_caught, baseline_recall = recall(3)
    llm_caught, llm_recall = recall(4)
    layered_caught, layered_recall = recall(5)

    print(f"\n--- Recall on {n} pairs with a real disqualifying criterion ---")
    print(f"Baseline caught:  {baseline_caught}/{n}  ({baseline_recall:.0%})")
    print(f"LLM caught:       {llm_caught}/{n}  ({llm_recall:.0%})")
    print(f"Layered caught:   {layered_caught}/{n}  ({layered_recall:.0%})")

    missed_by_llm = [r for r in true_ineligible if r[4] != "INELIGIBLE"]
    print(f"\n--- Missed by LLM evaluator ({len(missed_by_llm)}) ---")
    for r in missed_by_llm:
        print(f"  {r[0]} / {r[1]}: ground truth INELIGIBLE, LLM said {r[4]}")

    false_positives = [r for r in rows if r[2] != "INELIGIBLE" and r[4] == "INELIGIBLE"]
    print(f"\n--- LLM false exclusions ({len(false_positives)}) ---")
    for r in false_positives:
        print(f"  {r[0]} / {r[1]}: ground truth {r[2]}, LLM said INELIGIBLE")

    total = sum(stage_counts.values())
    baseline_only = stage_counts["baseline_only"]
    needed_extraction = stage_counts["needed_extracted_criteria"]

    print(f"\n--- Where the free baseline alone was sufficient ---")
    print(f"Resolved by baseline, no extracted criteria needed: {baseline_only}/{total} ({baseline_only/total:.0%})")
    print(f"Needed the extracted criteria to resolve:           {needed_extraction}/{total} ({needed_extraction/total:.0%})")

    try:
        with open("extraction_usage.json") as f:
            usage = json.load(f)
        total_cost = sum(u["cost_usd"] for u in usage)
        n_trials = len(usage)
        print(f"\n--- Real extraction economics ---")
        print(f"Extraction is a per-TRIAL cost, paid once, not a per-patient cost.")
        print(f"Total cost to extract criteria for {n_trials} trials: ${total_cost:.6f}")
        print(f"Average cost per trial extracted: ${total_cost/n_trials:.6f}")
        print(f"That one-time cost then serves unlimited patient checks at $0 marginal cost.")
        print(f"In this run: {n_trials} trials extracted, {len(PATIENTS)} patients each = "
              f"{n_trials * len(PATIENTS)} checks served from {n_trials} paid API calls.")
        print(f"Effective cost per patient-trial check in this run: "
              f"${total_cost/(n_trials * len(PATIENTS)):.6f}")
    except FileNotFoundError:
        print("\n(Run extract_criteria.py first to see real cost data here.)")
