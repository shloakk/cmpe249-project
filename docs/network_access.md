# HPC network access

Direct compute-node package access failed in job 116268. The user subsequently
supplied an HTTP proxy route. Job 116269 verified the staged Senna source and
reached all seven package endpoints through that proxy. Installation then stopped
at the defaults-channel terms prompt. No offline transfer is currently required
by this evidence; the new conda-forge endpoints still need their setup preflight.

Add the supplied `http_proxy` and `https_proxy` values only to the ignored `.env`.
The existing SLURM scripts load and export that file, and Git, pip, Conda and the
Python connectivity probe inherit those settings. Keep the private proxy address
out of tracked examples. Never disable TLS certificate verification.

Stage the pinned Senna source from a network-enabled node using `src.upstream`.
Then submit the existing Senna setup job. It verifies staged sources and runs the
package connectivity check before Conda creation or installation; any failed
check stops setup. A successful proxy check can proceed to installation in the
same allocation. No model weights are downloaded.

Return complete setup logs and SLURM accounting. Distinguish PACKAGE_NETWORK_OK
from SENNA_IMPORTS_OK: only the latter, correct package versions and exactly one
visible GPU pass the Senna environment gate. If proxy access fails, preserve its
errors before choosing a supported offline build/transfer route.

## Python bootstrap channel selection

The Senna bootstrap now specifies `conda-forge` and `nodefaults`. This affects
only this environment; no shared or user-wide Conda configuration is modified
and no channel terms are accepted automatically. Python remains 3.10 and the
hashed official Senna pip requirements are unchanged. The network preflight now
checks the selected conda-forge Linux/noarch indexes instead of defaults.

Conda documents `nodefaults` as excluding default channels for that environment:
[Managing environments](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html#creating-an-environment-file-manually).
