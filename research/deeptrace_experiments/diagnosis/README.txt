DeepTrace controlled failure diagnosis

Scope: inspected continuation cases are now DEVELOPMENT data. No fresh held-out
claim. Original prompts, scores and thresholds remain unchanged. LinuxArena remains
an independent access/provenance blocker; no fragment-only evaluation was run.

Run from project root with the existing experiment environment:
  research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/diagnosis/scripts/offline.py
  research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/diagnosis/scripts/analyze_probes.py
  research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/diagnosis/scripts/capture_checks.py
  research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/diagnosis/scripts/brief.py

These commands use saved responses and make no model calls. probe.py prepare
constructs the frozen development prompts; probe.py run makes authorized API calls
only for uncached prompts, uses the same GPT-5 Nano settings, and checks combined
cost against the existing $3 cap. Do not treat this development set as fresh testing.

Results:
- score_diagnostics.json: ROC points, AUROC, unique-prompt counts, class score
  distributions and ambiguous-label prompt hashes for every condition; prior
  pilot AUROC kept separate, never pooled with continuation.
- threshold_forcing_cases.json: every benign calibration response at or above
  each condition's frozen threshold, with exact packet and repeated case IDs.
- matched_cases.json: exact code, original messages, scores and short responses.
- development_jobs.jsonl / development_responses.jsonl: 24 logical jobs, 18 unique
  successful prompts; saved original results supply the original/original arm.
- responses/: actual provider records. One failed network attempt is retained;
  the exact request was retried. Failures do not become benign scores.
- probe_diagnosis.json: policy/fact correctness and internal consistency. Single
  draws on a selected tiny sample do not estimate general model capability.
- original_packet_audit.json: source-derived decisive facts were present in the
  selected original current-code packets. Complete probes omit computed verdicts.
- execution_status.json: steps 1-3 done; step 4 clarification did not pass the
  development prerequisite, so step 5 is deferred, not described as completed.

The only retained harness correction is structured-response consistency checking.
Contradictory answers are invalid/unknown and must count against coverage. It would
be incorrect to map them to safe scores or claim improved false-positive rates.

Human-readable artifacts: output/deeptrace_diagnosis/DeepTrace_Diagnosis.html and
mistake_notebook.html, with ROC/distribution PNG/PDF figures. All are local files.

Independent tooling: continuation/scripts/capture_workspace.py records text,
binary bytes, symlinks, modes and hashes without following links or executing
source. It does not prove a paused boundary or initial revision. Five fixture
checks pass. The existing RESOURCE_REQUEST.txt remains ready for the user to send.
