#!/bin/sh
# Documentary command record. Run from the DSC-180A project root.
# Existing results are frozen: regenerate into a NEW directory for a new study.
# No recorded LinuxArena commands are executed by these scripts.

# Sources acquired for inspection:
# git clone --depth 1 https://github.com/linuxarena/control-tower.git research/deeptrace_experiments/control-tower
# git clone --depth 1 --branch v1.0.1 https://github.com/linuxarena/auto_workflow.git research/deeptrace_experiments/env-auto-workflow

# Preparation, BEFORE inference (do not overwrite the frozen original run):
# research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/audit.py
# research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/controlled.py
# env -i PATH=/usr/bin:/bin HOME=/private/tmp TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 /usr/bin/sandbox-exec -f research/deeptrace_experiments/continuation/results/isolation.sb research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/static.py
# research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/packets.py
# research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/score.py calibration
# research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/score.py test

# Offline verification/analysis (safe for current saved run):
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/checks.py
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/metrics.py
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/final_checks.py
research/deeptrace_experiments/.venv/bin/python research/deeptrace_experiments/continuation/scripts/report.py
research/deeptrace_experiments/tools/tectonic output/pdf/deeptrace_experiment_report/main.tex
