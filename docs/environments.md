# Environment provenance and execution

The returned infrastructure smoke passed. Environment installation and model
imports have NOT run. Use separate environments; never install into the shared
course environment. No model checkpoint is downloaded by these recipes.

## Official sources inspected

`configs/upstream-lock.json` stores full Git revisions and SHA-256 hashes for
the inspected upstream requirements/instructions. The fetch utility refuses
existing checkouts with the wrong commit, any dirty status or mismatched files.
Source checkouts are stored under `$CMPE249_ARTIFACT_ROOT/upstream`.

| Source | Evidence | Recipe choice |
|---|---|---|
| [Senna README](https://github.com/hustvl/Senna/blob/31a3a2336e9494c254b612665fe55e95f67e9cae/README.md) and [requirements](https://github.com/hustvl/Senna/blob/31a3a2336e9494c254b612665fe55e95f67e9cae/requirements.txt) | Python 3.10; torch 2.0.1+cu118; torchvision 0.15.2+cu118; transformers 4.31.0 | Install complete root requirements unchanged in an isolated Conda prefix |
| [VAD install guide](https://github.com/hustvl/VAD/blob/1688c4b1c3a9e2e7873ca9700ff8058170c0e3c8/docs/install.md) and [export](https://github.com/hustvl/VAD/blob/1688c4b1c3a9e2e7873ca9700ff8058170c0e3c8/requirements.txt) | Guide: Python 3.8; torch 1.9.1+cu111; MMCV-full 1.4.0; mmdet 2.14.0; mmseg 0.14.1; mmdet3d 0.17.1; nuScenes devkit 1.1.9 | Legacy stack in a CUDA 11.1 development container |

VAD's requirements file is a Conda export containing PyPI entries, not a pip
requirements file. It records Python 3.7.16 while its install guide says 3.8;
this recipe follows the guide's Python 3.8. `vad-constraints.txt` mechanically
projects all `pypi_0` version entries into pip constraints, including the exported
timm 0.6.12 and numpy 1.19.5. Constraints do not install unrelated CARLA/Jupyter
packages. The recipe requests the documented VAD stack and resolves dependencies
under those constraints. This is a documented reconstruction of installation,
not a byte-for-byte recreation of the authors' environment.

Senna's nested `llava_next/pyproject.toml` describes a different training stack;
it is not installed on top of the root requirements. The evaluator uses root
`llava` modules via their source path. The probe imports those modules directly
and checks the Senna model loader exists, avoiding a misleading top-level import
success caused by upstream's broad exception handler.

## Senna setup — next run

Push this commit locally, then on HPC from the existing project directory:

```bash
git pull --ff-only origin hpc-readiness
set -a
source .env
set +a
sbatch --parsable --chdir="$PWD" \
  --output="$CMPE249_ARTIFACT_ROOT/logs/senna-environment-%j.out" \
  --error="$CMPE249_ARTIFACT_ROOT/logs/senna-environment-%j.err" \
  scripts/hpc/setup_senna.sbatch
```

Setup creates `$CMPE249_ARTIFACT_ROOT/environments/senna`. Conda executable
availability was observed during the smoke test, but compute-node network access
and environment resolution are unverified. Torch is installed first because
DeepSpeed metadata generation may import it. `DS_BUILD_OPS=0` disables optional
DeepSpeed ahead-of-time extension builds for this inference-only setup; package
versions remain the official ones. This build setting is a recorded deviation,
not a model-logic change. The probe does not run training or load weights.

The job requests one A100, 4 CPUs, 32 GB RAM, at most 2 hours (up to 2 allocated
GPU-hours). It uses caches and temp space under the artifact root. A lock blocks
concurrent setup, and any existing environment prefix causes an explicit stop
rather than overwriting a successful or partially installed environment.
If it fails, preserve the directory and return logs before deciding how to retry.
Do not silently remove unavailable packages or upgrade dependency pins.

## VAD container — prepared, run after reviewing the Senna attempt

```bash
sbatch --parsable --chdir="$PWD" \
  --output="$CMPE249_ARTIFACT_ROOT/logs/vad-environment-%j.out" \
  --error="$CMPE249_ARTIFACT_ROOT/logs/vad-environment-%j.err" \
  scripts/hpc/setup_vad.sbatch
```

This job also requests one A100, 4 CPUs, 32 GB and up to 2 hours. It builds
`$CMPE249_ARTIFACT_ROOT/environments/vad.sif`, prints its SHA-256, then imports
MMCV CUDA ops, MMDetection3D and the actual VAD plugin and runs CUDA NMS. It does
not install model weights or evaluate a dataset. A100 compilation uses compute
capability 8.0; this is a hardware-specific build setting. No job changes
`CUDA_VISIBLE_DEVICES`. The NVIDIA driver is supplied with `--nv` at runtime.

Apptainer presence does not prove fakeroot/user-namespace builds are allowed.
If the build is blocked, preserve the full error and prepare a supported external
build/transfer route. Do not try a privileged build on the login node.

## Required evidence and remaining reproducibility limits

For each attempt, replace JOB_ID and NAME (`senna` or `vad`) below:

```bash
sacct -j "$JOB_ID" --format=JobID,State,ExitCode,Elapsed,AllocTRES,MaxRSS
cat "$CMPE249_ARTIFACT_ROOT/logs/$NAME-environment-$JOB_ID.out"
cat "$CMPE249_ARTIFACT_ROOT/logs/$NAME-environment-$JOB_ID.err"
```

Return complete submission stdout/stderr, both log files and accounting. A model
environment passes only with COMPLETED, exit 0:0, its `SENNA_IMPORTS_OK` or
`VAD_IMPORTS_OK` marker, correct package versions, and exactly one CUDA-visible
GPU. Until both pass, dataset processing and checkpoint downloads remain blocked.

These are candidate recipes, not tested fully resolved environment locks. Conda
bootstrap builds, dependencies absent from the original exports, OS packages and
the tagged CUDA base image can still vary. Successful runs must retain explicit
Conda listings, pip freeze/check output, logs, container hash and build metadata;
pin the resolved image digest and missing transitive versions before calling
rebuilds fully locked. Shared filesystem free space is not a verified user quota.
