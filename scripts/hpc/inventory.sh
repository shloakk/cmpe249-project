#!/usr/bin/env bash
# Read-only inventory: no recursive scans, package installation or model loading.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$repo"
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
python_bin=${HOST_PYTHON:-python3}
printf 'UTC time: '; date -u +%FT%TZ
printf 'Host: '; hostname
printf 'Git commit: '; git rev-parse HEAD
printf 'Git status:\n'; git status --short
printf 'Python command: %q\n' "$python_bin"
"$python_bin" --version
"$python_bin" -m src.config
printf 'Storage capacity:\n'
df -h "$EXPERIMENT_ROOT"
printf 'CAN-bus direct candidate checks (absence is informational during inventory):\n'
for candidate in "$NUSCENES_DATA_ROOT/can_bus" "$(dirname "$NUSCENES_DATA_ROOT")/can_bus" "$EXPERIMENT_ROOT/can_bus"; do
  if [[ -d "$candidate" ]]; then printf 'FOUND %s\n' "$candidate"; else printf 'MISSING %s\n' "$candidate"; fi
done
printf 'Derived annotation presence only; compatibility NOT established:\n'
for name in nuscenes_infos_train.pkl nuscenes_infos_train-tiny.pkl nuscenes_infos_val.pkl; do
  if [[ -r "$NUSCENES_DERIVED_ROOT/$name" ]]; then printf 'READABLE %s\n' "$name"; else printf 'MISSING %s\n' "$name"; fi
done
printf 'Optional infrastructure commands:\n'
for program in apptainer singularity conda; do command -v "$program" || true; done
printf 'INVENTORY_OK (no model environment or dataset compatibility claim)\n'
