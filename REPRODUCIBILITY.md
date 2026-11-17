# Reproducibility contract

Every experiment must retain:

- the exact Git commit and a clean/dirty status record;
- the pinned upstream revisions in `configs/upstream-lock.json`;
- the resolved Python packages or container digest;
- the dataset split, annotation checksum, and manifest checksum;
- the condition, seed, model checkpoint, and generated config;
- scheduler state, elapsed time, allocated resources, and peak memory;
- raw predictions, parsed actions, aggregate metrics, and failure logs.

Generated data, weights, caches, environments, scheduler logs, and credentials
must remain outside Git. Runtime paths are exported from an ignored `.env` file.
Shared datasets are treated as read-only; writable artifacts live below
`EXPERIMENT_ROOT`.

Run dependency-light checks before submitting jobs:

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/hpc/*.sh scripts/hpc/*.sbatch scripts/environments/*.sh \
  scripts/prepare_vad_data.sh
```

An experiment is considered complete only when the scheduler reports success,
the expected terminal marker is present, and every expected output passes a
nonempty/schema check. A passing unit test does not substitute for a model or GPU
validation run.
