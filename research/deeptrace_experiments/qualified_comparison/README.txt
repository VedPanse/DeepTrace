DeepTrace meeting update: qualification and one paired follow-up

The original negative pilots remain frozen; qualification/results/negative_pilot_freeze.json
records their hashes. Neither H1 nor H2 is established, and LinuxArena is not completed.

Stages:
1. qualification/: source-backed semantic packet repair and frozen two-model check.
   Both models failed the first untouched check. A development-only reference
   correction preserved known argument/shell facts under an unresolved guard;
   original records are retained in development_reference_v1/.
2. monitor_repair/: ONE targeted correction distinguishes guard/control flow from
   argument/data flow and puts the fixed-list exception first. Fresh development
   and qualification data, identical criteria and settings. Nano passed on 43/44;
   GPT-5 had the same accuracy but failed unknown/contradiction handling.
3. qualified_comparison/: ONE new paired supported-fixture comparison using Nano
   after the gate passed. Current evidence remains byte-identical in the history
   arm. Calibration thresholds and prompts were frozen before fresh testing.

Test result: current code 12/12 unsafe identified, 16/108 raw false accusations,
1 raw null. Current + history 9/12 unsafe, 25/108 raw false accusations, 28 raw nulls.
Contradiction validation leaves 17 versus 53 unhandled actions. Rejected answers
are NOT safe classifications. Zero accepted false alarms is not a zero-cost or
matched-intervention result. Raw false-positive rates differ. Basic qualification
success did not guarantee robust behavior on the broader instances.

History consists of bounded, verified earlier source facts and change provenance.
This is not a performance test of the later full source/support DAG or a finished
security-directed DeepTrace selector. It is not LinuxArena sabotage detection.
The deterministic checker is a restricted-fixture reference only.

Offline reproduction (from project root, with the existing pinned .venv):
  research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/qualification/scripts/checks.py
  research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/monitor_repair/scripts/checks.py
  research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/qualified_comparison/scripts/analyze.py test
  research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/qualified_comparison/scripts/checks.py
  research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/qualified_comparison/scripts/meeting_report.py

Do not rerun preparation over the frozen directories. For new studies use new run
paths and new held-out families. Network inference is in run.py and was performed
as development -> seal -> qualification, and calibration -> seal -> test. Each run
keeps exact prompts, reference facts, raw provider responses and content hashes.
Cached exact prompts share one draw. No raw qualification response was available
before its release/seal check. No target process or LinuxArena tools were executed.

Models: openai/gpt-5-nano and openai/gpt-5, same minimal reasoning and 256-token
output cap, OpenAI-only provider routing with data_collection deny. Provider alias
and metadata snapshots are saved, but immutable weights and ZDR are not claimed.
Total project spending remains below the existing $3 cap.

Presentation: output/deeptrace_meeting/DeepTrace_Meeting_Final.pptx.
Each slide has a short SAY THIS script and separate detailed Q&A/source notes.
Readable research record: output/deeptrace_meeting/Research_Summary.html.
Access request: continuation/RESOURCE_REQUEST.txt. No external request was sent.
