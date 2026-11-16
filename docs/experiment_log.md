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

## 2026-11-15 — Senna environment setup, failed before installation

- Commit: 38b2a326d0124e83cc89b9f86dc22c3131df2406; clean working tree.
- Command: submitted `scripts/hpc/setup_senna.sbatch`; job 116267 on cs001.hpc.coe.
- Scheduler: FAILED, exit 1:0; elapsed 00:02:12; batch MaxRSS 41.50M.
- GPU assignment: 0; approximate allocated GPU-hours 132/3600 = 0.03667.
- Logs: `logs/senna-environment-116267.out` and `.err` in the artifact root;
  complete stdout/stderr and accounting returned in chat.
- Failure: `git clone` timed out connecting to github.com:443 in the compute
  allocation. Package installation, Conda environment creation and model imports
  were not reached. No model metrics or peak CUDA memory measured.
- Resolution prepared locally: source staging separated from compute-node setup;
  verification-only mode; parallel HEAD-only package-server connectivity checks.
- Local validation: 17 unit tests passed; shell/Python syntax, naming/privacy and
  whitespace checks passed. No real HPC network probe was run locally.
- Gate: infrastructure remains passed; model environments BLOCKED by unresolved
  installation connectivity. Do not build VAD or retry Senna installation yet.
- Next action: return login/compute network diagnostics; choose installation or
  offline transfer based on evidence. Preserve any partial clone/environment.

## 2026-11-15 — Compute package connectivity, blocked

- Commit: b8ab435d38392335a40c32af5c48c9f3b5d112db; clean working tree.
- Command: `scripts/hpc/check_network.sbatch`; job 116268 on cs001.hpc.coe.
- Scheduler: FAILED as designed for a blocked route, exit 1:0; elapsed 41 seconds;
  batch MaxRSS 28.50M. One assigned GPU (0), unused by the diagnostic.
- Approximate allocated GPU-hours: 41/3600 = 0.01139. AllocTRES was truncated in
  returned accounting; use the submission request for this estimate.
- Logs: `logs/package-network-116268.out` and `.err` under the artifact root;
  complete stdout/accounting supplied in chat, no stderr content pasted.
- Results: all seven Conda/PyPI/PyTorch endpoint probes returned Errno 101,
  Network is unreachable; PACKAGE_NETWORK_BLOCKED. No downloads, installation,
  CUDA initialization, model imports or model metrics.
- Conclusion: the tested direct compute-node route is unavailable. The user
  subsequently supplied a proxy route; no proxy success evidence exists yet.
- Next action: configure proxy variables in ignored .env, stage the pinned source,
  then run the existing setup job. Its network preflight must pass before package
  installation. No separate connectivity allocation is needed.
- Gate: infrastructure passed; both model environment imports still PENDING.

## 2026-11-15 — Proxy connectivity passed; Conda bootstrap blocked by terms

- Commit: b8ab435d38392335a40c32af5c48c9f3b5d112db; clean working tree.
- Command: `scripts/hpc/setup_senna.sbatch`; job 116269 on cs001.hpc.coe.
- Scheduler: FAILED, exit 1:0; elapsed 8 seconds; batch MaxRSS 3576K.
- One assigned GPU (0); estimated allocated GPU-hours 8/3600 = 0.00222.
- Logs: `logs/senna-environment-116269.out` and `.err` under the artifact root;
  complete stdout/stderr and prior accounting returned in chat.
- Results: source VERIFIED at the pinned Senna revision; all seven package
  endpoint checks reachable via the supplied proxy; PACKAGE_NETWORK_OK.
- Failure: CondaToSNonInteractiveError for the defaults main/r channels at
  environment creation. No pip package installation or model imports occurred.
- Resolution prepared locally: replace the bootstrap defaults channel with
  conda-forge plus nodefaults; update preflight to test the new channel endpoints.
  No channel terms accepted; official Python minor and pip requirements unchanged.
- Local checks: 17 unit tests, shell/Python syntax, privacy/naming/size audit and
  whitespace checks passed. No local Linux package solve or HPC installation.
- Gate: previous proxy route PASSED; new bootstrap channel reachability and both
  model environment import gates PENDING. Do not begin dataset/model runs.
- Next action: retry Senna setup through the proxy; preserve any existing prefix
  and return its guard error if present, rather than removing files blindly.

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
