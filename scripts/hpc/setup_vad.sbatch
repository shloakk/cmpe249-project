#!/usr/bin/env bash
#SBATCH --job-name=vad-environment
#SBATCH --partition=gpuqs
#SBATCH --account=coe
#SBATCH --qos=normal
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
set -euo pipefail
: "${SLURM_JOB_ID:?Submit through sbatch}"
cd "${SLURM_SUBMIT_DIR:?}"
repo=$PWD
set -a
source .env
set +a
"${CMPE249_PYTHON:-python3}" -m src.config
exec 9>"$CMPE249_ARTIFACT_ROOT/logs/.vad-setup.lock"
flock -n 9 || { echo 'VAD environment setup already active' >&2; exit 1; }
printf 'UTC: '; date -u +%FT%TZ
printf 'Job: %s\nHost: ' "$SLURM_JOB_ID"; hostname
printf 'Commit: '; git rev-parse HEAD
printf 'Dirty status:\n'; git status --short
printf 'GPU assignment: %s\n' "${CUDA_VISIBLE_DEVICES:-UNSET}"
nvidia-smi
export APPTAINER_CACHEDIR="$CMPE249_ARTIFACT_ROOT/caches/apptainer"
export APPTAINER_TMPDIR="$CMPE249_ARTIFACT_ROOT/tmp"
export PYTHONDONTWRITEBYTECODE=1
image="$CMPE249_ARTIFACT_ROOT/environments/vad.sif"
[[ ! -e "$image" ]] || { echo 'VAD image exists; inspect previous logs before rebuilding' >&2; exit 1; }
set -x
"${CMPE249_PYTHON:-python3}" -m src.upstream --root "$CMPE249_ARTIFACT_ROOT/upstream" --verify-only vad
apptainer --version
apptainer build --fakeroot "$image" containers/vad.def
sha256sum "$image"
env -u PYTHONPATH -u PYTHONHOME apptainer exec --nv \
    --bind "$repo:$repo" --bind "$CMPE249_ARTIFACT_ROOT:$CMPE249_ARTIFACT_ROOT" \
    "$image" python3 "$repo/scripts/environments/probe.py" \
    vad --upstream "$CMPE249_ARTIFACT_ROOT/upstream/vad"
