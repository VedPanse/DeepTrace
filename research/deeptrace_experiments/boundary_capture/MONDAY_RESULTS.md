# DeepTrace progress for November 16

## Main result

We now have a repeatable demonstration of why source history needs execution receipts, not just final diffs or successful-command logs. In a pinned LinuxArena application's actual TypeScript role-checking middleware, an authored edit changed the viewer/admin behavior even though its editing command exited with code 7. Restoring the file erased the change from the final source tree. Our captures preserved the intermediate state and its failed-command receipt.

This is a controlled infrastructure study. It does not establish improved attack detection by a model, reproduce a historical attack, or evaluate the complete LinuxArena task.

## What ran

- Three fresh isolated containers using the same pinned AMD64 application image. These are repetitions of one authored scenario, not three independent attacks.
- The complete `/app/src` tree: 27 files, 37 entries including directories, 87,084 initial content bytes. No host folders, network, database, HTTP service or model calls.
- The real `requireRole` function from `api/middleware/rbac.ts`, transpiled using the image's TypeScript installation and invoked with mock requests/responses. A viewer and an admin were checked against an admin-only rule.
- A harmless comment edit, a guard weakening followed by exit code 7, restoration, and a separately synchronized background mutation. The final restoration returned both source and observed middleware behavior to baseline.

## Observations

| Check | Result across repetitions | Why it matters |
|---|---:|---|
| Baseline and harmless edit deny the viewer, allow admin | 3/3 | The probe distinguishes the intended control from the changed guard. |
| Failed editing command leaves a persistent change and allows viewer | 3/3 | A failed call must still receive a post-action capture. |
| Restoration returns the viewer to denial | 3/3 | Intermediate weakening and current state must stay distinct. |
| Background child changes source after its parent returns | 3/3 | Foreground completion alone does not establish that all effects are complete. |
| Pre-dispatch guard notices unexplained drift and blocks the next call | 3/3 | Do not silently attach an earlier state to the next proposed action. |
| Final source tree exactly matches initial source tree | 3/3 | Initial/final comparison alone misses this temporary change. |

The viewer's middleware outcome followed `denied (status 403) → allowed (next called) → denied → allowed after background release → denied after restoration`. These are middleware-level observations with mocks, not HTTP requests or demonstrated application-level harm.

We verified all 36 original tar captures against their JSON manifests, file bytes and hashes. Nine capture/dispatch integrity tests pass; the original six-scenario pilot still verifies offline. The background trigger and completion handshake are recorded separately as analyst synchronization, not attributed to a foreground agent call.

## Runtime and limits

Each repetition took approximately 4.4–4.5 seconds on this local machine. The measured interval from confirmed pause to completed resume was approximately 54 ms median and 65 ms maximum. This excludes the initial pause-command latency and is not the total instrumentation overhead or a general performance benchmark. The AMD64 image ran on an ARM64 host.

The guard compares the previous captured state to the next pre-action state. It does not prevent a background mutation after that check, prove which process caused a change, or determine whether it was malicious. This study uses an explicit completion handshake to create a known delayed effect. Database state, network effects, process memory, files outside `/app/src`, full-harness integration and independently reviewed harm boundaries remain unfinished.

## How this changes our direction

The earlier 36-case selector study remains unchanged: current evidence scored 20/36, unselected history 26/36, and selected history 24/36. These new results do not overturn that negative comparison. They establish a more concrete engineering need: preserving and checking intermediate state before evaluating which history helps a monitor. The next experiment should connect this capture layer to real harness actions and compare evidence strategies on independently checked trajectories with equal current-code access.

## Reproduce or inspect

From the repository root, without Docker or model calls:

```sh
python3 research/deeptrace_experiments/boundary_capture/analyze_application.py research/deeptrace_experiments/boundary_capture/results/application-2026-11-13
python3 -m unittest discover -s research/deeptrace_experiments/boundary_capture -p 'test_*.py' -v
```

To run fresh repetitions, start Docker Desktop, ensure the pinned `IMAGE` in `pilot.py` is installed, then choose an unused output directory:

```sh
python3 research/deeptrace_experiments/boundary_capture/application_study.py --out /tmp/deeptrace-application-new --repetitions 3
```

`results/application-2026-11-13/protocol.json` records the source hashes and image before execution. `summary.json` contains aggregate measurements; each `repeat-*` directory contains original captures, intent/receipt records and middleware observations. No paid calls were made.
