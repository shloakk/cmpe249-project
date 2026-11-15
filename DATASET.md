# Dataset contract

Use the shared nuScenes **v1.0-trainval** dataroot read-only. Do not download or
copy the full dataset and do not substitute mini. Configure the root containing
`samples/`, `sweeps/`, `maps/`, and `v1.0-trainval/` in `.env`.
Existing derived `nuscenes_infos_{train,train-tiny,val}.pkl` files are candidates
only: presence does not imply compatibility with VAD. Do not unpickle untrusted
files; dataset validation must establish provenance/trust before inspecting their schema
and compare required fields with the pinned official loader.

The inventory checks directory readability, storage capacity, and direct CAN-bus
candidates only. It does not validate tables, image completeness or annotations.
Dataset validation must verify tables and all required inputs for a deterministic 50-token
manifest from trainval/validation, recording split and provenance. Never write
new annotations into shared storage.

CAN-bus was not found in the user-reported initial inspection. The inventory
checks `DATA_ROOT/can_bus`, its parent's `can_bus`, and
`ARTIFACT_ROOT/can_bus` directly, without recursive searching. Absence is reported,
not treated as evidence that model preprocessing is ready. If required and
absent, dataset preparation must document the official expansion-only download and build a
symlink-based local dataroot view in the writable area before preprocessing.
