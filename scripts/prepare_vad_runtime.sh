#!/usr/bin/env bash
set -euo pipefail

[[ $# -eq 3 ]] || {
  echo "Usage: $0 RUNTIME_DIR VAD_ROOT VAD_DATA_ROOT" >&2
  exit 2
}

runtime=$1
vad_root=$2
data_root=$3

[[ -d "$vad_root/projects" ]] || {
  echo "Missing VAD projects directory: $vad_root/projects" >&2
  exit 1
}
[[ -d "$data_root" ]] || {
  echo "Missing VAD data root: $data_root" >&2
  exit 1
}

mkdir -p "$runtime/data"

link_checked() {
  local target=$1
  local link=$2
  if [[ -L "$link" ]]; then
    [[ "$(readlink -f "$link")" == "$(readlink -f "$target")" ]] || {
      echo "Runtime link points elsewhere: $link" >&2
      exit 1
    }
  elif [[ -e "$link" ]]; then
    echo "Runtime path already exists and is not a symlink: $link" >&2
    exit 1
  else
    ln -s "$target" "$link"
  fi
}

link_checked "$vad_root/projects" "$runtime/projects"
link_checked "$data_root" "$runtime/data/nuscenes"

printf 'VAD runtime view: %s\n' "$runtime"
printf '  projects -> %s\n' "$(readlink -f "$runtime/projects")"
printf '  data/nuscenes -> %s\n' \
  "$(readlink -f "$runtime/data/nuscenes")"
