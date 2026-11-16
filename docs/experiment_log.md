# Experiment log

## 2026-11-15 — HPC readiness setup (local only)

- Base commit: d53ef4a1db9d702ea1de217f8815fe88a495c7ae.
- Change commit: resolve with `git rev-parse HEAD` on this scaffold commit.
- Inputs: three existing proposal documents and user-supplied HPC observations.
- Work: path validation, inventory and SLURM smoke scaffold, tests, corrected scope.
- Local validation: 9 unit tests passed; all 3 HPC scripts passed `bash -n`;
  `git diff --check` passed. Synthetic local inventory integration passed with
  no dataset mutation; 8 representative ignore checks passed. Missing-config
  CLI returned the expected clear error and exit status 2. No HPC/GPU execution.
- HPC command: `bash scripts/hpc/submit_smoke.sh` (not yet run on HPC).
- SLURM job ID, runtime, GPU-hours, memory and metrics: not available.
- Expected logs: `$CMPE249_ARTIFACT_ROOT/logs/smoke-<jobid>.{out,err}`.
- Initial failure: workspace contained only empty Git metadata; repository fetch
  required approval to write .git. Resolved by approved fetch and working branch.
- Limitation: student IDs exist in inherited Git history; current files remove
  them. No destructive history rewrite performed.
- Gate: local evidence to be reported; HPC gate PENDING.
- Next action: user submits smoke, returns complete logs and SLURM accounting.

## 2026-11-15 — HPC infrastructure smoke, successful

- Commit: 49cba504dc0dffab58e152a96acd45e2bebe8af6; clean working tree.
- Command: `bash scripts/hpc/submit_smoke.sh`; submitted job 116264.
- Inputs: configured shared dataroot/derived directories and writable artifact root.
- Outputs: `logs/smoke-116264.out` and `.err` under the artifact root; complete
  stdout/accounting supplied in chat, no stderr content pasted.
- Scheduler: COMPLETED, exit 0:0; 2 seconds elapsed; batch MaxRSS 3580K.
- Approximate allocated GPU-hours: 2/3600 = 0.00056 with one allocated GPU.
  No model inference, model peak memory or planning metrics measured.
- Results: INVENTORY_OK and ENVIRONMENT_SMOKE_OK; assigned GPU 1; Python 3.9.25;
  no torch/MM stack installed; three CAN-bus checks missing; three annotation
  candidates readable; shared filesystem 5.0 TB available (quota unverified).
- Resolution: infrastructure gate PASSED. Missing model packages are expected
  at this stage and do not pass either model environment gate.
- Next action: install the exact official Senna requirements in an isolated
  Python 3.10 prefix through SLURM, then return complete logs and accounting.

## 2026-11-15 — Upstream requirements audit and environment recipes (local only)

- Commit: resolve this change with `git rev-parse HEAD` after checkout.
- Inputs: official Senna 31a3a2336e9494c254b612665fe55e95f67e9cae,
  VAD 1688c4b1c3a9e2e7873ca9700ff8058170c0e3c8,
  MMDetection3D v0.17.1 tag f1107977dfd26155fc1f83779ee6535d2468f449.
- Outputs: hashed upstream manifest, isolated Senna bootstrap/install recipe,
  VAD container recipe/constraints, import/CUDA probes and SLURM scripts.
- Local checks: 10 unit tests and shell syntax checks passed. Both available
  temporary official checkouts passed source-commit/hash verification. The VAD
  constraints projection matched every PyPI entry in its official export.
- Network failure: initial source cloning hit sandbox DNS restrictions; approved
  network execution fetched source successfully. No model weights downloaded.
- Deviations/limits: recorded in environments.md; recipes are not complete
  binary locks and no dependency installation/build was performed locally.
- Runtime, job IDs, GPU memory and metrics: not available for these recipes.
- Next action: one Senna setup attempt. Both model environment gates PENDING.

## Template for each subsequent attempt (including failures)

- Date / commit / dirty status:
- Complete command / environment:
- SLURM job ID / terminal state / exit code:
- Inputs / upstream commits / checkpoint hashes / split / config:
- Output and log locations:
- Metrics and denominators (or not measured):
- Wall time / GPU model and count / peak memory / GPU-hours:
- Failure reason / evidence:
- Resolution / deviations / limitations:
- Gate outcome / next action:
