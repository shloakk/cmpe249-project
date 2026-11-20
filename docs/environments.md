# Runtime environments

Senna and VAD require separate runtimes.

## Senna

The Senna inference environment uses Python 3.10, PyTorch 2.0.1 with CUDA 11.8,
torchvision 0.15.2, and transformers 4.31.0. The selected inference profile is
derived from the pinned upstream requirements; training-only packages are not
installed.

```bash
bash scripts/environments/setup_senna.sh
```

If a reviewed partial prefix already exists, set `RESUME_SENNA_ENV=1`. The
installer validates Python and PyTorch versions before reusing it.

## VAD

VAD uses a persistent Conda prefix with Python 3.8, PyTorch 1.9.1 with CUDA
11.1, MMCV-full 1.4.0, MMDetection 2.14.0, and MMDetection3D 0.17.1. The legacy
CUDA extensions are compiled in an unmodified CUDA 11.1 development image;
the resulting environment runs directly under SLURM.

```bash
srun --partition=cpuqs --account="$SLURM_ACCOUNT" --qos="$SLURM_QOS" \
  --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=16G --time=01:30:00 \
  --chdir="$PWD" bash scripts/environments/setup_vad.sh

sbatch scripts/hpc/setup_vad.sbatch  # one-GPU runtime validation
```

The installer stores packages, source checkouts, and caches under
`EXPERIMENT_ROOT`. The validation job tests actual CUDA execution, MMCV ops,
the VAD plugin, pinned package versions, and dependency consistency.
