# Local-to-HPC handoff

Development runs locally; commits are pushed before HPC execution. No HPC success is
assumed without complete returned evidence. All scripts use exported variables
from ignored `.env`. The YAML files are documentation templates only.

## Local validation and push

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/hpc/inventory.sh scripts/hpc/submit_smoke.sh scripts/hpc/smoke.sbatch
git push -u origin hpc-readiness
```

## HPC checkout

Set `REPO` to the existing HPC clone. Preserve any local edits before switching.

```bash
cd "$REPO"
git status --short --branch
git fetch origin
git switch --track origin/hpc-readiness
git pull --ff-only origin hpc-readiness
```

On subsequent updates use `git switch hpc-readiness` instead of
creating the branch again. Keep model environments out of this checkout.

## Private configuration and smoke

```bash
cp .env.example .env
# Edit ONLY ignored .env: set the five real absolute roots.
# Optionally export CMPE249_PYTHON to a reference Python interpreter.
set -a
source .env
set +a
mkdir -p "$CMPE249_ARTIFACT_ROOT"/{checkpoints,caches/huggingface,outputs,logs,environments,tmp}
bash scripts/hpc/submit_smoke.sh
```

Use the returned numeric job ID below. Submission runs only dependency-free
path validation on the login node; package/GPU probes execute inside SLURM.
No CUDA_VISIBLE_DEVICES override, installation, dataset write or model download.
The smoke checks optional reference torch if installed; missing torch is clearly
reported and does not satisfy either model environment requirement.

```bash
JOB_ID=<returned-job-id>
squeue -j "$JOB_ID"
sacct -j "$JOB_ID" --format=JobID,State,ExitCode,Elapsed,AllocTRES,MaxRSS
cat "$CMPE249_ARTIFACT_ROOT/logs/smoke-$JOB_ID.out"
cat "$CMPE249_ARTIFACT_ROOT/logs/smoke-$JOB_ID.err"
```

Expected: INVENTORY_OK and ENVIRONMENT_SMOKE_OK, scheduler COMPLETED, ExitCode 0:0.
CAN-bus absence and missing optional packages are diagnostic, not model-readiness
claims. Return the complete submission stdout/stderr, both log files and sacct
output (including failure details). If accounting is delayed, wait and retry
sacct. Retain logs privately because they contain actual paths and host details.
No experiment output exists at this stage. Tests and logs are not interchangeable:
passing local checks does not pass the HPC gate.

Environment pinning begins only after this evidence passes review; see
[readiness requirements](docs/readiness.md) for environment pinning policy.
