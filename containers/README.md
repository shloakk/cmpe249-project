# Environment setup awaits the HPC smoke test

Do not build an image or install the course environment as the VAD environment.
Environment setup must inspect pinned official requirements before selecting any dependency
versions. Prefer Apptainer if the official legacy VAD stack cannot be installed
reliably on the host. Store built images under the ignored artifact root.
