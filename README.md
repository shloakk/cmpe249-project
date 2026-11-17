# Error-Aware Meta-Action Conditioning for Autonomous Planning

This repository evaluates whether a trajectory planner becomes more robust when
its training-time conditioning reflects the measured error distribution of an
upstream vision-language model.

The pipeline runs the released Senna-VLM on nuScenes, records speed and path
meta-actions, audits its joint confusion distribution, and conditions a frozen
VAD-Tiny planner through a small residual adapter. The complete Senna-E2E system
is not publicly available, so the planner integration is explicitly a
Senna-style reconstruction built on the released VAD implementation.

## Experimental design

| ID | Planner conditioning | Role |
|---|---|---|
| C0 | Released VAD-Tiny without an adapter | Baseline |
| C1 | Ground-truth speed and path actions | Oracle conditioning |
| C2 | Uniform corruption at the measured Senna error rate | Matched-rate control |
| C3 | Empirical joint Senna confusion distribution | Error-aware conditioning |

C1-C3 share the same adapter architecture, initialization, seed, optimizer,
data order, and training schedule. The adapter's final projection is initialized
to zero, preserving the released planner output before optimization. All
non-adapter parameters remain frozen.

## Pipeline

1. Convert VAD-style nuScenes annotations into six-camera Senna manifests.
2. Run deterministic Senna inference into a resumable JSONL cache.
3. Export parse rates, confusion matrices, per-class metrics, and joint errors.
4. Build C1-C3 configurations from the measured validation distribution.
5. Train only the residual meta-action adapter.
6. Evaluate C0-C3 with the same cached real Senna predictions.
7. Export a report-ready planning metrics table.

## Repository layout

```text
configs/             Path templates, dependency constraints, upstream locks
containers/          Reproducible VAD Apptainer definition
integrations/vad/    Additive VAD detector/head integration
scripts/hpc/         SLURM jobs for validation, inference, training, evaluation
src/error_audit/     Prediction parsing and confusion analysis
src/planner_adapter/ Standalone residual adapter
src/senna_cache/     Manifest generation and resumable inference
tests/               Dependency-light unit tests
```

## Quick start

```bash
cp .env.example .env
# Edit .env with local absolute paths.
set -a; source .env; set +a
python3 -m src.config
python3 -m unittest discover -s tests -v
```

See [HPC_RUNBOOK.md](HPC_RUNBOOK.md) for end-to-end execution and
[REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the artifact contract. Dataset and
checkpoint files are intentionally excluded from Git.

## Upstream provenance

Official source revisions are pinned in `configs/upstream-lock.json`:

- `hustvl/Senna` for released VLM inference;
- `hustvl/VAD` for the downstream planning baseline;
- `open-mmlab/mmdetection3d` for the legacy VAD runtime.

The reported planning metrics are open-loop proxies and do not establish
closed-loop or real-world driving safety.
