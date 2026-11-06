# DeepTrace

DeepTrace studies whether code-change history helps an AI security reviewer judge proposed changes. The instructions below reproduce the main results of our selector experiment using saved model responses. They do not make new model calls or rerun the selector.

## Data

Clone the repository and open the project folder:

```bash
git clone https://github.com/VedPanse/DeepTrace.git
cd DeepTrace
```

The required data is included in the repository under `research/deeptrace_experiments/selector_evaluation/results/`:

- `test_analysis.json`: saved responses and reference answers for 36 cases in each of three conditions.
- `protocol.json`: the experiment settings.
- `calibration_seal.json`: the saved alarm thresholds.

Leave these files in that folder. No additional data downloads or API keys are needed.

## Dependencies

Install Git and Python 3.10 or newer. The reproduction script uses only Python's standard library, so there are no extra packages to install.

## Run the experiment analysis

Run these commands from the `DeepTrace` folder.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe reproduce.py
```

**macOS or Linux:**

```bash
python3 -m venv .venv
.venv/bin/python reproduce.py
```

The script recalculates the results from individual saved responses and checks them against the original totals. It prints a table and saves `results.csv`, `results.json`, and `summary.md` in `output/reproduction/`.

The correct-verdict counts should be:

| Evidence given to the reviewer | Correct verdicts |
| --- | ---: |
| Current evidence only | 20/36 |
| Current evidence + unselected history | 26/36 |
| Current evidence + selected history | 24/36 |

Correct verdicts include correctly answering unknown. Selected history did not outperform unselected history in this small controlled experiment.

A successful run ends with:

```text
PASS: 108 records verified; recalculated metrics match the saved study.
```

## Check reproducibility

Try the instructions above in a fresh clone, rather than an existing working folder. You can also run the tests:

```powershell
# Windows
.\.venv\Scripts\python.exe -m unittest discover -s reproduction -p "test_*.py" -v
```

```bash
# macOS or Linux
.venv/bin/python -m unittest discover -s reproduction -p 'test_*.py' -v
```

All seven tests should pass. This workflow reproduces the saved experiment's main analysis; it does not reproduce fresh model inference or every historical experiment in the repository.
