# From 36% to 79%: Testing LLMs for Clinical Trial Matching

A small applied research project testing whether LLM-based extraction of
free-text clinical trial eligibility criteria meaningfully improves patient
matching over filtering on structured fields alone, and where it doesn't.

**Full writeup:** [From 36% to 79%: Testing LLMs for Clinical Trial Matching](https://www.ffpurpose.com/from-36-to-79-testing-llms-for-clinical-trial-matching/)
on Fit for Purpose.

## The question

ClinicalTrials.gov exposes structured fields (age range, sex, condition) for
every trial through a free, public API. It also exposes a free-text
eligibility criteria block containing the actual inclusion and exclusion
logic: HbA1c thresholds, required medications, pregnancy exclusions,
investigator judgment clauses. Structured filtering is nearly free.
LLM-based extraction of the free text costs real money and adds real
latency. Does it earn its cost?

## Approach

1. **Deterministic rules engine** (`rules_engine.py`): the checkable
   criteria from 5 real Type 2 diabetes drug trials, hand-encoded as Python
   logic, serving as reference standard. Verdicts use four states rather
   than a binary: `PASS`, `FAIL`, `INSUFFICIENT_DATA` (checkable in
   principle, not in the patient schema), and `NOT_AUTOMATABLE` (requires a
   clinician's judgment call by design, no schema fixes this).
2. **Structured-field baseline** (`baseline.py`): filters on age range and
   sex only, using nothing beyond what the API already returns as
   structured data.
3. **LLM extraction** (`extract_criteria.py`, `llm_evaluator.py`): Claude
   extracts structured predicates (age/BMI/HbA1c ranges, required and
   excluded medications, diabetes-type and pregnancy exclusions) from the
   same free-text criteria block, evaluated against 5 synthetic patient
   profiles designed to stress-test specific gaps.
4. **Layered pipeline** (`compare_methods.py`): runs the free baseline
   first; only pairs it can't already reject get evaluated against the
   LLM-extracted criteria.

## Data

- 5 Type 2 diabetes drug trials, deliberately narrowed from an initial
  candidate pool of 30+ (see `exploration/` for what was tried and why it
  didn't fit; two dropped trials had inclusion criteria that contradicted
  the rest of the set's assumed patient population).
- 5 synthetic patient profiles, each designed to test a specific gap (a
  clean control case, a hard demographic disqualification, a
  pregnancy-only exclusion, a recency-window edge case, a
  never-eligible-to-begin-with case).
- All data is public, structured or free-text trial metadata from
  ClinicalTrials.gov's v2 API. No patient data, real or synthetic-from-real,
  is used anywhere.

## Results

Recall on the 14 patient-trial pairs with a real, reference-confirmed
disqualifying criterion:

| Method | Recall |
|---|---|
| Structured-field baseline | 36% (5/14) |
| LLM extraction | 79% (11/14) |
| Layered (baseline + LLM) | 79% (11/14), same accuracy as full LLM |

The layered pipeline resolved 20% of all patient-trial pairs at the free
baseline stage, with no loss of accuracy on those pairs.

**Cost**: extracting structured criteria from all 5 trials cost $0.026
total (measured from the API response's actual usage counts, not
estimated), roughly $0.005/trial. That cost is paid once per trial, not per
patient; in this run, 5 extracted trials served 25 patient-trial checks at
an effective cost of about $0.001 per check, and that ratio improves
further as more patients are checked against the same already-extracted
trials. Extrapolated cost is roughly $5/1,000 trials, but this should be
read as an order-of-magnitude estimate: cost scales with criteria length,
and criteria length varies enormously across real trials (one trial in
this set had criteria roughly 4x longer than another).

## What the LLM extraction missed, and why

Three named failure modes, none of them a simple "hallucination":

1. **Missing schema field.** Two missed exclusions (trial recency window,
   prior-therapy-failure requirement) weren't extraction failures; the
   extraction schema never asked about those fields.
2. **Missing domain knowledge.** A patient who had recently taken
   semaglutide should have been excluded from a trial that excludes "GLP-1
   analogues," but the matching logic does plain string containment with
   no pharmacological ontology, so "semaglutide" never matched "GLP-1
   analogues." The extraction correctly found the exclusion category;
   nothing downstream could connect a real drug name to it.
3. **Model variance combined with brittle matching.** Rerunning extraction
   8 times on the same trial produced 3 different phrasings of the same
   required-medication field ("SGLT2i" vs "SGLT2 inhibitor" vs
   "sodium-glucose cotransporter 2 inhibitor (SGLT2i)"). Because the
   matching logic does substring containment, one phrasing failed to match
   the patient's medication record. Three of eight identical extraction
   runs would therefore have produced a different downstream eligibility
   verdict.

A fourth category of criterion cannot be automated at all: three of the
five trials contain investigator-judgment clauses like "any finding that
may interfere with safety." No schema, rule, or model can resolve these.

## What this does not establish

- 5 trials and 5 patients is not a claim about how these numbers generalize
  to the full space of trials on the registry, which include far more
  heterogeneous criteria structures than this narrowed,
  same-drug-class set.
- Every trial in this set contains at least one investigator-judgment
  clause that no schema, rule, or model can resolve. As a direct
  consequence, the reference implementation never reaches a confident
  ELIGIBLE verdict on any pair in this dataset, only INELIGIBLE or
  UNDETERMINED. This means "the system said eligible" is not a claim this
  project makes or tests.
- The reference implementation was hand-encoded by one person reading the
  trial text once. Every disagreement between baseline, LLM extraction,
  and the reference (10 cases in total) was manually reviewed against the
  actual trial text, and zero labeling errors were found in the
  reference, but that review was still done by one person.

## What I'd test next

Widen the trial set from 5 tightly related T2DM trials to 50 trials across
multiple therapeutic areas, and test whether the exclusion-first
architecture survives messier eligibility criteria. Replace the
keyword-based drug matcher with a real drug-class ontology to close the
semaglutide-style gap. Extend the extraction schema to represent
OR-conditions and duration requirements explicitly. Run extraction multiple
times per trial and measure how often the nondeterminism actually changes
a downstream verdict, not just wording.

## Project structure

patients.py # synthetic patient profiles
trial_scope.py # single source of truth for which trials are in scope
rules_engine.py # hand-coded reference standard logic
baseline.py # structured-field-only filter
extract_criteria.py # LLM extraction of free-text criteria (calls Anthropic API)
llm_evaluator.py # evaluates patients against LLM-extracted criteria
run_matching.py # scorecard view of rules-engine verdicts
compare_methods.py # baseline vs LLM vs layered comparison + economics
adjudicate.py # walks through disagreements for manual review
test_nondeterminism.py # reruns extraction N times to measure output stability
fetch_final_trials.py # fetches the 5 kept trials by NCT ID
trials.json # simplified trial records used throughout
raw_trials.json # full raw API records, for provenance
extracted_criteria.json # LLM extraction output
extraction_usage.json # real token/cost/latency data per extraction call
adjudication_log.json # manual review record of all disagreement cases
nondeterminism_runs.json # raw output from 8-run stability test
exploration/ # superseded approaches, kept for the dead ends' findings


## Reproducibility

Every number in the essay and in the results table above comes from
running the scripts in this repo against the code and data as committed.
Specifics:

- **Python version:** 3.13
- **Model:** `claude-sonnet-4-6` (Anthropic API)
- **Model temperature/sampling:** the Anthropic API's defaults (not
  explicitly set in `extract_criteria.py`). Any real production use would
  want to pin these deliberately.
- **Extraction prompt:** the full prompt used lives in `extract_criteria.py`
  as `EXTRACTION_PROMPT`. Reading it there rather than duplicating it here
  keeps a single source of truth.
- **API pricing used for cost calculations:** $3.00 per million input
  tokens and $15.00 per million output tokens for `claude-sonnet-4-6`
  (checked against Anthropic's platform docs at the time of the runs).
  Pricing may have changed since; the raw token counts are saved in
  `extraction_usage.json` so cost can be recomputed against current
  pricing.
- **Extraction runs:** [YYYY-MM-DD to fill in]
- **Nondeterminism test:** 8 extraction runs per trial, 40 API calls total,
  cost ~$0.21.

## Setup

Requires Python 3.9+ and an Anthropic API key (console.anthropic.com) for
the extraction step only. `run_matching.py` (the rules engine) needs no
API key at all.

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key-here" > .env
python3 run_matching.py # reference standard, no API calls
python3 extract_criteria.py # LLM extraction, ~$0.03 total
python3 compare_methods.py # full comparison
python3 test_nondeterminism.py # optional: 8-run stability test, ~$0.21
python3 adjudicate.py # optional: manual review of disagreements