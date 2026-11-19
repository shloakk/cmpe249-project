#!/usr/bin/env bash
#SBATCH --job-name=vad-environment
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
"${HOST_PYTHON:-python3}" -m src.config
exec 9>"$EXPERIMENT_ROOT/logs/.vad-setup.lock"
flock -n 9 || { echo 'VAD environment setup already active' >&2; exit 1; }
printf 'UTC: '; date -u +%FT%TZ
printf 'Job: %s\nHost: ' "$SLURM_JOB_ID"; hostname
printf 'Commit: '; git rev-parse HEAD
printf 'Dirty status:\n'; git status --short
printf 'GPU assignment: %s\n' "${CUDA_VISIBLE_DEVICES:-UNSET}"
nvidia-smi
export APPTAINER_CACHEDIR="$EXPERIMENT_ROOT/caches/apptainer"
export APPTAINER_TMPDIR="$EXPERIMENT_ROOT/tmp"
export PYTHONDONTWRITEBYTECODE=1
image="$EXPERIMENT_ROOT/environments/vad.sif"
[[ ! -e "$image" ]] || { echo 'VAD image exists; inspect previous logs before rebuilding' >&2; exit 1; }
set -x
"${HOST_PYTHON:-python3}" -m src.upstream --root "$EXPERIMENT_ROOT/upstream" --verify-only vad
apptainer --version
apptainer build --fakeroot --ignore-fakeroot-command \
  "$image" containers/vad.def
sha256sum "$image"
env -u PYTHONPATH -u PYTHONHOME apptainer exec --nv \
    --bind "$repo:$repo" --bind "$EXPERIMENT_ROOT:$EXPERIMENT_ROOT" \
    "$image" python3 "$repo/scripts/environments/probe.py" \
    vad --upstream "$EXPERIMENT_ROOT/upstream/vad"
