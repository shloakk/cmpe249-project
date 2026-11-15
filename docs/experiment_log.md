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
