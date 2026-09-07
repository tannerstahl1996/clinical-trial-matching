# Clinical Trial Eligibility Matching: How Much Requires Reading the Fine Print?

A small applied research project testing whether LLM-based extraction of
free-text clinical trial eligibility criteria meaningfully improves patient
matching over filtering on structured fields alone — and where it doesn't.

## The question

ClinicalTrials.gov exposes structured fields (age range, sex, condition) for
every trial through a free, public API. It also exposes a free-text
eligibility criteria block containing the actual inclusion and exclusion
logic — HbA1c thresholds, required medications, pregnancy exclusions,
investigator judgment clauses. Structured filtering is nearly free.
LLM-based extraction of the free text costs real money and adds real
latency. Does it earn its cost?

## Approach

1. **Deterministic rules engine** (`rules_engine.py`) — the checkable
   criteria from 5 real Type 2 diabetes drug trials, hand-encoded as Python
   logic, serving as ground truth. Verdicts use four states rather than a
   binary: `PASS`, `FAIL`, `INSUFFICIENT_DATA` (checkable in principle, not
   in the patient schema), and `NOT_AUTOMATABLE` (requires a clinician's
   judgment call by design — no schema fixes this).
2. **Structured-field baseline** (`baseline.py`) — filters on age range and
   sex only, using nothing beyond what the API already returns as
   structured data.
3. **LLM extraction** (`extract_criteria.py`, `llm_evaluator.py`) — Claude
   extracts structured predicates (age/BMI/HbA1c ranges, required and
   excluded medications, diabetes-type and pregnancy exclusions) from the
   same free-text criteria block, evaluated against 5 synthetic patient
   profiles designed to stress-test specific gaps.
4. **Layered pipeline** (`compare_methods.py`) — runs the free baseline
   first; only pairs it can't already reject get evaluated against the
   LLM-extracted criteria.

## Data

- 5 Type 2 diabetes drug trials, deliberately narrowed from an initial
  candidate pool of 30+ (see `exploration/` for what was tried and why it
  didn't fit — two dropped trials had inclusion criteria that contradicted
  the rest of the set's assumed patient population).
- 5 synthetic patient profiles, each designed to test a specific gap (a
  clean control case, a hard demographic disqualification, a
  pregnancy-only exclusion, a recency-window edge case, a
  never-eligible-to-begin-with case).
- All data is public, structured or free-text trial metadata from
  ClinicalTrials.gov's v2 API. No patient data, real or synthetic-from-real,
  is used anywhere.

## Results

Recall on the 14 patient-trial pairs with a real, ground-truth-confirmed
disqualifying criterion:

| Method | Recall |
|---|---|
| Structured-field baseline | 36% (5/14) |
| LLM extraction | 79% (11/14) |
| Layered (baseline + LLM) | 79% (11/14), same accuracy as full LLM |

The layered pipeline resolved 20% of all patient-trial pairs using the free
baseline alone, with no loss of accuracy on those pairs.

**Cost**: extracting structured criteria from all 5 trials cost $0.026
total (measured, not estimated) — roughly $0.005/trial. That cost is paid
once per trial, not per patient; in this run, 5 extracted trials served 25
patient-trial checks at an effective cost of about $0.001 per check, and
that ratio improves further as more patients are checked against the same
already-extracted trials. Extrapolated cost is roughly $5/1,000 trials, but
this should be read as an order-of-magnitude estimate: cost scales with
criteria length, and criteria length varies enormously across real trials
(one trial in this set had criteria roughly 4x longer than another).

## What the LLM extraction actually missed, and why

Three named, reproducible failure modes, none of them a simple
"hallucination":

1. **Schema-ceiling misses.** Two missed exclusions (trial recency window,
   prior-therapy-failure requirement) weren't extraction failures — the
   extraction schema never asked about those fields. An extraction
   pipeline's real ceiling is set by what it was told to look for, not by
   the model's reading comprehension.
2. **Drug-class-matching gap.** A patient who'd recently taken semaglutide
   should have been excluded from a trial that excludes "GLP-1 analogues,"
   but the matching logic does plain string containment with no
   pharmacological ontology, so "semaglutide" never matched "GLP-1
   analogues." The extraction correctly found the exclusion category; nothing
   downstream could connect a real drug name to it.
3. **OR-condition collapse.** One trial defines diabetes diagnosis as any
   one of four alternative lab thresholds. The extraction schema only has
   single min/max fields, so it collapsed a 4-way OR into one required
   HbA1c minimum, producing a false exclusion for a patient who qualified
   through a different diagnostic pathway.

A fourth finding surfaced without being sought: **re-running extraction on
identical input with an identical prompt produced slightly different
wording** in one trial's excluded-medications list across separate runs.
Extraction is not perfectly reproducible even holding everything else
constant — worth accounting for in any production design (e.g., running
extraction multiple times and reconciling, rather than trusting a single
pass).

## What this doesn't establish

- 5 trials and 5 patients is not a claim about how these numbers generalize
  to the full space of ~500,000 trials on the registry, which include far
  more heterogeneous criteria structures than this narrowed,
  same-drug-class set.
- Every trial in this set contains at least one investigator-judgment
  clause ("any finding that may interfere with safety") that no schema,
  rule, or model can resolve. As a direct consequence, ground truth never
  reaches a confident ELIGIBLE verdict on any pair in this dataset — only
  INELIGIBLE or UNDETERMINED. This is a structural property of how these
  trials are written, not a limitation of this project's design, but it
  means "the system said eligible" is not a claim this project makes or
  tests.
- The rules engine, while designed to be an independent ground truth, was
  hand-encoded by one person reading the trial text once. It has not been
  independently spot-checked against the source text by a second reviewer.

## What I'd test next

- Widen the trial set beyond same-drug-class T2DM trials to test whether
  the 79% recall figure holds on more heterogeneous criteria structures.
- Replace the keyword-based drug matcher with a real drug-class ontology
  to close the semaglutide-style gap.
- Extend the extraction schema to represent OR-conditions and duration
  requirements explicitly, rather than forcing them into single-value
  fields.
- Run extraction multiple times per trial and measure how often the
  non-determinism actually changes a downstream verdict, not just wording.

## Project structure

## Project structure

patients.py # synthetic patient profiles
trial_scope.py # single source of truth for which trials are in scope
rules_engine.py # hand-coded ground truth logic
baseline.py # structured-field-only filter
extract_criteria.py # LLM extraction of free-text criteria (calls Anthropic API)
llm_evaluator.py # evaluates patients against LLM-extracted criteria
run_matching.py # scorecard view of rules-engine verdicts
compare_methods.py # baseline vs LLM vs layered comparison + economics
fetch_final_trials.py # fetches the 5 kept trials by NCT ID
trials.json # simplified trial records used throughout
raw_trials.json # full raw API records, for provenance
extracted_criteria.json # LLM extraction output
extraction_usage.json # real token/cost/latency data per extraction call
exploration/ # superseded approaches, kept for the dead ends' findings


## Setup

Requires Python 3.9+ and an Anthropic API key (console.anthropic.com) for
the extraction step only — `run_matching.py` (the rules engine) needs no
API key at all.

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key-here" > .env
python3 run_matching.py # ground truth, no API calls
python3 extract_criteria.py # LLM extraction, ~$0.03 total
python3 compare_methods.py # full comparison