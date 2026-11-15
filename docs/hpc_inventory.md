# SJSU HPC inventory

Source: user-supplied observations, recorded 2026-11-15. Not independently
executed or independently verified. Public paths deliberately use placeholders.

| Item | Reported value |
|---|---|
| Scheduler / account / QOS | SLURM / `coe` / `normal` |
| GPU | NVIDIA A100-PCIE-40GB; driver observed 590.44.01 |
| Request | `--gres=gpu:a100:1` |
| Partitions | `gpuqs` ≤2 days; `gpuqm` ≤7 days; `gpuql` ≤14 days |
| Visibility | One-GPU allocation set `CUDA_VISIBLE_DEVICES=0`; never override it |
| Software facilities | Anaconda, Miniconda modules; Apptainer, Singularity |
| Dataset | Shared full nuScenes trainval, read only |
| Derived annotations | legacy_2024 train, train-tiny and val pickles; compatibility unknown |
| CAN-bus | Not found in initial inspection; direct checks pending |
| Artifact directories | checkpoints, caches, outputs, logs, environments, tmp |

Repository: `/fs/atipa/home/<user>/cmpe249-project`.
Shared data: `/fs/atipa/data/<course>/datasets/nuscenes/v1.0-trainval`.
Derived: `/fs/atipa/data/<course>/derived/nuscenes/legacy_2024`.
Artifacts: `/fs/atipa/data/<course>/students/<user>/cmpe249-senna`.

The reference course environment reports Python 3.10.22, torch 2.1.2+cu118,
torchvision 0.16.2+cu118, MMCV 2.1.0, MMDetection 3.2.0 and MMDetection3D 1.4.0.
It is likely too new for official VAD. Never modify it. Environment setup will derive
separate environments from pinned official requirements. Physical `nvidia-smi`
output may show four GPUs; only the SLURM-assigned GPU is authorized.

Storage capacity, current modules, model imports and GPU runtime remain pending
returned HPC evidence. The smoke job uses 1 GPU, 2 CPUs, 8 GB RAM and at most 10 minutes
(upper bound 1/6 allocated GPU-hour); actual consumption must be recorded.
