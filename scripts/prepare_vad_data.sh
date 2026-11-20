#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo"
set -a
source .env
set +a
target="$EXPERIMENT_ROOT/vad_data"
mkdir -p "$target"
for name in samples sweeps v1.0-trainval; do
  if [[ ! -e "$target/$name" ]]; then
    ln -s "$NUSCENES_DATA_ROOT/$name" "$target/$name"
  fi
done

# nuScenesMap expects expansion JSON files below dataroot/maps/expansion. The
# shared dataset keeps them beside v1.0-trainval under extras/expansion, so the
# writable VAD view must combine both locations without modifying shared data.
maps_source="$NUSCENES_DATA_ROOT/maps"
maps_target="$target/maps"
expansion_source=""
for candidate in \
  "$maps_source/expansion" \
  "$(dirname "$NUSCENES_DATA_ROOT")/extras/expansion"; do
  if [[ -d "$candidate" ]]; then
    expansion_source="$candidate"
    break
  fi
done
[[ -d "$maps_source" ]] || {
  echo "Missing nuScenes maps directory: $maps_source" >&2
  exit 1
}
[[ -n "$expansion_source" ]] || {
  echo "Missing nuScenes map expansion data" >&2
  exit 1
}
if [[ -L "$maps_target" ]]; then
  unlink "$maps_target"
elif [[ -e "$maps_target" && ! -d "$maps_target" ]]; then
  echo "VAD maps path is not a directory: $maps_target" >&2
  exit 1
fi
mkdir -p "$maps_target"
shopt -s nullglob
for source in "$maps_source"/*; do
  name=$(basename "$source")
  [[ "$name" == expansion ]] && continue
  [[ -e "$maps_target/$name" || -L "$maps_target/$name" ]] \
    || ln -s "$source" "$maps_target/$name"
done
[[ -e "$maps_target/expansion" || -L "$maps_target/expansion" ]] \
  || ln -s "$expansion_source" "$maps_target/expansion"

printf 'VAD data view: %s\n' "$target"
printf 'Map expansion: %s\n' "$expansion_source"
printf 'Still required in this directory:\n'
for file in vad_nuscenes_infos_temporal_train.pkl \
  vad_nuscenes_infos_temporal_val.pkl; do
  [[ -f "$target/$file" ]] || printf '  MISSING %s\n' "$file"
done
