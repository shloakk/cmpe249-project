# VAD runtime container

`vad.def` is an optional recipe for systems that support privileged or correctly
configured fakeroot builds. The primary HPC workflow uses the persistent Conda
environment created by `scripts/environments/setup_vad.sh`; it does not require
a custom SIF image at runtime.

Use `scripts/hpc/setup_vad.sbatch` to validate the installed Conda runtime on one
GPU. Do not build on the login node or modify a shared environment. Packages,
caches and temporary files go into the configured artifact root.
See [environment provenance and limitations](../docs/environments.md).
