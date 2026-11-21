# HPC execution runbook

This guide separates network-enabled setup from scheduled compute. Site-specific
SLURM account, partition, QoS, and proxy values belong in private shell state;
they are not tracked by the repository.

Define the following private variables for your cluster:

```bash
export REPOSITORY_URL=https://github.com/<owner>/senna-error-aware-planning.git
export PROJECT_ROOT=/path/to/workspace/senna-error-aware-planning
export EXPERIMENT_ROOT=/path/to/writable/senna-experiments
GPU_SBATCH=(--partition=<gpu-partition> --account=<account> --qos=<qos>)
CPU_SBATCH=(--partition=<cpu-partition> --account=<account> --qos=<qos>)
```

## 1. Clone and configure

```bash
git clone "$REPOSITORY_URL" "$PROJECT_ROOT"
cd "$PROJECT_ROOT"
mkdir -p "$EXPERIMENT_ROOT"/{checkpoints,caches,outputs,logs,environments,tmp,upstream}
mkdir -p "$EXPERIMENT_ROOT/caches/huggingface"
cp .env.example .env
# Replace every placeholder in the ignored .env file.
set -a; source .env; set +a
python3 -m src.config
python3 -m unittest discover -s tests -v
```

## 2. Stage pinned sources and released assets

Run these commands on a network-enabled host:

```bash
python3 -m src.upstream --root "$EXPERIMENT_ROOT/upstream" senna vad

"$EXPERIMENT_ROOT/environments/senna/bin/python" \
  -m src.download_checkpoint \
  --output "$SENNA_CHECKPOINT_ROOT/Senna"

bash scripts/prepare_vad_data.sh
VAD_DATA="$EXPERIMENT_ROOT/vad_data"
SENNA_PY="$EXPERIMENT_ROOT/environments/senna/bin/python"
"$SENNA_PY" -m pip install gdown
"$SENNA_PY" -m gdown 1OVd6Rw2wYjT_ylihCixzF6_olrAQsctx \
  -O "$VAD_DATA/vad_nuscenes_infos_temporal_train.pkl"
"$SENNA_PY" -m gdown 16DZeA-iepMCaeyi57XSXL3vYyhrOQI9S \
  -O "$VAD_DATA/vad_nuscenes_infos_temporal_val.pkl"
"$SENNA_PY" -m gdown 1KgCC_wFqPH0CQqdr6Pp2smBX5ARPaqne \
  -O "$SENNA_CHECKPOINT_ROOT/VAD_tiny_stage_2.pth"
```

Verify that the downloaded files are binary artifacts rather than HTML error
pages:

```bash
file "$VAD_DATA"/*.pkl "$SENNA_CHECKPOINT_ROOT/VAD_tiny_stage_2.pth"
du -h "$VAD_DATA"/*.pkl "$SENNA_CHECKPOINT_ROOT/VAD_tiny_stage_2.pth"
```

## 3. Validate Senna and run a small inference pilot

```bash
sbatch "${GPU_SBATCH[@]}" --parsable --chdir="$PWD" \
  --output="$EXPERIMENT_ROOT/logs/senna-validation-%j.out" \
  --error="$EXPERIMENT_ROOT/logs/senna-validation-%j.err" \
  scripts/hpc/validate_senna.sbatch

LIMIT=16 SPLIT=val sbatch "${GPU_SBATCH[@]}" --parsable --chdir="$PWD" \
  --output="$EXPERIMENT_ROOT/logs/senna-pilot-%j.out" \
  --error="$EXPERIMENT_ROOT/logs/senna-pilot-%j.err" \
  scripts/hpc/senna_inference.sbatch
```

Require `COMPLETED`, exit code `0:0`, `SENNA_IMPORTS_OK`, and 16 prediction
records before starting the full cache.

## 4. Cache validation predictions and audit errors

```bash
SPLIT=val sbatch "${GPU_SBATCH[@]}" --parsable --chdir="$PWD" \
  --output="$EXPERIMENT_ROOT/logs/senna-val-%j.out" \
  --error="$EXPERIMENT_ROOT/logs/senna-val-%j.err" \
  scripts/hpc/senna_inference.sbatch

SPLIT=val sbatch "${CPU_SBATCH[@]}" --parsable --chdir="$PWD" \
  --output="$EXPERIMENT_ROOT/logs/senna-audit-%j.out" \
  --error="$EXPERIMENT_ROOT/logs/senna-audit-%j.err" \
  scripts/hpc/error_audit.sbatch
```

Primary outputs:

```text
outputs/senna/val.jsonl
outputs/audit/val/metrics.json
outputs/audit/val/speed_confusion.csv
outputs/audit/val/path_confusion.csv
```

## 5. Validate the VAD runtime and evaluate C0

```bash
sbatch "${GPU_SBATCH[@]}" --parsable --chdir="$PWD" \
  --output="$EXPERIMENT_ROOT/logs/vad-environment-%j.out" \
  --error="$EXPERIMENT_ROOT/logs/vad-environment-%j.err" \
  scripts/hpc/setup_vad.sbatch

export VAD_CHECKPOINT="$SENNA_CHECKPOINT_ROOT/VAD_tiny_stage_2.pth"
export VAD_ROOT="$EXPERIMENT_ROOT/upstream/vad"
export VAD_CONFIG="$EXPERIMENT_ROOT/caches/vad_configs/c0.py"
"$EXPERIMENT_ROOT/environments/senna/bin/python" \
  scripts/prepare_vad_baseline.py --vad-root "$VAD_ROOT" \
  --data-root "$EXPERIMENT_ROOT/vad_data" --output "$VAD_CONFIG"

CONDITION=c0 sbatch "${GPU_SBATCH[@]}" --parsable --chdir="$PWD" \
  --output="$EXPERIMENT_ROOT/logs/vad-c0-%j.out" \
  --error="$EXPERIMENT_ROOT/logs/vad-c0-%j.err" \
  scripts/hpc/vad_eval.sbatch
```

Each evaluation writes to `outputs/vad/<condition>/<job-id>/` by default, so
reruns cannot replace earlier results. Set a unique `RUN_ID` before submission
when a descriptive run name is preferred. Require a nonempty
`outputs/vad/c0/<run-id>/planning_metrics.json` before training an adapter.
Each run also creates an isolated runtime view that maps the released
`./data/nuscenes/...` annotation paths to `$EXPERIMENT_ROOT/vad_data`; the
pinned upstream checkout remains unchanged and concurrent runs do not share it.
The generated C0-C3 configs force the original BGR, unit-standard-deviation
image normalization required by the released VAD checkpoint. Do not replace it
with the newer ImageNet normalization unless training a matching checkpoint.

## 6. Prepare C1-C3

```bash
SENNA_PY="$EXPERIMENT_ROOT/environments/senna/bin/python"
VAD_DATA="$EXPERIMENT_ROOT/vad_data"
TRAIN_MANIFEST="$EXPERIMENT_ROOT/caches/manifests/train.json"
TRAIN_CACHE="$EXPERIMENT_ROOT/caches/manifests/train_gt.jsonl"
AUDIT="$EXPERIMENT_ROOT/outputs/audit/val/metrics.json"
VAD_ROOT="$EXPERIMENT_ROOT/upstream/vad"

"$SENNA_PY" -m src.senna_cache.build_manifest \
  --annotation "$VAD_DATA/vad_nuscenes_infos_temporal_train.pkl" \
  --data-root "$NUSCENES_DATA_ROOT" --output "$TRAIN_MANIFEST"
"$SENNA_PY" -m src.senna_cache.manifest_to_cache \
  --manifest "$TRAIN_MANIFEST" --output "$TRAIN_CACHE"

for CONDITION in c1 c2 c3; do
  "$SENNA_PY" scripts/prepare_condition.py \
    --vad-root "$VAD_ROOT" --condition "$CONDITION" \
    --cache "$TRAIN_CACHE" --audit "$AUDIT" --data-root "$VAD_DATA" \
    --output "$EXPERIMENT_ROOT/caches/vad_configs/$CONDITION.py"
done
```

## 7. Train C1-C3 independently

Run one condition per allocation or worker:

```bash
export CONDITION=c1
export VAD_CHECKPOINT="$SENNA_CHECKPOINT_ROOT/VAD_tiny_stage_2.pth"
export VAD_CONFIG="$EXPERIMENT_ROOT/caches/vad_configs/$CONDITION.py"
sbatch "${GPU_SBATCH[@]}" --parsable --chdir="$PWD" \
  --output="$EXPERIMENT_ROOT/logs/vad-$CONDITION-train-%j.out" \
  --error="$EXPERIMENT_ROOT/logs/vad-$CONDITION-train-%j.err" \
  scripts/hpc/vad_train_adapter.sbatch
```

Change `CONDITION` to `c2` or `c3` for the other runs. Record the Git commit,
config, seed, checkpoint, elapsed time, memory, and allocated GPU for every run.
Training outputs are isolated under `outputs/vad/<condition>/<run-id>/train`.

## 8. Evaluate with real Senna predictions

```bash
REAL_CONFIG="$EXPERIMENT_ROOT/caches/vad_configs/real.py"
"$SENNA_PY" scripts/prepare_condition.py \
  --vad-root "$VAD_ROOT" --condition real \
  --cache "$EXPERIMENT_ROOT/outputs/senna/val.jsonl" \
  --audit "$AUDIT" --data-root "$VAD_DATA" --output "$REAL_CONFIG"
```

Evaluate each trained C1-C3 checkpoint with `VAD_CONFIG=$REAL_CONFIG` and
`scripts/hpc/vad_eval.sbatch`. Then aggregate:

```bash
"$SENNA_PY" scripts/compare_results.py \
  --root "$EXPERIMENT_ROOT/outputs/vad" \
  --output "$EXPERIMENT_ROOT/outputs/vad/results_table.csv"
```
