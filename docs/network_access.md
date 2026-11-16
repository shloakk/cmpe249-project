# HPC network access

Direct compute-node package access failed in job 116268. The user subsequently
supplied an HTTP proxy route. Job 116269 verified the staged Senna source and
reached all seven package endpoints through that proxy. Installation then stopped
at the defaults-channel terms prompt. No offline transfer is currently required
by this evidence. Job 116270 also reached both conda-forge endpoints, but the
YAML-only channel change did not resolve the terms pre-check.

Add the supplied `http_proxy` and `https_proxy` values only to the ignored `.env`.
The installer and validation scripts load and export that file; Git, pip, Conda and the
Python connectivity probe inherit those settings. Keep the private proxy address
out of tracked examples. Never disable TLS certificate verification.

Stage the pinned Senna source from a network-enabled node using `src.upstream`.
Then run the Senna installer directly in the terminal. It verifies staged sources and runs the
package connectivity check before Conda creation or installation; any failed
check stops setup. A successful proxy check can proceed to installation in the
same terminal run; no GPU allocation is used for installation. No model weights are downloaded.

Return complete setup logs and SLURM accounting. Distinguish PACKAGE_NETWORK_OK
from SENNA_IMPORTS_OK: only the latter, correct package versions and exactly one
visible GPU pass the Senna environment gate. If proxy access fails, preserve its
errors before choosing a supported offline build/transfer route.

## Python bootstrap channel selection

The YAML reference specifies conda-forge/nodefaults, but setup now uses
`conda create --override-channels --channel https://conda.anaconda.org/conda-forge`
with the same Python/pip specifications. This explicit command-level selection
addresses the pre-command terms check seen in job 116270. It affects only the
new environment; no shared or user-wide Conda configuration is modified
and no channel terms are accepted automatically. Python remains 3.10 and the
hashed upstream requirements file is unchanged; installation now selects a
documented inference-only subset after the aidisdk failure in job 116271. The network preflight
checks the selected conda-forge Linux/noarch indexes; these passed in job 116270.

Conda documents `nodefaults` as excluding default channels for that environment:
[Managing environments](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html#creating-an-environment-file-manually).
