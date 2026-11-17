# Dataset contract

Use the full nuScenes `v1.0-trainval` payload. `NUSCENES_DATA_ROOT` must point to
the directory containing `samples/`, `sweeps/`, `maps/`, and `v1.0-trainval/`.
The repository never writes to this location.

VAD uses its released temporal train/validation annotation files. Store these in
the writable view created by `scripts/prepare_vad_data.sh`:

```text
$EXPERIMENT_ROOT/vad_data/
├── maps -> $NUSCENES_DATA_ROOT/maps
├── samples -> $NUSCENES_DATA_ROOT/samples
├── sweeps -> $NUSCENES_DATA_ROOT/sweeps
├── v1.0-trainval -> $NUSCENES_DATA_ROOT/v1.0-trainval
├── vad_nuscenes_infos_temporal_train.pkl
└── vad_nuscenes_infos_temporal_val.pkl
```

Manifest construction verifies six camera paths and rejects samples with an
incomplete three-second future trajectory. The generated manifest records the
navigation-command source so fallback route commands remain auditable.

Do not commit datasets, annotations, manifests, prediction caches, or weights.
