#!/usr/bin/env bash
#SBATCH --job-name=senna-smoke
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
# Submit with --chdir and --output/--error as documented in REPRODUCIBILITY.md.
set -euo pipefail
: "${SLURM_JOB_ID:?Run this script through sbatch}"
: "${SLURM_SUBMIT_DIR:?Missing SLURM submission directory}"
cd "$SLURM_SUBMIT_DIR"
set -a
source .env
set +a
# A second submission must wait/fail rather than overlap this smoke check.
exec 9>"$EXPERIMENT_ROOT/logs/.environment-smoke.lock"
flock -n 9 || { echo 'Another environment smoke job is active' >&2; exit 1; }
printf 'Job ID: %s\nCUDA_VISIBLE_DEVICES: %s\n' "$SLURM_JOB_ID" "${CUDA_VISIBLE_DEVICES:-UNSET}"
[[ -n "${CUDA_VISIBLE_DEVICES:-}" && "$CUDA_VISIBLE_DEVICES" != *,* && "$CUDA_VISIBLE_DEVICES" != -1 ]] || { echo 'Expected one SLURM-assigned GPU' >&2; exit 1; }
printf 'Command: bash scripts/hpc/inventory.sh\n'
bash scripts/hpc/inventory.sh
printf 'Physical GPU inventory (may show devices outside this allocation):\n'
nvidia-smi
# Inventory needs no torch install; model environments require torch and one GPU.
python_bin=${HOST_PYTHON:-python3}
printf 'Command: %q - (reference package/GPU probe)\n' "$python_bin"
"$python_bin" - <<'PYTHON'
import importlib.metadata as metadata
import importlib.util
import json
for name in ('torch', 'torchvision', 'mmcv', 'mmcv-full', 'mmdet', 'mmdet3d'):
    try:
        print(name, metadata.version(name))
    except metadata.PackageNotFoundError:
        print(name, 'NOT_INSTALLED')
if importlib.util.find_spec('torch') is not None:
    import torch
    print(json.dumps({'torch_cuda': torch.version.cuda, 'cuda_available': torch.cuda.is_available(),
                      'visible_gpu_count': torch.cuda.device_count()}))
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise SystemExit('Reference torch must see exactly one GPU when installed')
    print('assigned_gpu:', torch.cuda.get_device_name(0))
else:
    print('Reference torch unavailable; model environment imports remain PENDING')
PYTHON
printf 'ENVIRONMENT_SMOKE_OK; model environment checks remain PENDING\n'
