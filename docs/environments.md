# Environment provenance and execution

The returned infrastructure smoke passed. Senna setup job 116267 failed on
compute-node GitHub connectivity before environment creation. Package installation
and model imports have NOT run. Do not retry setup until connectivity is reviewed. Use separate environments; never install into the shared
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

## Connectivity diagnosis — next run

Job 116267 failed after 2 minutes 12 seconds with exit 1:0 while cloning Senna
from GitHub on the compute node. This demonstrates GitHub connectivity failure
for that attempt; it does not establish whether PyPI, Conda or the PyTorch wheel
server are blocked. Do not spend another installation allocation guessing.

After pulling the next commit, run the small HEAD-only check on the login node:

```bash
set -a
source .env
set +a
python3 -m src.network_check
```

Then submit the same check on a compute node:

```bash
sbatch --parsable --chdir="$PWD" \
  --output="$CMPE249_ARTIFACT_ROOT/logs/package-network-%j.out" \
  --error="$CMPE249_ARTIFACT_ROOT/logs/package-network-%j.err" \
  scripts/hpc/check_network.sbatch
```

Return the complete login output, submission output, SLURM accounting, and both
`package-network-<jobid>.out`/`.err` files. The job requests one GPU only because
the confirmed partition is a GPU partition; it does not initialize CUDA or run
model code. Maximum allocation is 3 minutes (0.05 GPU-hours). HTTP probes have
10-second socket timeouts and run concurrently; no packages are downloaded.
Success is PACKAGE_NETWORK_OK and exit 0:0. A missing route intentionally prints
PACKAGE_NETWORK_BLOCKED and exits 1; return those failures without retrying setup.
A root-path 404 from the Python file host proves reachability only, not a usable
wheel download. No probe result guarantees dependency availability or solving.

If compute package access is blocked, prepare an offline environment/package
transfer route or request the cluster's supported proxy/mirror after reviewing
the evidence. Do not install packages or solve large environments on the login
node. No network bypass or environment-version substitution is authorized by
these checks. The VAD container also needs Docker registry, OS-package and
MMDetection3D GitHub access; a successful Senna package check does not validate
those additional destinations.

## Stage source before any future setup job

Use the network-enabled login node for source staging only (not environment
creation). Existing source directories must be clean and at the pinned revision:

```bash
python3 -m src.upstream --root "$CMPE249_ARTIFACT_ROOT/upstream" senna vad
```

The utility now fetches complete Git objects rather than a partial clone that
could need later network access. It never resets or removes an existing checkout.
If the failed clone left an incomplete directory, preserve it and return the
error before changing it. Compute-node setup uses `--verify-only`, so missing
sources produce an immediate error without attempting GitHub access.

## Senna setup — after connectivity review


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
