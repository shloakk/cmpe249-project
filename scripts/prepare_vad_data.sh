#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo"
set -a
source .env
set +a
target="$EXPERIMENT_ROOT/vad_data"
mkdir -p "$target"
for name in samples sweeps maps v1.0-trainval; do
  if [[ ! -e "$target/$name" ]]; then
    ln -s "$NUSCENES_DATA_ROOT/$name" "$target/$name"
  fi
done
printf 'VAD data view: %s\n' "$target"
printf 'Still required in this directory:\n'
for file in vad_nuscenes_infos_temporal_train.pkl \
  vad_nuscenes_infos_temporal_val.pkl; do
  [[ -f "$target/$file" ]] || printf '  MISSING %s\n' "$file"
done
