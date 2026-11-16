# VAD runtime container

`vad.def` is a candidate Apptainer recipe based on the pinned official VAD
installation guide. It is not built or validated yet. Run it from the repository
root so `%files` resolves `configs/vad-constraints.txt`. The build requires
fakeroot/user namespace support, outbound network and temporary writable space.
The runtime requires the host NVIDIA driver via `apptainer exec --nv`.

Use `scripts/hpc/setup_vad.sbatch` after the Senna environment attempt is reviewed.
Do not build on the login node or modify the course environment. Built images,
package caches and temporary files go into the configured artifact root.
See [environment provenance and limitations](../docs/environments.md).
