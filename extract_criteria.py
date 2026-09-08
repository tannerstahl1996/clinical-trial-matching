import os
import json
import time
from dotenv import load_dotenv
from anthropic import Anthropic
from trial_scope import KEPT_TRIAL_IDS

load_dotenv()
client = Anthropic()

with open("trials.json") as f:
    all_trials = json.load(f)

trials = [t for t in all_trials if t["nct_id"] in KEPT_TRIAL_IDS]
print(f"Filtered to {len(trials)} of {len(all_trials)} trials in trials.json")

INPUT_RATE_PER_MTOK = 3.00
OUTPUT_RATE_PER_MTOK = 15.00

EXTRACTION_PROMPT = """You are extracting structured eligibility criteria from clinical trial text.

Trial structured fields (already known, don't re-derive these):
- Sex: {sex}
- Minimum age: {min_age}
- Maximum age: {max_age}

Given the eligibility criteria below, extract these fields as JSON. If a field isn't specified anywhere in the text, use null or an empty list — do not guess or assume a typical value for this kind of trial.

Fields:
- min_age (integer, years — use the structured field above if the criteria text doesn't restate it)
- max_age (integer, years — use the structured field above if the criteria text doesn't restate it)
- min_bmi (float, or null)
- max_bmi (float, or null)
- min_hba1c (float, percent, or null)
- max_hba1c (float, percent, or null)
- required_medications (list of strings — medications the PATIENT must already be taking to qualify. Do NOT include the drug being studied as the trial's intervention itself.)
- medication_requirement_type (string: "any_of" if a patient needs just ONE of the required_medications, "all_of" if ALL are required together, or null if required_medications is empty)
- excluded_medications (list of strings — medications or drug classes that DISQUALIFY a patient if used, per the exclusion criteria. Include the recency window in the string if one is stated, e.g. "GLP-1 analogues (past 3 months)".)
- excludes_type1_diabetes (boolean — true ONLY if Type 1 diabetes is explicitly mentioned as an exclusion in the text below)
- excludes_pregnancy (boolean)

Eligibility criteria:
{criteria}

Return ONLY valid JSON, no other text, no markdown code fences."""

def extract(trial: dict) -> tuple:
    prompt = EXTRACTION_PROMPT.format(
        sex=trial["sex"],
        min_age=trial["minimum_age"],
        max_age=trial["maximum_age"],
        criteria=trial["eligibility_criteria"],
    )
    start = time.time()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = time.time() - start

    usage = {
        "nct_id": trial["nct_id"],
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_seconds": round(elapsed, 2),
        "cost_usd": round(
            (response.usage.input_tokens / 1_000_000 * INPUT_RATE_PER_MTOK) +
            (response.usage.output_tokens / 1_000_000 * OUTPUT_RATE_PER_MTOK),
            6
        ),
    }

    raw = response.content[0].text
    return json.loads(raw), usage

if __name__ == "__main__":
    results = {}
    all_usage = []

    for trial in trials:
        print(f"\nExtracting {trial['nct_id']}...")
        try:
            extracted, usage = extract(trial)
            results[trial["nct_id"]] = extracted
            all_usage.append(usage)
            print(json.dumps(extracted, indent=2))
            print(f"  [{usage['input_tokens']} in / {usage['output_tokens']} out, "
                  f"{usage['latency_seconds']}s, ${usage['cost_usd']:.6f}]")
        except json.JSONDecodeError as e:
            print(f"  FAILED TO PARSE: {e}")
            results[trial["nct_id"]] = None

    with open("extracted_criteria.json", "w") as f:
        json.dump(results, f, indent=2)

    with open("extraction_usage.json", "w") as f:
        json.dump(all_usage, f, indent=2)
    print("Saved usage data to extraction_usage.json")

    total_cost = sum(u["cost_usd"] for u in all_usage)
    total_input = sum(u["input_tokens"] for u in all_usage)
    total_output = sum(u["output_tokens"] for u in all_usage)
    avg_latency = sum(u["latency_seconds"] for u in all_usage) / len(all_usage)

    print(f"\n--- Usage summary across {len(all_usage)} extraction calls ---")
    print(f"Total input tokens:  {total_input}")
    print(f"Total output tokens: {total_output}")
    print(f"Total cost:          ${total_cost:.6f}")
    print(f"Average latency:     {avg_latency:.2f}s per call")
    print(f"Projected cost per 1,000 trials: ${(total_cost / len(all_usage)) * 1000:.2f}")

    print("\nSaved all results to extracted_criteria.json")
