# Exploration

Early approaches that were tried and deliberately set aside as the project's
scope tightened. Kept here rather than deleted because the dead ends surfaced
real findings, not because the code itself is reusable.

- **fetch_trials.py / fetch_candidates.py** — earlier versions of the trial
  fetch script, before the trial set was narrowed from 7 candidates to 5
  comparable drug-vs-drug trials. Two dropped trials (a CAD-focused
  canagliflozin study and a treatment-naive semaglutide study) had inclusion
  criteria that contradicted the rest of the trial set's assumed patient
  population — see the main README for details.

- **label_trials.py / labels.csv** — an early approach to building ground
  truth by hand-labeling patient-trial pairs directly, before that was
  replaced by a deterministic rules engine (rules_engine.py). Abandoned
  because hand-labeling didn't scale cleanly once trial criteria proved more
  heterogeneous than the first trial suggested.

- **candidate_trials_raw.json / sample_study.json** — raw API responses
  from early data exploration, kept for provenance.
