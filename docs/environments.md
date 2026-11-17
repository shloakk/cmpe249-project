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

VAD is isolated in an Apptainer image because its released stack uses Python
3.8, PyTorch 1.9.1 with CUDA 11.1, MMCV-full 1.4.0, MMDetection 2.14.0, and
MMDetection3D 0.17.1.

```bash
sbatch scripts/hpc/setup_vad.sbatch
```

The build uses `containers/vad.def`, stores caches under `EXPERIMENT_ROOT`, and
validates actual MMCV CUDA operations before accepting the image.
