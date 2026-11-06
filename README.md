# DeepTrace

DeepTrace explores whether code-change history can help an AI security reviewer
judge a proposed change. A command runner might look the same even though an
earlier edit removed the check protecting it. Our prototype tracks these changes
and selects relevant history for the reviewer.

## Reproduce one experiment

For our Quarter 1 submission, we provide an offline reproduction of the **selector
evaluation**. We compared three ways of showing evidence to the reviewer:

- **Current:** facts about the proposed code, with supporting source.
- **Unselected history:** the same current evidence plus earlier version facts.
- **Selected history:** the same current evidence plus changes chosen by our selector.

There are 36 small Python cases per condition: six unsafe, 24 safe, and six where
the supported analysis cannot determine the answer. They come from six related
families, so they are not 36 independent real-world examples.

The command below recalculates the main results from saved per-case model responses
and reference answers. It does not call a model, regenerate source cases, or rerun
the selector. You can reproduce the analysis without an API key or any cost. Fresh
model calls are outside this reproduction and might give different answers.

### 1. Get the code and data

```bash
git clone https://github.com/VedPanse/DeepTrace.git
cd DeepTrace
git switch michael
```

These instructions use the `michael` branch, where this reproduction was added.
After it is merged into `main`, you can use `main` instead.

All data needed for this reproduction is included in Git. There is no separate
download or data account. Keep these files in their original locations under
`research/deeptrace_experiments/selector_evaluation/results/`:

| File | What we use it for |
| --- | --- |
| `test_analysis.json` | The `decoded` list contains 108 per-case records, including saved parsed model responses, reference answers, case IDs, and evidence token counts. |
| `protocol.json` | Records the conditions, original model settings, and study design. |
| `calibration_seal.json` | Contains the previously chosen alarm thresholds. We reuse these without recalibrating on test data. |

Although `test_analysis.json` also contains precomputed statistics, our script
calculates the table from individual responses. It ignores saved correctness flags
and checks the new totals against the original statistics. Checksums in
`reproduction/inputs.sha256.json` catch accidental input changes while allowing
different JSON formatting and Windows line endings.

The original reviewer was `openai/gpt-5-nano` through OpenRouter's OpenAI provider,
using minimal reasoning, JSON output, and a 256-token response limit. The exact
system prompt and settings are in `protocol.json`. This checkout does not include
the full original prompt/source dataset or individual provider-response archives;
the included parsed response records are sufficient for this analysis.

### 2. Set up Python and run

You need Git and **Python 3.10 or newer**. This reproduction uses only the Python
standard library, so there are no packages to install. It does not need Docker,
a GPU, Z3, NumPy, or the upstream analyzer. Those may be needed by other research
scripts, which are not part of this workflow.

We recommend a virtual environment. On Windows, in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe reproduce.py
```

On macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python reproduce.py
```

No activation step is needed. If Windows does not recognize `python`, try
`py -3 -m venv .venv` for the first command. Once Python is installed, the run is
offline and normally takes a few seconds.

### 3. Read the results

The command prints a table and writes these files to `output/reproduction/`:

- `results.csv`: recalculated numbers you can open in a spreadsheet.
- `results.json`: those numbers, the input checksums, and the reproduction scope.
- `summary.md`: a readable table and explanation.

You should get:

| Condition | Cases | Correct facts | Correct verdicts | Unsafe identified (raw) | Safe cases falsely accused (raw) | Contradictory answers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Current | 36 | 36 | 20 | 6 | 13 | 13 |
| Unselected history | 36 | 36 | 26 | 4 | 5 | 7 |
| Selected history | 36 | 36 | 24 | 6 | 9 | 9 |

Correct facts means all three reported facts match the reference: the input
restriction, the argument's origin, and whether shell execution is enabled.
Correct verdicts includes correctly answering unknown on the six unknown cases.
Raw means the model's answer before applying the alarm threshold. Contradictory
answers remain in the raw counts; they are not removed to improve the scores.

All three saved thresholds are 1. With binary verdict scores and the study's
strict `score > threshold` rule, every alarm is disabled. Calibrated detections
and false alarms are therefore both zero. This is not a useful detection result.

Selected history did not outperform unselected history on verdict accuracy in this
small study. The model recovered the current facts but often applied the policy
incorrectly. These cases already provided sufficient current facts, so they do not
establish a retrieval benefit in large repositories or improved LinuxArena attack
detection. Reference answers were not independently reviewed by human annotators.
More discussion is in `research/deeptrace_experiments/selector_evaluation/README.md`.

This reproduction covers the main counts and mean evidence lengths. It does not
recompute bootstrap intervals, the calibration process, or API costs. Historical
research results are left unchanged. Rerunning only replaces the three generated
files in `output/reproduction/`.

### Check the code

On Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s reproduction -p "test_*.py" -v
```

On macOS or Linux:

```bash
.venv/bin/python -m unittest discover -s reproduction -p 'test_*.py' -v
```

The tests cover unknown answers, contradictory verdicts, invalid responses,
duplicate or missing case pairs, and agreement with the saved results. The main
command exits with an error if data is missing, a checksum changes, or recalculated
totals disagree with the study. Restore the original inputs if this happens rather
than changing the expected numbers.

## The rest of the repository

- `research/agentsecgraph/`: our inspection of the existing analyzer, challenge
  programs, graph measurements, and visualizations.
- `research/deeptrace_experiments/`: temporal experiments, selector, monitor
  evaluations, diagnosis, and LinuxArena reconstruction work.
- `output/`: reports, figures, and presentations.
- `reproduce.py` and `reproduction/`: the offline reproduction described above.

Other folders preserve the research history. Their scripts are not a single build,
and some require excluded datasets, external repositories, credentials, or the
original platform. Use the commands above for this submission; do not run every
research script in sequence.
