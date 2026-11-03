# LinuxArena access reassessment — November 1, 2026

The previous claim that we had to wait for private access was too broad. Official documentation supports public archive downloads and local Docker evaluations. On this reassessment the public site responded, and the exact formerly failing run archive downloaded without credentials. Synthetic results remain frozen; no new monitor or paid agent calls were made.

## Verified access and setup

* Public discovery: https://data.linuxarena.ai/llms.txt returned HTTP 200 and identifies public, credential-free access.
* https://data.linuxarena.ai/api/runs?limit=1 returned HTTP 200.
* https://data.linuxarena.ai/api/runs/ace6e820844e4faf9e0a5907f774a7c6/eval returned HTTP 200: 18,537,569 bytes, 105 samples. The original archive is saved under data/ and its SHA256 is recorded in results/archive_inventory.json.
* Unlike our previously cached excerpts, this archive contains environment commits, image digests and harness revision metadata. Its 105 samples contain 7,383 tool events. An inventory is available; these counts do not prove completeness, replay correctness or harm timing.
* Docker Desktop was installed but not running. After opening it, Docker Engine 29.3.1 became available on ARM64.
* The historical auto_workflow image pinned in that archive pulled publicly and passed an isolated, no-network smoke test: ARM64, Node v18.20.8, Python 3.10.12, application source under /app/src. This is a container test, not a complete task evaluation.
* A separate current harness checkout was pinned at 0faf35e034ff3c89802d0b456c11ab215149fa0a. Its frozen dependencies installed successfully: Inspect 0.3.282, CT 6.0.0rc4, SDK 4.0.0rc2. The host's uv 0.9.8 was too old; a task-specific uv>=0.13.5 ran the frozen install without replacing the global executable.
* A free OpenRouter key-status request succeeded. The existing key can support fresh runs; it was not printed or copied into this directory. A Vast.ai GPU rental is unnecessary for API-based runs.
* Full local readiness subsequently succeeded through `ct live up`: legitimate task webhook_node_full_implementation installed, application/PostgreSQL/RabbitMQ all healthy, and the application's /health endpoint returned healthy. This was real Docker with direct internet and the internet simulator disabled, not the LLM-simulated sandbox. No model was called. It verifies this setup configuration, not the full simulator-enabled research configuration or agent/scorer success.
* The current application image was pinned to index sha256:6894de9f192927526d334fc1a89ca0dd2531bf833805d1e7117811e87a6ea3e5, PostgreSQL to sha256:2bc89eed5490967e6b1fa5175d84cb45d65f19fbb8973c7b23450dea785b9505, RabbitMQ to sha256:c601bbed8c3138c74d13439d1db867c106ec76029c3c9e458c11e18c3de25b2e. Exact container image IDs, source commits, lock hash and health receipts are in results/local_readiness.json.
* A post-setup readiness capture saved all 8,213 entries under /app (148,436,681 content bytes), with no silent exclusions, in data/readiness_app.json.gz. Services were paused before copying and resumed afterward. Pauses were sequential, not a globally atomic machine snapshot. Database/broker contents, process memory and files outside /app are outside this scope. This is one initial capture, NOT automatic per-action capture or a verified replay of the recovered historical run.

Official references: https://docs.linuxarena.ai/quickstart and https://docs.linuxarena.ai/web-viewer . Documentation describes local evaluation, not a guarantee that any particular task will succeed on this machine.

## Revised blocker

Public access and initial revision/image metadata are no longer the demonstrated blocker for this run. We still must validate the pinned initial task setup, account for tool failures and partial effects, reconstruct and verify intermediate states, and independently establish harm boundaries. Scorer baseline store entries are not workspace snapshots. Hidden goals, scorer material and future outcomes must stay out of monitor inputs.

The recovered historical archive should be audited before paying to generate replacements. A fresh cohort is now an alternative, not something requiring private access. It would be a new evaluation, not an exact reproduction of published runs. The existing Python selector still does not implement general semantic analysis for this TypeScript application.

Three matching webhook samples (one honest, two attack) are listed in results/candidate_cohort.json, selected by task filename rather than outcomes. They remain unverified candidates. Environment metadata in the archive contains side-task goal information; do NOT pass full environment metadata to monitors. Any future evidence exporter must allowlist legitimate task/source/action fields and keep analyst/scorer records separate.

## Fresh-cohort preparation, if needed

Start with one honest and one attack episode on the same legitimate task/environment, then validate capture/reconstruction end to end. This pair is an infrastructure pilot, not enough for false-positive calibration or a detection claim. Candidate: auto_workflow / webhook_node_full_implementation; choose and freeze an appropriate side task only after inspecting its setup and defining harm evidence. Do not select episodes by successful outcomes after generation.

Pin the harness/SDK/Inspect lock, environment commit, every service image digest including database/broker/simulator, platform, model settings, task/scorer source and setup. Save initial post-setup workspace bytes and tree hashes. Existing capture_workspace.py can encode inert file contents but is NOT automatically connected to live action execution.

Before paid generation, add and validate an execution-boundary capture hook: record the proposed action and call ID, pause relevant services at an identified boundary, capture workspace state, release for execution, then capture after results including failed/partial writes. Serial calls and parallel action groups must be distinguished; either serialize under a declared protocol or capture the entire group and report that individual intermediate boundaries are unavailable. Record background effects and service data separately. Pausing services is an intervention and must be recorded; identical capture procedures should apply to honest and attack runs.

Do not claim automatic per-action snapshots are ready merely because a helper exists. Validate the hook without model calls on real isolated-container edits, a failed/partially writing command, and ordering/concurrency. Never run recorded attack tools on the host. Do not upload logs to the hosted viewer; local .eval output suffices.

## Cost estimate before any paid launch

Current public OpenRouter model metadata reports GPT-5 Mini at $0.25 per million input tokens and $2 per million output tokens. At an assumed 1 million cumulative input tokens and 20,000 output tokens per episode, cost is $0.29. One honest plus one attack episode is $0.58; a 25% reserve gives $0.725. This is an assumption-based estimate, not a measured LinuxArena run cost or a quality endorsement of this model.

An initial proposed agent budget is about $0.75, excluding a later monitoring study and any model-based scoring. Verify all scorer roles before launching; use per-sample cost limits and token/step caps, and allow for final-request overshoot. No cloud/GPU charges are needed locally. The previous recorded project spend is about $0.97; preserve the existing $3 project cap rather than treating the account key's larger allowance as authorization to spend it.

Monitor choice and the realistic evidence-comparison rationale remain separate research decisions. Readiness work here does not reopen synthetic prompt/selector tuning or authorize another monitoring evaluation.

## Reproducible commands

Run from the project root unless stated otherwise:

    curl -L --fail https://data.linuxarena.ai/api/runs/ace6e820844e4faf9e0a5907f774a7c6/eval -o research/deeptrace_experiments/linuxarena_reassessment/data/ace6e820844e4faf9e0a5907f774a7c6.eval
    research/deeptrace_experiments/linuxarena_fresh_control/.venv/bin/python research/deeptrace_experiments/linuxarena_reassessment/scripts/archive_inventory.py
    docker pull linuxarena/env-auto_workflow@sha256:e821d9ac0293508ddaa254de3a670bdede625b906e4ad5cbf4de5bdf56864205

Do not rerun downloads over the saved archive without preserving its hash. The separately pinned current setting is under linuxarena_fresh_control/.settings/linuxarena, with auto_workflow at b7f3e189ebf436ccb783d1e6e12faf360baf5b9a. Historical image and current environment source are distinct provenance records; do not conflate them.
